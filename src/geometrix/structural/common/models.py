from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.models import PrincipalInertia, RadiiOfGyration
from geometrix.geometry.solid import Solid
from geometrix.material.models import Material


class StructuralElement(BaseModel):
    """
    High-level data model for an engineering structural element.

    This class serves as a central DTO (Data Transfer Object) that aggregates
    both the geometric definition (Solid) and the material properties (Material)
    of a physical component. It provides a comprehensive context before
    discretization and numerical analysis.

    Attributes:
        solid (Solid): The 3D geometric model of the element, containing
                       volume, centroid, and inertia properties.
        material (Material): Physical properties of the material (density, E, nu).
    """
    solid: Solid = Field(description="The 3D geometric model of the element.")
    material: Material = Field(description="Physical properties of the material.")

    class Config:
        frozen = True

    @computed_field
    @property
    def mass(self) -> float:
        """
        Calculates the total mass of the element.

        The total mass is derived from the element's volume (from `solid`)
        and its material density (from `material`).

        Returns:
            float: Total mass of the element in kilograms [kg].
        """
        return self.solid.volume * self.material.density

    @computed_field
    @property
    def principal_inertia(self) -> PrincipalInertia:
        """
        Returns the principal mass moments of inertia of the element.

        These properties are typically pre-calculated and encapsulated within
        the geometric model (`solid.principal_moments_of_inertia`).

        Returns:
            PrincipalInertia: An object containing the principal mass moments of inertia.
        """
        return self.solid.principal_moments_of_inertia

    @computed_field
    @property
    def radii_of_gyration(self) -> RadiiOfGyration:
        """
        Returns the principal radii of gyration of the element.

        These properties are typically pre-calculated and encapsulated within
        the geometric model (`solid.principal_radii_of_gyration`).

        Returns:
            RadiiOfGyration: An object containing the principal radii of gyration.
        """
        return self.solid.principal_radii_of_gyration
