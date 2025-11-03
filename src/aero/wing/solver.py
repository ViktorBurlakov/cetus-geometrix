import math

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class SolverResults(BaseModel):
    """
    Структура для зберігання всіх результатів розрахунку.
    """
    frequency_rad_s: float = Field(description="Власна частота [рад/с]")
    frequency_hz: float = Field(description="Власна частота [Гц]")
    iteration_count: int = Field(description="Кількість виконаних ітерацій")
    convergence_met: bool = Field(description="Чи досягнута збіжність")
    df_results: pd.DataFrame = Field(description="Таблиця з нормалізованою та реальною формою коливань")


class WingNaturalFrequencySolver:
    """
    Універсальний вирішувач для обчислення власних частот згину та кручення
    методом послідовних наближень (ПР) для секціонованих конструкцій.
    """

    def __init__(self, wing: CalculationData):
        """
        Ініціалізація вирішувача з попередньо зібраними інженерними даними.
        """
        self.data = calculation_data
        self.max_iter = 15
        self.tolerance = 0.005  # 0.5% похибки збіжності

    def perform_iteration(self, mass_data: np.ndarray, stiffness_data: np.ndarray,
                          f_prev: np.ndarray, integration_type: str) -> tuple:
        """
        Виконує одну ітерацію методу послідовних наближень.

        :param mass_data: Масив погонної маси (m_prime або I_m_prime).
        :param stiffness_data: Масив жорсткості (EI_y або GJ).
        :param f_prev: Попередня форма коливань (f_k-1 або phi_k-1).
        :param integration_type: 'bending' (згин, 4 інтеграли) або 'torsion' (кручення, 2 інтеграли).
        :return: (f_norm, p, f_real, G/W_11) - Нормалізована форма, частота, реальна форма, константа нормування.
        """

        N = self.data.N_SECTIONS
        delta_z = self.data.DELTA_Z

        # --- 1. СТОВПЕЦЬ 4 (Початкове навантаження) ---
        # Обчислення m' * f_prev (для згину) або Im' * phi_prev (для кручення)
        col_4 = mass_data * f_prev

        # --- 2. СТОВПЕЦЬ 5/6 (Перший інтеграл - Зворотний) ---
        # F(z) = ∫_L^z (m' * f) dz. Відповідає поперечній силі (згин) або моменту (кручення).
        col_5 = np.zeros_like(f_prev)

        # NOTE: Використовується спрощена формула чисельного інтегрування методу ПР
        # (яка не є стандартним методом трапецій), відповідно до типової методики.
        # col_5[i] = col_5[i+1] + (col_4[i] + col_4[i+1]) * (Delta_z / 2) - спрощений ПР:
        for i in range(N, 0, -1):
            col_5[i - 1] = col_5[i] + (col_4[i] + col_4[i - 1])

            # --- 3. СТОВПЕЦЬ 7 (Інтегрант) ---
        # Обчислення F(z) / Жорсткість
        # Для згину: F(z) / EI_y. Для кручення: F(z) / GJ.
        # NOTE: Використовуємо жорсткість у точці i
        col_7 = col_5 / stiffness_data

        # ====================================================================
        # 4. АЛГОРИТМ ДЛЯ ЗГИНУ (4 інтеграли, консоль: f(0)=0, f'(0)=0, f''(L)=0, f'''(L)=0)
        # ====================================================================
        if integration_type == 'bending':
            # --- СТОВПЕЦЬ 8 (Другий інтеграл - Прямий) ---
            # ∫_0^z (col_7) dz. Відповідає куту повороту (φ) або куту закручування.
            col_8 = np.zeros_like(f_prev)
            for i in range(1, N + 1):
                # Прямий інтеграл: h_i = h_{i-1} + (d_{i-1} + d_i) * (Delta_z / 2) - спрощений ПР
                col_8[i] = col_8[i - 1] + (col_7[i - 1] + col_7[i])

            # --- СТОВПЕЦЬ 9 (Третій інтеграл - Зворотний) ---
            # ∫_L^z (col_8) dz. Вводиться для задоволення граничних умов консолі.
            col_9 = np.zeros_like(f_prev)

            for i in range(N, 0, -1):
                # Зворотний інтеграл: c_i = c_{i+1} + (b_{i+1} + b_i) - спрощений ПР
                col_9[i - 1] = col_9[i] + (col_8[i] + col_8[i - 1])

            # --- СТОВПЕЦЬ 10 (Четвертий інтеграл - Прямий) ---
            # ∫_0^z (col_9) dz. Це фінальна ненормована форма коливань f_k.
            col_10 = np.zeros_like(f_prev)

            for i in range(1, N + 1):
                # Прямий інтеграл: g_i = g_{i-1} + (h_{i-1} + h_i) - спрощений ПР
                col_10[i] = col_10[i - 1] + (col_9[i - 1] + col_9[i])

            # Нормуючий множник (G11 або G_nn)
            G11 = col_10[-1]

            # Розрахунок частоти та форм
            f_real = col_10 * (delta_z ** 4)  # Реальна прогини
            f_norm = col_10 / G11  # Нормована форма

            # p^2 = 1 / (G11 * (Delta_z)^4)
            p_sq = 1.0 / (G11 * (delta_z ** 4))
            p = np.sqrt(p_sq)

            return f_norm, p, f_real, G11

        # ====================================================================
        # 5. АЛГОРИТМ ДЛЯ КРУЧЕННЯ (2 інтеграли, консоль: φ(0)=0, φ'(L)=0)
        # ====================================================================
        elif integration_type == 'torsion':

            # --- СТОВПЕЦЬ 8 (Другий інтеграл - Прямий) ---
            # ∫_0^z (col_7) dz. Це фінальна ненормована форма коливань phi_k.
            col_8 = np.zeros_like(f_prev)
            for i in range(1, N + 1):
                # Прямий інтеграл: h_i = h_{i-1} + (d_{i-1} + d_i) - спрощений ПР
                col_8[i] = col_8[i - 1] + (col_7[i - 1] + col_7[i])

            # Нормуючий множник (W11 або W_nn)
            W11 = col_8[-1]

            # Розрахунок частоти та форм
            phi_real = col_8 * (delta_z ** 2)  # Реальні кути закручування
            phi_norm = col_8 / W11  # Нормована форма

            # p^2 = 1 / (W11 * (Delta_z)^2)
            p_sq = 1.0 / (W11 * (delta_z ** 2))
            p = np.sqrt(p_sq)

            return phi_norm, p, phi_real, W11

        else:
            raise ValueError("Невідомий тип інтегрування. Очікується 'bending' або 'torsion'.")

    def execute(self, initial_data: dict[str, np.ndarray], integration_type: str) -> SolverResults:
        """
        Запускає розрахунок власних частот для заданого типу коливань.

        :param initial_data: Словник з початковим наближенням форми ('f0' або 'phi0') та координат ('z/l').
        :param integration_type: 'bending' або 'torsion'.
        :return: Об'єкт SolverResults з фінальною частотою та формою.
        """

        # Визначення вхідних даних залежно від типу коливань
        f_key = 'f0' if integration_type == 'bending' else 'phi0'

        f_k_1 = initial_data[f_key]

        # Вибір відповідних масивів МІХ та Жорсткостей
        if integration_type == 'bending':
            mass_data = self.data.m_prime_array
            stiffness_data = self.data.EI_y_array
        elif integration_type == 'torsion':
            mass_data = self.data.Im_prime_array
            stiffness_data = self.data.GJ_array
        else:
            raise ValueError("Тип коливань повинен бути 'bending' або 'torsion'.")

        p_prev = 0.0
        k = 1

        print(f"\n[{'=' * 50}]")
        print(f"ПОЧАТОК РОЗРАХУНКУ {integration_type.upper()} КОЛИВАНЬ")
        print(f"[{'=' * 50}]")

        while k <= self.max_iter:
            # Виконуємо ітерацію
            f_k, p_k, f_real, _ = self.perform_iteration(mass_data, stiffness_data,
                                                         f_k_1, integration_type)

            p_k_hz = p_k / (2 * math.pi)

            # Перевірка збіжності
            convergence_met = (k > 1 and abs(p_k - p_prev) / p_k < self.tolerance)

            print(f"Ітерація {k:2}: p_k = {p_k:.4f} рад/с, p'_k = {p_k_hz:.4f} Гц "
                  f"[Збіжність: {abs(p_k - p_prev) / p_k * 100:.2f}%]")

            if convergence_met:
                print(f"\n[Збіжність ({self.tolerance * 100}%) досягнута на ітерації {k}]")
                break

            f_k_1 = f_k
            p_prev = p_k
            k += 1

        else:
            print(f"\n[Збіжність не досягнута за максимальну кількість ітерацій ({self.max_iter})]")

        # Зведення фінальних результатів
        df_results = pd.DataFrame({
            'z/l': initial_data['z/l'],
            f'real_{integration_type}': f_real,
            f'norm_{integration_type}': f_k
        })

        print("\n--- ФІНАЛЬНІ РЕЗУЛЬТАТИ ---")
        print(f"Частота 1-го тону (p'): {p_k_hz:.4f} Гц")
        print(df_results.to_string(index=False))

        return SolverResults(
            frequency_rad_s=p_k,
            frequency_hz=p_k_hz,
            iteration_count=k,
            convergence_met=convergence_met,
            df_results=df_results
        )




