from abc import abstractmethod, ABC

from pydantic import computed_field, Field

from geometrix.geometry.flat import GeometryObject2D
from geometrix.geometry.gobject import GeometryObject


class Solid(GeometryObject, ABC):
    """Абстрактна база для всіх 3D геометричних тіл."""

    @computed_field
    @property
    def plane_area(self) -> float:
        """Площа перерізу для 3D тіла завжди 0.0 (якщо не визначено інше)."""
        return 0.0

    @computed_field
    @property
    def primary_measure(self) -> float:
        """Основна міра — це об'єм для 3D."""
        return self.volume

    @computed_field
    @property
    @abstractmethod
    def volume(self) -> float:
        """[ОБОВ'ЯЗКОВО] Об'єм тіла (V)."""
        pass  # Видалено дублювання

    @computed_field
    @property
    @abstractmethod
    def surface_area(self) -> float:
        """[ОБОВ'ЯЗКОВО] Площа поверхні."""
        pass


class PrismaticSolid(Solid):
    section: GeometryObject2D
    length: float = Field(gt=0)

    @computed_field
    @property
    def volume(self) -> float:
        return self.section.plane_area * self.length

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "PrismaticSolid":
        pass