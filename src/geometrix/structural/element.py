from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.core import GeometryObject
from geometrix.material import Material


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

    @computed_field
    @property
    def mass(self) -> float:
        """Обчислює масу елемента: Mass = Area * Length * Density."""
        return self.geometry.area * self.length * self.material.density
