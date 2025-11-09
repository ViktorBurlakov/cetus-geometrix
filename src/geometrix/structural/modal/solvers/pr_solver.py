# geometrix/structural/modal/solvers/pr_solver.py

"""
Модуль `pr_solver.py` містить реалізацію конкретного вирішувача
для модального аналізу (розрахунку власних частот та форм коливань)
структурних елементів.

Цей вирішувач використовує метод послідовних наближень (або ітерації Прандтля-Рітца,
звідси "PR" у назві) для знаходження першого власного тону для згинальних та крутильних
коливань одновимірної стрижневої системи.

Основні компоненти модуля:
- Клас `ProgressiveIterationSolver`: Реалізує логіку ітераційного розрахунку,
  успадковуючи від `AbstractIterativeSolver` для забезпечення уніфікованого інтерфейсу.

Залежності:
- `numpy`: Для числових обчислень та роботи з масивами.
- `pandas`: Для структурованого зберігання та обробки даних форм коливань.
- `math`, `time`: Для математичних функцій та вимірювання часу виконання.
- `geometrix.structural.modal.tasks.ModalAnalysisTask`: Контекст задачі модального аналізу,
  що містить вхідні дані (геометрію, масу, жорсткість, початкові наближення).
- `geometrix.structural.modal.results.*`: DTO для зберігання специфічних результатів
  модального аналізу (власні частоти, форми коливань).
- `geometrix.structural.common.results.ConvergenceReport`: Загальний DTO для звіту
  про збіжність ітераційного процесу.
- `geometrix.structural.common.solvers.abstract_solver.AbstractIterativeSolver`:
  Абстрактний базовий клас для всіх ітераційних солверів, який визначає спільний інтерфейс.
"""

import numpy as np
import pandas as pd
import math
import time

from geometrix.structural.modal.tasks import ModalAnalysisTask
from geometrix.structural.modal.results import ModalFrequencyResult, ModeShapeData, ModalAnalysisResults
from geometrix.structural.common.results import ConvergenceReport
from geometrix.structural.common.solvers.abstract_solver import AbstractIterativeSolver


