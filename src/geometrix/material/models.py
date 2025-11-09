from pydantic import BaseModel, Field, computed_field

class Material(BaseModel):
    """
    Data model for an engineering material, encapsulating fundamental physical constants.

    This class serves as a foundational DTO for structural analysis, as the stiffness
    and inertial properties of elements directly depend on the material's characteristics.

    Attributes:
        name (str): Name of the material (e.g., "Steel S235").
        density (float): Mass per unit volume [kg/m^3]. Must be greater than 0.
        E (float): Young's Modulus (Modulus of Elasticity) [Pa]. Must be greater than 0.
        nu (float): Poisson's Ratio (dimensionless). Must be between 0 and 0.5 (exclusive for 0.5).
    """
    name: str = Field(description="Name of the material (e.g., 'Steel S235').")
    density: float = Field(gt=0, description="Density (mass per unit volume) [kg/m^3].")
    E: float = Field(gt=0, description="Young's Modulus (Modulus of Elasticity) [Pa].")
    nu: float = Field(ge=0, lt=0.5, description="Poisson's Ratio (dimensionless, 0 <= nu < 0.5).")

    class Config:
        frozen = True

    @computed_field
    @property
    def shear_modulus(self) -> float:
        """
        Calculates the shear modulus (G) using the formula G = E / (2 * (1 + nu)).

        This property is derived from Young's Modulus (E) and Poisson's Ratio (nu),
        assuming an isotropic material. It is crucial for calculating shear and torsional stiffness.

        Returns:
            float: The calculated shear modulus in Pascals [Pa].
        """
        return self.E / (2 * (1 + self.nu))
