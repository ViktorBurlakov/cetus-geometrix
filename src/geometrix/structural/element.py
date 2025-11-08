from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.core import GeometryObject
from geometrix.material import Material
from geometrix.geometry.calculation import calculate_principal_axes, calculate_radii_of_gyration
from geometrix.geometry.models import AreaInertia, PrincipalInertia, RadiiOfGyration, Vertex


class StructuralElement(BaseModel):
    """
    Інженерний елемент (Контекст), що поєднує геометричний переріз,
    матеріал і довжину. Обчислює всі фінальні інженерні характеристики:
    масу, модуль зсуву, радіуси інерції та головні моменти.
    """

    # 1. Основні вхідні дані
    geometry: GeometryObject
    material: Material = Field(default_factory=Material)
    length: float = Field(1000.0, gt=0, description="Довжина елемента (наприклад, у мм).")

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    # =================================================================
    # 2. МАСОВІ ХАРАКТЕРИСТИКИ ТА МОДУЛЬ ЗСУВУ
    # =================================================================

    @computed_field
    @property
    def mass(self) -> float:
        """Обчислює масу елемента: Mass = Area * Length * Density."""
        return self.geometry.area * self.length * self.material.density

    @computed_field
    @property
    def shear_modulus(self) -> float:
        """
        Обчислює **модуль зсуву** (G) за законом Гука для ізотропних матеріалів.
        Формула: G = E / (2 * (1 + nu)).
        """
        return self.material.E / (2.0 * (1.0 + self.material.nu))

    @computed_field
    @property
    def centroid_location(self) -> tuple[float, float]:
        """X та Y координати центроїда (ЦМ)."""
        center = self.geometry.centroid.center
        return center.x, center.y

    @computed_field
    @property
    def center_of_mass(self) -> Vertex:
        """
        Координати Центру Мас (COM).
        Для однорідного матеріалу збігається з Центроїдом.
        Повертає об'єкт Vertex (з іменованими полями x та y).
        """
        # Повертаємо об'єкт Vertex, який вже обчислений у структурі Centroid
        return self.geometry.centroid.center

    # =================================================================
    # 3. МОМЕНТИ ІНЕРЦІЇ
    # =================================================================

    @computed_field
    @property
    def I_c(self) -> AreaInertia:
        """
        Повертає **центроїдальний тензор інерції** (Ix_c, Iy_c, Ixy_c)
        у структурованому вигляді AreaInertia.
        """
        return self.geometry.centroid.inertia

    @computed_field
    @property
    def principal_moments(self) -> PrincipalInertia:
        """
        Обчислює **головні моменти інерції** (I1, I2) та **кут повороту** (alpha).
        Передає об'єкт AreaInertia безпосередньо у функцію розрахунку.
        """
        return calculate_principal_axes(self.I_c)

    @computed_field
    @property
    def radii_of_gyration(self) -> RadiiOfGyration:
        """
        Обчислює **радіуси інерції** (rx, ry, r1, r2)
        і повертає їх у структурованому вигляді RadiiOfGyration.
        """
        return calculate_radii_of_gyration(self.geometry.area, self.I_c, self.principal_moments)