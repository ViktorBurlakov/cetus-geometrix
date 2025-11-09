from abc import abstractmethod, ABC

from pydantic import computed_field, Field

from geometrix.geometry.gobject import GeometryObject
from geometrix.geometry.primitives import GeometryObject2D


class Solid(GeometryObject, ABC):
    """Abstract base for all 3D geometric solids."""

    @computed_field
    @property
    def plane_area(self) -> float:
        """The cross-sectional area for a 3D solid is always 0.0 (unless defined otherwise)."""
        return 0.0

    @computed_field
    @property
    def primary_measure(self) -> float:
        """The primary measure is volume for 3D objects."""
        return self.volume

    @computed_field
    @property
    @abstractmethod
    def volume(self) -> float:
        """[REQUIRED] The volume of the solid (V)."""
        pass

    @computed_field
    @property
    @abstractmethod
    def surface_area(self) -> float:
        """[REQUIRED] The surface area."""
        pass


class PrismaticSolid(Solid):
    """
    Represents a solid created by extruding a 2D cross-section.
    Calculates volume based on the section's plane area and length.
    """
    section: GeometryObject2D
    length: float = Field(gt=0)

    @computed_field
    @property
    def volume(self) -> float:
        """Calculates the volume: Section Area * Length."""
        return self.section.plane_area * self.length

    @computed_field
    @property
    def surface_area(self) -> float:
        """
        Calculates the surface area: 2 * Section Area + Perimeter * Length.
        (Requires the GeometryObject2D to have a perimeter property, which should be added).
        """
        # NOTE: Assuming GeometryObject2D has a 'perimeter' property for full functionality.
        # For this example, we return an approximate calculation or 0.0 if perimeter is missing.
        # For a complete implementation, this would be: 2 * self.section.plane_area + self.section.perimeter * self.length
        return 0.0 # Placeholder for surface area implementation

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "PrismaticSolid":
        """Translates the entire solid by translating its 2D cross-section."""
        new_section = self.section.translate(dx, dy, dz)
        return self.__class__(section=new_section, length=self.length)
