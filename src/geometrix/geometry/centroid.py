from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.calculations import calculate_principal_axes, calculate_radii_of_gyration
from geometrix.geometry.models import Vertex, InertiaTensor, TOLERANCE, PrincipalInertia, RadiiOfGyration


class Centroid(BaseModel):
    """
    Результат фінальних обчислень властивостей перерізу/тіла відносно центру мас.
    """
    plane_area: float = Field(0.0, description="Площа перерізу (2D).")
    volume: float = Field(0.0, description="Об'єм тіла (3D).")
    surface_area: float = Field(0.0, description="Площа поверхні тіла (3D).")

    center: Vertex = Field(default_factory=Vertex, description="Координати центру мас (X_c, Y_c, Z_c).")
    inertia: InertiaTensor = Field(default_factory=InertiaTensor, description="Центроїдальний тензор інерції.")

    @computed_field
    @property
    def primary_measure(self) -> float:
        """Повертає основну ненульову міру (Площа перерізу або Об'єм)."""
        # Використовуємо TOLERANCE для перевірки, чи площа/об'єм ненульові
        if self.volume > TOLERANCE.AREA_CALC:
            return self.volume
        return self.plane_area

    class Config:
        frozen = True

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
        # Передаємо plane_area, оскільки calculate_radii_of_gyration потребує площі для 2D-радіусів
        return calculate_radii_of_gyration(self.plane_area, self.inertia, self.principal_moments)
