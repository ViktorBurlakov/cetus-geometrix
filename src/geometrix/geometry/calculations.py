import math
import numpy as np
from geometrix.geometry.models import (
    GeometrySums,
    InertiaTensor,
    StaticMoments,
    PrincipalInertia,
    RadiiOfGyration, TOLERANCE,
)


def calculate_vertices_sums(vertices: np.ndarray) -> GeometrySums:
    """
    Чисельний розрахунок **сирих геометричних сум (I_0)** перерізу відносно (0,0).

    Використовує **Метод Гаусса-Гріна** для обчислення площі (A),
    статичних моментів (Sx_0, Sy_0) та моментів інерції (Ixx_0, Iyy_0, Ixy_0)
    замкненого багатокутника за координатами його вершин.

    :param vertices: Масив NumPy (N, 2) координат вершин [x, y].
    :return: Об'єкт GeometrySums (A, Sx_0, Sy_0, Ixx_0, Iyy_0, Ixy_0).
    """
    if vertices.shape[0] < 3:
        return GeometrySums(
            plane_area=0.0,
            static_moments=StaticMoments(Sx=0.0, Sy=0.0),
            inertia=InertiaTensor(Ixx=0.0, Iyy=0.0, Ixy=0.0)
        )

    # 1. Забезпечення замкненості багатокутника
    if not np.array_equal(vertices[0], vertices[-1]):
        vertices = np.vstack([vertices, vertices[0]])

    x = vertices[:, 0]
    y = vertices[:, 1]
    x_next = np.roll(x, -1)
    y_next = np.roll(y, -1)

    # Базовий член Гаусса-Гріна: $x_i y_{i+1} - x_{i+1} y_i$
    cross_term = (x * y_next) - (x_next * y)

    # 2. Площа (A)
    A = 0.5 * np.sum(cross_term)

    # 3. Статичні Моменти
    Sy_0 = (1.0 / 6.0) * np.sum((x + x_next) * cross_term)
    Sx_0 = (1.0 / 6.0) * np.sum((y + y_next) * cross_term)

    # 4. Моменти Інерції
    Ix_0 = (1.0 / 12.0) * np.sum((y ** 2 + y * y_next + y_next ** 2) * cross_term)
    Iy_0 = (1.0 / 12.0) * np.sum((x ** 2 + x * x_next + x_next ** 2) * cross_term)
    # Ixy_0 = (1.0 / 24.0) * np.sum((x * y_next + x_next * y + x * y + x_next * y_next) * cross_term)
    Ixy_0 = (1.0 / 24.0) * np.sum(
        (x * y_next + 2 * x * y + 2 * x_next * y_next + x_next * y) * cross_term
    )

    return GeometrySums(
        plane_area=A,
        static_moments=StaticMoments(Sx=Sx_0, Sy=Sy_0),
        inertia=InertiaTensor(Ixx=Ix_0, Iyy=Iy_0, Ixy=Ixy_0)
    )


