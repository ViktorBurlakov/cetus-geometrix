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
    Numerical calculation of **raw geometric sums (I_0)** of the cross-section relative to (0,0).

    Uses the **Gauss-Green Method** to calculate area (A),
    static moments (Sx_0, Sy_0) and moments of inertia (Ixx_0, Iyy_0, Ixy_0)
    of a closed polygon based on its vertex coordinates.

    :param vertices: NumPy array (N, 2) of vertex coordinates [x, y].
    :return: GeometrySums object (A, Sx_0, Sy_0, Ixx_0, Iyy_0, Ixy_0).
    """
    if vertices.shape[0] < 3:
        return GeometrySums(
            plane_area=0.0,
            static_moments=StaticMoments(Sx=0.0, Sy=0.0),
            inertia=InertiaTensor(Ixx=0.0, Iyy=0.0, Ixy=0.0)
        )

    # 1. Ensure the polygon is closed
    if not np.array_equal(vertices[0], vertices[-1]):
        vertices = np.vstack([vertices, vertices[0]])

    x = vertices[:, 0]
    y = vertices[:, 1]
    x_next = np.roll(x, -1)
    y_next = np.roll(y, -1)

    # Gauss-Green basic term: $x_i y_{i+1} - x_{i+1} y_i$
    cross_term = (x * y_next) - (x_next * y)

    # 2. Area (A)
    A = 0.5 * np.sum(cross_term)

    # 3. Static Moments
    Sy_0 = (1.0 / 6.0) * np.sum((x + x_next) * cross_term)
    Sx_0 = (1.0 / 6.0) * np.sum((y + y_next) * cross_term)

    # 4. Moments of Inertia
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
    Universal function for **properties transfer** using **Steiner's Theorem**.

    Transfers moments of inertia (I) between parallel axes.
    Formula: $I_{new} = I_{old} \\pm A \\cdot d^2$

    :param area: Cross-sectional area (A).
    :param inertia: InertiaTensor object containing the initial moments of inertia.
    :param dx: Displacement distance along the X-axis.
    :param dy: Displacement distance along the Y-axis.
    :param reverted: True (Inverse transfer: subtraction), False (Direct transfer: addition).

    :return: GeometrySums object containing the new moments of inertia.
    """
    A = area
    sign = -1.0 if reverted else 1.0

    Ix_init = inertia.Ixx
    Iy_init = inertia.Iyy
    Ixy_init = inertia.Ixy

    # Steiner's Theorem
    Ix_new = Ix_init + sign * A * dy ** 2
    Iy_new = Iy_init + sign * A * dx ** 2
    Ixy_new = Ixy_init + sign * A * dx * dy

    # Static moments in direct transfer (from CM to 0,0) are A*dx/dy.
    # In INVERSE transfer (from 0,0 to CM), they must be ZERO.
    # If 'reverted' = False (Direct transfer), dx/dy are the CM coordinates (Cx, Cy).
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
    Calculates the **principal moments of inertia** ($I_1, I_2$) and the **angle of rotation** ($\alpha$)
    using **Mohr's Circle**.

    :param inertia: InertiaTensor object containing the centroidal moments ($I_{xx}^c, I_{yy}^c, I_{xy}^c$).
    :return: PrincipalInertia object (I1, I2, alpha).
    """
    Ix_c = inertia.Ixx
    Iy_c = inertia.Iyy
    Ixy_c = inertia.Ixy

    # Calculation of average moment and Mohr's Circle radius
    I_avg = (Ix_c + Iy_c) / 2.0
    R_sqr = ((Ix_c - Iy_c) / 2.0) ** 2 + Ixy_c ** 2

    R = math.sqrt(R_sqr)

    I1 = I_avg + R  # Maximum moment
    I2 = I_avg - R  # Minimum moment

    # Use AREA_CALC for zero tolerance check
    if abs(R) < TOLERANCE.AREA_CALC:
        alpha = 0.0
    else:
        # $\alpha = \frac{1}{2} \arctan \left( \frac{2 I_{xy}}{I_y - I_x} \right)$
        # Use atan2 to avoid problems with vertical lines
        alpha = 0.5 * math.atan2(2.0 * Ixy_c, Iy_c - Ix_c)

    return PrincipalInertia(I1=I1, I2=I2, alpha=alpha)


def calculate_radii_of_gyration(
        A: float,
        inertia: InertiaTensor,
        principal_inertia: PrincipalInertia
) -> RadiiOfGyration:
    """
    Calculates the **radii of gyration** ($r_x, r_y, r_1, r_2$).

    Formula: $r = \\sqrt{I / A}$.

    :param A: Cross-sectional area.
    :param inertia: Centroidal moments ($I_{xx}^c, I_{yy}^c$).
    :param principal_inertia: Principal moments ($I_1, I_2$).
    :return: RadiiOfGyration object containing (rx, ry, r1, r2).
    """
    # Use AREA_CALC for zero area check
    if abs(A) < TOLERANCE.AREA_CALC or A < 0:
        return RadiiOfGyration()

    # Radii relative to centroidal axes
    rx = math.sqrt(abs(inertia.Ixx) / A)
    ry = math.sqrt(abs(inertia.Iyy) / A)

    # Radii relative to principal axes
    r1 = math.sqrt(abs(principal_inertia.I1) / A)
    r2 = math.sqrt(abs(principal_inertia.I2) / A)

    return RadiiOfGyration(rx=rx, ry=ry, r1=r1, r2=r2)
