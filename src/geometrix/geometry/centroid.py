from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.calculations import calculate_principal_axes, calculate_radii_of_gyration
from geometrix.geometry.models import Vertex, InertiaTensor, TOLERANCE, PrincipalInertia, RadiiOfGyration


class Centroid(BaseModel):
    """
    The result of final property calculations for a cross-section/solid relative to its center of mass.
    """
    plane_area: float = Field(0.0, description="Cross-sectional area (2D).")
    volume: float = Field(0.0, description="Volume of the solid (3D).")
    surface_area: float = Field(0.0, description="Surface area of the solid (3D).")

    center: Vertex = Field(default_factory=Vertex, description="Coordinates of the center of mass (X_c, Y_c, Z_c).")
    inertia: InertiaTensor = Field(default_factory=InertiaTensor, description="Centroidal inertia tensor.")

    @computed_field
    @property
    def primary_measure(self) -> float:
        """Returns the primary non-zero measure (Cross-sectional Area or Volume)."""
        # Use TOLERANCE to check if the area/volume is non-zero
        if self.volume > TOLERANCE.AREA_CALC:
            return self.volume
        return self.plane_area

    class Config:
        frozen = True

    @computed_field
    @property
    def principal_moments(self) -> PrincipalInertia:
        """
        Calculates the **principal moments of inertia** (I1, I2) and the **angle of rotation** (alpha)
        relative to the centroid.
        """
        return calculate_principal_axes(self.inertia)

    @computed_field
    @property
    def radii_of_gyration(self) -> RadiiOfGyration:
        """
        Calculates the **radii of gyration** (rx, ry, r1, r2)
        relative to the centroidal and principal axes.
        """
        # Pass plane_area, as calculate_radii_of_gyration requires the area for 2D radii
        return calculate_radii_of_gyration(self.plane_area, self.inertia, self.principal_moments)
