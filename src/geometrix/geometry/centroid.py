from typing import NamedTuple

from pydantic import computed_field

from geometrix.geometry.calculations import calculate_principal_axes, calculate_radii_of_gyration
from geometrix.geometry.models import Vertex, AreaInertia, PrincipalInertia, RadiiOfGyration


class Centroid(NamedTuple):
    """Структура для зберігання властивостей фігури відносно її Центроїда (ЦП)."""
    area: float
    center: Vertex
    inertia: AreaInertia

    @computed_field
    @property
    def principal_moments(self) -> PrincipalInertia:
        """
        Обчислює **головні моменти інерції** (I1, I2) та **кут повороту** (alpha)
        відносно центроїда.
        """
        return calculate_principal_axes(self.inertia)

    @computed_field
    @property
    def radii_of_gyration(self) -> RadiiOfGyration:
        """
        Обчислює **радіуси інерції** (rx, ry, r1, r2)
        відносно центроїдальних та головних осей.
        """
        return calculate_radii_of_gyration(self.area, self.inertia, self.principal_moments)