def transfer_properties(
        area: float,
        inertia: InertiaTensor,
        dx: float,
        dy: float,
        reverted: bool = False
) -> GeometrySums:
    """
    Універсальна функція **перенесення властивостей** за **Теоремою Штейнера**.

    Переносить моменти інерції (I) між паралельними осями.
    Формула: $I_{new} = I_{old} \pm A \cdot d^2$

    :param area: Площа перерізу (A).
    :param inertia: Об'єкт InertiaTensor, що містить початкові моменти інерції.
    :param dx: Відстань зсуву по осі X.
    :param dy: Відстань зсуву по осі Y.
    :param reverted: True (Зворотний хід: віднімання), False (Прямий хід: додавання).

    :return: Об'єкт GeometrySums, що містить нові моменти інерції.
    """
    A = area
    sign = -1.0 if reverted else 1.0

    Ix_init = inertia.Ixx
    Iy_init = inertia.Iyy
    Ixy_init = inertia.Ixy

    # Теорема Штейнера
    Ix_new = Ix_init + sign * A * dy ** 2
    Iy_new = Iy_init + sign * A * dx ** 2
    Ixy_new = Ixy_init + sign * A * dx * dy

    # Статичні моменти при прямому трансфері (від ЦМ до 0,0) - це A*dx/dy.
    # При ЗВОРОТНОМУ трансфері (від 0,0 до ЦМ) вони мають бути НУЛЬОВИМИ.
    # Якщо 'reverted' = False (Прямий трансфер), dx/dy - це координати ЦМ (Cx, Cy).
    # Sx_0 = A * Cy, Sy_0 = A * Cx
    Sx_new = A * dy if not reverted else 0.0
    Sy_new = A * dx if not reverted else 0.0

    return GeometrySums(
        plane_area=A,
        static_moments=StaticMoments(Sx=Sx_new, Sy=Sy_new),
        inertia=InertiaTensor(Ixx=Ix_new, Iyy=Iy_new, Ixy=Ixy_new)
    )


def calculate_principal_axes(inertia: InertiaTensor) -> PrincipalInertia:
    """
    Обчислює **головні моменти інерції** ($I_1, I_2$) та **кут повороту** ($\alpha$)
    за допомогою **Кола Мора**.

    :param inertia: Об'єкт InertiaTensor, що містить центроїдальні моменти ($I_{xx}^c, I_{yy}^c, I_{xy}^c$).
    :return: Об'єкт PrincipalInertia (I1, I2, alpha).
    """
    Ix_c = inertia.Ixx
    Iy_c = inertia.Iyy
    Ixy_c = inertia.Ixy

    # Обчислення середнього моменту та радіуса Кола Мора
    I_avg = (Ix_c + Iy_c) / 2.0
    R_sqr = ((Ix_c - Iy_c) / 2.0) ** 2 + Ixy_c ** 2

    R = math.sqrt(R_sqr)

    I1 = I_avg + R  # Максимальний момент
    I2 = I_avg - R  # Мінімальний момент

    # Використовуємо AREA_CALC для перевірки нульової толерантності
    if abs(R) < TOLERANCE.AREA_CALC:
        alpha = 0.0
    else:
        # $\alpha = \frac{1}{2} \arctan \left( \frac{2 I_{xy}}{I_y - I_x} \right)$
        # Використання atan2 для уникнення проблем з вертикальними лініями
        alpha = 0.5 * math.atan2(2.0 * Ixy_c, Iy_c - Ix_c)

    return PrincipalInertia(I1=I1, I2=I2, alpha=alpha)


def calculate_radii_of_gyration(
        A: float,
        inertia: InertiaTensor,
        principal_inertia: PrincipalInertia
) -> RadiiOfGyration:
    """
    Обчислює **радіуси інерції** ($r_x, r_y, r_1, r_2$).

    Формула: $r = \sqrt{I / A}$.

    :param A: Площа перерізу.
    :param inertia: Центроїдальні моменти ($I_{xx}^c, I_{yy}^c$).
    :param principal_inertia: Головні моменти ($I_1, I_2$).
    :return: Об'єкт RadiiOfGyration, що містить (rx, ry, r1, r2).
    """
    # Використовуємо AREA_CALC для перевірки нульової площі
    if abs(A) < TOLERANCE.AREA_CALC or A < 0:
        return RadiiOfGyration()

    # Радіуси відносно центроїдальних осей
    rx = math.sqrt(abs(inertia.Ixx) / A)
    ry = math.sqrt(abs(inertia.Iyy) / A)

    # Радіуси відносно головних осей
    r1 = math.sqrt(abs(principal_inertia.I1) / A)
    r2 = math.sqrt(abs(principal_inertia.I2) / A)

    return RadiiOfGyration(rx=rx, ry=ry, r1=r1, r2=r2)