def run_demonstration():
    """Демонстраційна функція для показу роботи універсального вирішувача."""

    # 1. СТВОРЕННЯ КОНСТАНТ (для демонстрації)
    L = 1.2
    N_SECTIONS = 10
    DELTA_Z = L / N_SECTIONS

    # Константи МІХ та Жорсткостей для ПР (для однорідного профілю)
    # RHO = 2700, E = 70e9, G = 26e9 (як у заглушках)
    # Приклад для порожнистого профілю B=0.05, H=0.1, b=0.045, h=0.095
    m_prime_const = 3.5  # кг/м
    EI_y_const = 1.2e6  # Н*м^2
    Im_prime_const = 0.004  # кг*м^2
    GJ_const = 0.9e6  # Н*м^2

    N_points = N_SECTIONS + 1

    # 2. ПІДГОТОВКА ДАНИХ (для універсального входу)
    data = CalculationData(
        L=L,
        N_SECTIONS=N_SECTIONS,
        DELTA_Z=DELTA_Z,
        m_prime_array=np.full(N_points, m_prime_const),
        EI_y_array=np.full(N_points, EI_y_const),
        Im_prime_array=np.full(N_points, Im_prime_const),
        GJ_array=np.full(N_points, GJ_const),
        z_coords=np.linspace(0, L, N_points)
    )

    # 3. ПОЧАТКОВІ НАБЛИЖЕННЯ
    initial_data = {
        'z/l': data.z_coords / L,
        # Форма згину (консольна балка)
        'f0': np.array([0, 0.01675, 0.06385, 0.13205, 0.2299, 0.33945, 0.4611, 0.5908, 0.72595, 0.8623, 1.0]),
        # Форма кручення
        'phi0': np.array([0, 0.1564, 0.309, 0.4539, 0.5877, 0.7071, 0.809, 0.891, 0.951, 0.9876, 1.0]),
    }

    # 4. СТВОРЕННЯ ТА ВИКОНАННЯ ВИРІШУВАЧА
    solver = UnifiedNaturalFrequencySolver(calculation_data=data)

    # Розрахунок згину
    bending_results = solver.execute(initial_data, integration_type='bending')

    # Розрахунок кручення
    torsion_results = solver.execute(initial_data, integration_type='torsion')


if __name__ == '__main__':
    run_demonstration()