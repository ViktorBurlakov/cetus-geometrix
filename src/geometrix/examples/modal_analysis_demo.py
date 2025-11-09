
import numpy as np

from geometrix.structural.common.properties import LinearStructureSectionProperties
from geometrix.structural.modal.tasks import ModalAnalysisTask
from geometrix.structural.modal.solvers.pr_solver import ProgressiveIterationSolver
from geometrix.structural.modal.results import ModalAnalysisResults


def run_modal_analysis_demo():
    """Демонстраційна функція для показу роботи універсального вирішувача."""

    # 1. ПІДГОТОВКА МОДЕЛЬНИХ ДАНИХ (LinearStructureSectionProperties)
    L = 1.2
    N_SECTIONS = 10

    N_points = N_SECTIONS + 1
    delta_z = L / N_SECTIONS
    z_coords_array = np.linspace(0, L, N_points)

    m_prime_const = 3.5  # кг/м
    EI_y_const = 1.2e6  # Н*м^2
    Im_prime_const = 0.004  # кг*м^2
    GJ_const = 0.9e6  # Н*м^2

    section_data = LinearStructureSectionProperties(
        section_count=N_SECTIONS,
        delta_x=delta_z,
        z_coords=z_coords_array,
        m_prime_array=np.full(N_points, m_prime_const),
        EI_y_array=np.full(N_points, EI_y_const),
        Im_prime_array=np.full(N_points, Im_prime_const),
        GJ_array=np.full(N_points, GJ_const)
    )

    # 2. ПІДГОТОВКА КОНТЕКСТУ ЗАДАЧІ (ModalAnalysisTask)
    initial_bending_f0 = np.array([0, 0.01675, 0.06385, 0.13205, 0.2299, 0.33945, 0.4611, 0.5908, 0.72595, 0.8623, 1.0])
    initial_torsion_phi0 = np.array([0, 0.1564, 0.309, 0.4539, 0.5877, 0.7071, 0.809, 0.891, 0.951, 0.9876, 1.0])

    modal_task = ModalAnalysisTask(
        model_data=section_data,
        initial_bending_f0=initial_bending_f0,
        initial_torsion_phi0=initial_torsion_phi0,
        max_iter=20,
        tolerance=0.001
    )

    print("\n" + "=" * 70)
    print(" === Запуск модального аналізу через Task Context (вкладена структура) ===")
    print("=" * 70 + "\n")

    # 3. ВИБІР ТА ЗАПУСК СОЛВЕРА
    solver = ProgressiveIterationSolver(task_context=modal_task)
    results: ModalAnalysisResults = solver.execute()

    print("\n" + "=" * 70)
    print(" === Демонстрація завершена ===")
    print("=" * 70 + "\n")

    # Виведення агрегованих результатів
    print("\n✅ ФІНАЛЬНІ РЕЗУЛЬТАТИ МОДАЛЬНОГО АНАЛІЗУ:")

    print(f"   Звіт про збіжність (на основі розрахунку згину):")
    print(f"     Кількість ітерацій: {results.report.iteration_count}")
    print(f"     Збіжність досягнута: {results.report.convergence_met}")
    print(f"     Час обчислення: {results.report.computation_time_s:.4f} с")

    if results.frequencies:
        print("\n   Частоти:")
        print(
            f"     1-й тон (Згин): Частота [Гц]: {results.frequencies[0].frequency_hz:.4f}, Частота [рад/с]: {results.frequencies[0].frequency_rad_s:.4f}")
        print(
            f"     2-й тон (Кручення): Частота [Гц]: {results.frequencies[1].frequency_hz:.4f}, Частота [рад/с]: {results.frequencies[1].frequency_rad_s:.4f}")

    if results.mode_shapes:
        print("\n   Форми коливань (1-й тон, Згин):")
        print(results.mode_shapes[0].df_mode_shape.to_string(index=False))
        print("\n   Форми коливань (2-й тон, Кручення):")
        print(results.mode_shapes[1].df_mode_shape.to_string(index=False))


if __name__ == '__main__':
    run_modal_analysis_demo()
