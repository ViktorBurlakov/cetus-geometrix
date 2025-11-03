import math
import numpy as np

from engine.geometry.models import (
    GeometrySums,
    AreaInertia,
    StaticMoments,
    Centroid,
    PrincipalInertia,
    RadiiOfGyration  # <-- Нова структура
)

TOLERANCE = 1e-9


def calculate_vertices_sums(vertices: np.ndarray) -> GeometrySums:
    """
    Чисельний розрахунок **сирих геометричних сум (I_0)** перерізу відносно (0,0).

    Використовує **Метод Гаусса-Гріна** для обчислення площі (A),
    статичних моментів (Sx_0, Sy_0) та моментів інерції (Ix_0, Iy_0, Ixy_0)
    замкненого багатокутника за координатами його вершин.

    :param vertices: Масив NumPy (N, 2) координат вершин [x, y].
    :return: Об'єкт GeometrySums (A, Sx_0, Sy_0, Ix_0, Iy_0, Ixy_0).
    """
    if vertices.shape[0] < 3:
        return GeometrySums(
            static_moments=StaticMoments(Sx=0.0, Sy=0.0),
            inertia=AreaInertia(Ix=0.0, Iy=0.0, Ixy=0.0)
        )

    x = vertices[:, 0]
    y = vertices[:, 1]
    x_next = np.roll(x, -1)
    y_next = np.roll(y, -1)

    # Базовий член Гаусса-Гріна: $x_i y_{i+1} - x_{i+1} y_i$
    cross_term = (x * y_next) - (x_next * y)

    # Площа (A)
    A = 0.5 * np.sum(cross_term)

    # Статичні Моменти
    Sy_0 = (1.0 / 6.0) * np.sum((x + x_next) * cross_term)
    Sx_0 = (1.0 / 6.0) * np.sum((y + y_next) * cross_term)

    # Моменти Інерції
    Ix_0 = (1.0 / 12.0) * np.sum((y ** 2 + y * y_next + y_next ** 2) * cross_term)
    Iy_0 = (1.0 / 12.0) * np.sum((x ** 2 + x * x_next + x_next ** 2) * (-cross_term))
    Ixy_0 = (1.0 / 24.0) * np.sum((x * y_next + 2 * x * y + 2 * x_next * y_next + x_next * y) * cross_term)

    return GeometrySums(
        area=A,
        static_moments=StaticMoments(Sx=Sx_0, Sy=Sy_0),
        inertia=AreaInertia(Ix=Ix_0, Iy=Iy_0, Ixy=Ixy_0)
    )


def transfer_properties(
        data: Centroid,
        dx: float,
        dy: float,
        reverted: bool = False
) -> GeometrySums:
    """
    Універсальна функція **перенесення властивостей** за **Теоремою Штейнера**.

    Переносить моменти інерції (I) між паралельними осями.
    Формула: $I_{new} = I_{old} \pm A \cdot d^2$

    :param data: Об'єкт Centroid, що містить початкові моменти інерції та площу (A).
    :param dx: Відстань зсуву по осі X.
    :param dy: Відстань зсуву по осі Y.
    :param reverted:
        - False (Прямий хід): Від ЦМ до довільної осі. **Додавання** ($+$).
        - True (Зворотний хід): Від довільної осі до ЦМ. **Віднімання** ($-$); $I_c$ завжди мінімальний.

    :return: Об'єкт GeometrySums, що містить нові моменти інерції.
    """
    A = data.area
    sign = -1.0 if reverted else 1.0

    Ix_init = data.inertia.Ix
    Iy_init = data.inertia.Iy
    Ixy_init = data.inertia.Ixy

    # Теорема Штейнера
    Ix_new = Ix_init + sign * A * dy ** 2
    Iy_new = Iy_init + sign * A * dx ** 2
    Ixy_new = Ixy_init + sign * A * dx * dy

    # Статичні моменти генеруються лише при ПРЯМОМУ трансфері
    Sx_0 = A * dy if not reverted else 0.0
    Sy_0 = A * dx if not reverted else 0.0

    return GeometrySums(
        area=A,
        static_moments=StaticMoments(Sx=Sx_0, Sy=Sy_0),
        inertia=AreaInertia(Ix=Ix_new, Iy=Iy_new, Ixy=Ixy_new)
    )


def calculate_principal_axes(inertia: AreaInertia) -> PrincipalInertia:
    """
    Обчислює **головні моменти інерції** ($I_1, I_2$) та **кут повороту** ($\alpha$)
    за допомогою **Кола Мора**.

    Кут $\alpha$ (в радіанах) — це кут повороту від осі X до осі $I_1$ (осі максимального моменту).

    :param inertia: Об'єкт AreaInertia, що містить центроїдальні моменти ($I_x^c, I_y^c, I_{xy}^c$).
    :return: Об'єкт PrincipalInertia (I1, I2, alpha).
    """
    Ix_c = inertia.Ix
    Iy_c = inertia.Iy
    Ixy_c = inertia.Ixy

    # Обчислення середнього моменту та радіуса Кола Мора
    I_avg = (Ix_c + Iy_c) / 2.0;
    R = math.sqrt(((Ix_c - Iy_c) / 2.0) ** 2 + Ixy_c ** 2)

    I1 = I_avg + R;  # Максимальний момент
    I2 = I_avg - R  # Мінімальний момент

    if abs(R) < TOLERANCE:
        alpha = 0.0
    else:
        # $\alpha = \frac{1}{2} \arctan \left( \frac{2 I_{xy}}{I_y - I_x} \right)$
        alpha = 0.5 * math.atan2(2.0 * Ixy_c, Iy_c - Ix_c)

    return PrincipalInertia(I1=I1, I2=I2, alpha=alpha)


def calculate_radii_of_gyration(
        A: float,
        inertia: AreaInertia,
        principal_inertia: PrincipalInertia
) -> RadiiOfGyration:
    """
    Обчислює **радіуси інерції** ($r_x, r_y, r_1, r_2$).

    Радіус інерції — це відстань від осі, на якій повинна бути зосереджена
    вся площа (A) перерізу, щоб забезпечити той самий момент інерції (I).
    Формула: $r = \sqrt{I / A}$.

    :param A: Площа перерізу.
    :param inertia: Центроїдальні моменти ($I_x^c, I_y^c$).
    :param principal_inertia: Головні моменти ($I_1, I_2$).
    :return: Об'єкт RadiiOfGyration, що містить (rx, ry, r1, r2).
    """
    if A < TOLERANCE:
        return RadiiOfGyration()

    # Радіуси відносно центроїдальних осей
    rx = math.sqrt(abs(inertia.Ix) / A)
    ry = math.sqrt(abs(inertia.Iy) / A)

    # Радіуси відносно головних осей
    r1 = math.sqrt(abs(principal_inertia.I1) / A)
    r2 = math.sqrt(abs(principal_inertia.I2) / A)

    return RadiiOfGyration(rx=rx, ry=ry, r1=r1, r2=r2)