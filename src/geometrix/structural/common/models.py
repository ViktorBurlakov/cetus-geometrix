from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.models import PrincipalInertia, RadiiOfGyration
from geometrix.geometry.solid import Solid
from geometrix.material.models import Material


class StructuralElement(BaseModel):
    """
    🏗️ Інженерний елемент (Контекст), що поєднує геометричний об'єм (solid)
    та матеріал. Агрегує всі жорсткісні характеристики через `StiffnessProperties`.
    """
    solid: Solid = Field(description="Об'ємна геометрична модель елемента, що містить обчислений Centroid.")
    material: Material = Field(default_factory=Material, description="Фізичні властивості матеріалу.")

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    @computed_field
    @property
    def mass(self) -> float:
        """Обчислює масу елемента: Mass = Volume * Density [кг]."""
        return self.solid.volume * self.material.density

    @computed_field
    @property
    def principal_inertia(self) -> PrincipalInertia:
        """
        Повертає головні моменти інерції та кут повороту, вже обчислені
        та інкапсульовані в `solid.centroid`.
        """
        return self.solid.centroid.principal_moments

    @computed_field
    @property
    def radii_of_gyration(self) -> RadiiOfGyration:
        """
        Повертає радіуси інерції, вже обчислені та інкапсульовані
        в `solid.centroid`.
        """
        return self.solid.centroid.radii_of_gyration