class ProgressiveIterationSolver(AbstractIterativeSolver[ModalAnalysisTask, ModalAnalysisResults]):
    """
    Конкретний вирішувач для модального аналізу, що реалізує метод
    послідовних наближень (Progressive Iteration) для визначення
    перших власних частот та форм коливань для згинальних та крутильних
    режимів.

    Успадковує від `AbstractIterativeSolver`, реалізуючи його абстрактні методи
    та спеціалізуючи їх під `ModalAnalysisTask` (вхідні дані) та
    `ModalAnalysisResults` (вихідні результати).
    """

    def __init__(self,
                 task_context: ModalAnalysisTask):
        """
        Ініціалізує вирішувач з контекстом задачі модального аналізу.

        Аргументи:
            task_context (ModalAnalysisTask): Об'єкт, що містить всі вхідні дані
                                              для розрахунку (властивості моделі,
                                              параметри солвера, початкові наближення).
        """
        # Виклик конструктора базового класу AbstractIterativeSolver.
        # Він витягує спільні параметри, такі як model_data, max_iter, tolerance
        # і ініціалізує N_SECTIONS та DELTA_Z.
        super().__init__(task_context)

    def _integrate_bending(self, mass_data: np.ndarray, stiffness_data: np.ndarray, f_prev: np.ndarray) -> tuple:
        """
        Виконує інтегрування для розрахунку згинальних коливань.
        Цей метод імітує чотирикратне інтегрування рівняння коливань балки
        для отримання нової форми коливань та власної частоти.

        Аргументи:
            mass_data (np.ndarray): Масив розподілених мас (погонна маса).
            stiffness_data (np.ndarray): Масив згинальних жорсткостей (EI_y).
            f_prev (np.ndarray): Попередня форма коливань (початкове наближення або результат попередньої ітерації).

        Повертає:
            tuple: Кортеж, що містить:
                - f_norm (np.ndarray): Нормалізована форма коливань.
                - p (float): Власна частота в рад/с.
                - f_real (np.ndarray): Реальна амплітуда коливань.
                - G11 (float): Інтегральна константа, що використовується для обчислення p.
        """
        N = self.N_SECTIONS
        delta_z = self.DELTA_Z

        # col_4: f_prev * mass_data (маса * амплітуда)
        col_4 = mass_data * f_prev
        # col_5: Перше інтегрування (від кінця до початку)
        col_5 = np.zeros_like(f_prev)
        for i in range(N, 0, -1):
            col_5[i - 1] = col_5[i] + (col_4[i] + col_4[i - 1])  # Приблизне інтегрування методом трапецій

        # col_7: col_5 / stiffness_data (поділ на жорсткість)
        col_7 = col_5 / stiffness_data

        # col_8: Друге інтегрування (від початку до кінця)
        col_8 = np.zeros_like(f_prev)
        for i in range(1, N + 1):
            col_8[i] = col_8[i - 1] + (col_7[i - 1] + col_7[i])

        # col_9: Третє інтегрування (від кінця до початку)
        col_9 = np.zeros_like(f_prev)
        for i in range(N, 0, -1):
            col_9[i - 1] = col_9[i] + (col_8[i] + col_8[i - 1])

        # col_10: Четверте інтегрування (від початку до кінця)
        col_10 = np.zeros_like(f_prev)
        for i in range(1, N + 1):
            col_10[i] = col_10[i - 1] + (col_9[i - 1] + col_9[i])

        G11 = col_10[-1]  # Значення на вільному кінці після 4-х інтегрувань
        f_real = col_10 * (delta_z ** 4) # Реальні амплітуди
        f_norm = col_10 / G11 if G11 != 0 else np.zeros_like(col_10) # Нормалізовані амплітуди

        # Обчислення власної частоти з використанням G11
        p_sq = 1.0 / (G11 * (delta_z ** 4)) if G11 != 0 else 0.0
        p = np.sqrt(p_sq)

        return f_norm, p, f_real, G11

    def _integrate_torsion(self, mass_data: np.ndarray, stiffness_data: np.ndarray, f_prev: np.ndarray) -> tuple:
        """
        Виконує інтегрування для розрахунку крутильних коливань.
        Цей метод імітує двократне інтегрування рівняння крутильних коливань
        для отримання нової форми коливань та власної частоти.

        Аргументи:
            mass_data (np.ndarray): Масив розподілених моментів інерції маси (погонний момент інерції).
            stiffness_data (np.ndarray): Масив крутильних жорсткостей (GJ).
            f_prev (np.ndarray): Попередня форма коливань (початкове наближення або результат попередньої ітерації).

        Повертає:
            tuple: Кортеж, що містить:
                - phi_norm (np.ndarray): Нормалізована форма коливань.
                - p (float): Власна частота в рад/с.
                - phi_real (np.ndarray): Реальна амплітуда коливань.
                - W11 (float): Інтегральна константа, що використовується для обчислення p.
        """
        N = self.N_SECTIONS
        delta_z = self.DELTA_Z

        # col_4: f_prev * mass_data (момент інерції * кут повороту)
        col_4 = mass_data * f_prev
        # col_5: Перше інтегрування (від кінця до початку)
        col_5 = np.zeros_like(f_prev)
        for i in range(N, 0, -1):
            col_5[i - 1] = col_5[i] + (col_4[i] + col_4[i - 1])

        # col_7: col_5 / stiffness_data (поділ на крутильну жорсткість)
        col_7 = col_5 / stiffness_data

        # col_8: Друге інтегрування (від початку до кінця)
        col_8 = np.zeros_like(f_prev)
        for i in range(1, N + 1):
            col_8[i] = col_8[i - 1] + (col_7[i - 1] + col_7[i])

        W11 = col_8[-1]  # Значення на вільному кінці після 2-х інтегрувань
        phi_real = col_8 * (delta_z ** 2) # Реальні амплітуди
        phi_norm = col_8 / W11 if W11 != 0 else np.zeros_like(col_8) # Нормалізовані амплітуди

        # Обчислення власної частоти з використанням W11
        p_sq = 1.0 / (W11 * (delta_z ** 2)) if W11 != 0 else 0.0
        p = np.sqrt(p_sq)

        return phi_norm, p, phi_real, W11

    def perform_iteration(self, mass_data: np.ndarray, stiffness_data: np.ndarray,
                          f_prev: np.ndarray, integration_type: str) -> tuple[np.ndarray, float, np.ndarray, float]:
        """
        Виконує одну ітерацію методу послідовних наближень для заданого типу коливань.

        Цей метод є реалізацією абстрактного методу з `AbstractIterativeSolver`.

        Аргументи:
            mass_data (np.ndarray): Масив розподілених мас (для згину) або моментів інерції (для кручення).
            stiffness_data (np.ndarray): Масив жорсткостей (згинальних або крутильних).
            f_prev (np.ndarray): Попереднє наближення форми коливань.
            integration_type (str): Тип інтегрування ('bending' для згинальних, 'torsion' для крутильних).

        Повертає:
            tuple: Результати інтегрування: нормалізована форма, власна частота (рад/с),
                   реальна амплітуда форми, інтегральна константа (G11 або W11).
        """
        if integration_type == 'bending':
            return self._integrate_bending(mass_data, stiffness_data, f_prev)
        elif integration_type == 'torsion':
            return self._integrate_torsion(mass_data, stiffness_data, f_prev)
        else:
            raise ValueError("Невідомий тип інтегрування. Очікується 'bending' або 'torsion'.")

    def _run_single_mode(self, initial_f0: np.ndarray, integration_type: str) -> ModalAnalysisResults:
        """
        Запускає ітераційний процес для обчислення ОДНОГО власного тону
        (першого) для заданого типу коливань (згин або кручення).

        Аргументи:
            initial_f0 (np.ndarray): Початкове наближення форми коливань.
            integration_type (str): Тип інтегрування ('bending' або 'torsion').

        Повертає:
            ModalAnalysisResults: Об'єкт, що містить результати розрахунку
                                  для одного власного тону (частоту, форму, звіт про збіжність).
        """
        f_k_1 = initial_f0 # Початкове наближення для першої ітерації

        # Вибір масових та жорсткісних даних залежно від типу коливань
        if integration_type == 'bending':
            mass_data = self.section_data.m_prime_array
            stiffness_data = self.section_data.EI_y_array
        elif integration_type == 'torsion':
            mass_data = self.section_data.Im_prime_array
            stiffness_data = self.section_data.GJ_array
        else:
            raise ValueError("Тип коливань повинен бути 'bending' або 'torsion'.")

        p_prev = 0.0 # Попередня власна частота для перевірки збіжності
        k = 1 # Лічильник ітерацій
        convergence_met = False # Прапорець збіжності
        p_k = 0.0 # Поточна власна частота
        f_k = np.zeros_like(initial_f0) # Поточна форма коливань (нормалізована)
        f_real_final = np.zeros_like(initial_f0) # Фінальна реальна форма коливань

        start_time = time.time() # Початок відліку часу

        print(f"\n[{'=' * 50}]")
        print(f"ПОЧАТОК РОЗРАХУНКУ {integration_type.upper()} КОЛИВАНЬ")
        print(f"[{'=' * 50}]")

        # Головний цикл ітерацій
        while k <= self.max_iter:
            # Виконання однієї ітерації
            f_k, p_k, f_real, _ = self.perform_iteration(mass_data, stiffness_data, f_k_1, integration_type)
            p_k_hz = p_k / (2 * math.pi) # Перетворення частоти в Герци

            # Перевірка збіжності (починаючи з другої ітерації)
            if k > 1 and p_prev != 0:
                relative_error = abs(p_k - p_prev) / p_k
                convergence_met = (relative_error < self.tolerance)
                print(f"Ітерація {k:2}: p_k = {p_k:.4f} рад/с, p'_k = {p_k_hz:.4f} Гц "
                      f"[Збіжність: {relative_error * 100:.2f}%]")
            else:
                 print(f"Ітерація {k:2}: p_k = {p_k:.4f} рад/с, p'_k = {p_k_hz:.4f} Гц")

            # Якщо збіжність досягнута, виходимо з циклу
            if convergence_met:
                print(f"\n[Збіжність ({self.tolerance * 100}%) досягнута на ітерації {k}]")
                break

            f_k_1 = f_k # Оновлюємо початкове наближення для наступної ітерації
            p_prev = p_k # Оновлюємо попередню частоту
            f_real_final = f_real # Зберігаємо останню реальну форму
            k += 1
        else:
            # Якщо цикл завершився без досягнення збіжності (досягнуто max_iter)
            print(f"\n[Збіжність не досягнута за максимальну кількість ітерацій ({self.max_iter})]")

        end_time = time.time() # Кінець відліку часу
        computation_time = end_time - start_time # Загальний час обчислення

        # Формування об'єкта звіту про збіжність
        report = ConvergenceReport(
            iteration_count=k - 1 if convergence_met else k, # Кількість виконаних ітерацій
            convergence_met=convergence_met,
            error_message="Convergence not met" if not convergence_met else "",
            computation_time_s=computation_time
        )

        # Формування об'єкта результату власної частоти
        frequency_result = ModalFrequencyResult(
            mode_number=1, # Завжди 1-й тон для цього солвера
            frequency_rad_s=p_k,
            frequency_hz=p_k / (2 * math.pi)
        )

        # Формування DataFrame для форми коливань
        df_mode_shape = pd.DataFrame({
            'z_coord': self.section_data.z_coords,
            'real_amplitude': f_real_final,
            'norm_amplitude': f_k
        })
        # Формування об'єкта даних форми коливань
        mode_shape_result = ModeShapeData(
            mode_number=1,
            df_mode_shape=df_mode_shape
        )

        # Повернення агрегованих результатів модального аналізу для одного тону
        return ModalAnalysisResults(
            report=report,
            frequencies=[frequency_result],
            mode_shapes=[mode_shape_result]
        )

    def execute(self) -> ModalAnalysisResults:
        """
        Запускає повний розрахунок власних частот для згинальних та крутильних
        коливань, використовуючи метод послідовних наближень.

        Цей метод є реалізацією абстрактного методу з `AbstractIterativeSolver`.

        Він виконує окремі розрахунки для згинання та кручення,
        а потім агрегує їх у єдиний об'єкт `ModalAnalysisResults`.

        Повертає:
            ModalAnalysisResults: Агрегований об'єкт, що містить звіти,
                                  власні частоти та форми коливань для
                                  згинання та кручення.
        """
        # Запуск розрахунку для згинальних коливань
        bending_mode_results = self._run_single_mode(
            initial_f0=self.task_context.initial_bending_f0,
            integration_type='bending'
        )

        # Запуск розрахунку для крутильних коливань
        torsion_mode_results = self._run_single_mode(
            initial_f0=self.task_context.initial_torsion_phi0,
            integration_type='torsion'
        )

        # Звіт про збіжність беремо з розрахунку згинальних коливань,
        # оскільки для першого тону він є репрезентативним.
        aggregated_report = bending_mode_results.report

        # Агрегування результатів обох типів коливань
        return ModalAnalysisResults(
            report=aggregated_report,
            frequencies=[bending_mode_results.frequencies[0], torsion_mode_results.frequencies[0]],
            mode_shapes=[bending_mode_results.mode_shapes[0], torsion_mode_results.mode_shapes[0]]
        )
