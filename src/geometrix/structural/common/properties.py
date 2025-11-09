import numpy as np
from pydantic import BaseModel, Field, computed_field


class ShearAreas(BaseModel):
    """
    Encapsulates effective shear areas for different directions.

    These parameters are used for calculating shear deformations.

    Attributes:
        shear_area_y (float): Effective shear area for Y-direction [m^2].
        shear_area_x (float): Effective shear area for X-direction [m^2].
        shear_area_z (float): Effective shear area for Z-direction [m^2].
    """
    shear_area_y: float = Field(0.0, description="Effective shear area for Y-direction ($A_{shear,y}$) [m^2].")
    shear_area_x: float = Field(0.0, description="Effective shear area for X-direction ($A_{shear,x}$) [m^2].")
    shear_area_z: float = Field(0.0, description="Effective shear area for Z-direction ($A_{shear,z}$) [m^2].")

    class Config:
        frozen = True

class StiffnessProperties(BaseModel):
    """
    Encapsulates all standard stiffness characteristics of an element.

    Used to describe the element's resistance to deformation under load.

    Attributes:
        EI_xx (float): Bending stiffness [N*m^2] about the X-axis.
        EI_yy (float): Bending stiffness [N*m^2] about the Y-axis.
        GJ_torsion (float): Torsional stiffness [N*m^2].
        EA_axial (float): Axial stiffness [N].
        GA_shear_x (float): Shear stiffness [N] along the X-axis.
        GA_shear_y (float): Shear stiffness [N] along the Y-axis.
        GA_shear_z (float): Shear stiffness [N] along the Z-axis.
    """
    EI_xx: float = Field(0.0, description="Bending stiffness [N*m^2] about the X-axis.")
    EI_yy: float = Field(0.0, description="Bending stiffness [N*m^2] about the Y-axis.")
    GJ_torsion: float = Field(0.0, description="Torsional stiffness [N*m^2].")
    EA_axial: float = Field(0.0, description="Axial stiffness [N].")
    GA_shear_x: float = Field(0.0, description="Shear stiffness [N] along the X-axis.")
    GA_shear_y: float = Field(0.0, description="Shear stiffness [N] along the Y-axis.")
    GA_shear_z: float = Field(0.0, description="Shear stiffness [N] along the Z-axis.")

    class Config:
        frozen = True

class DistributedInertialProperties(BaseModel):
    """
    Encapsulates calculated distributed (per unit length) mass-inertial properties.

    These properties describe the distribution of mass and its inertia along an element.

    Attributes:
        m_prime_effective (float): Effective distributed mass [kg/m].
        Im_prime_effective (float): Effective distributed mass moment of inertia [kg*m^2/m].
    """
    m_prime_effective: float = Field(description="Effective distributed mass [kg/m].")
    Im_prime_effective: float = Field(description="Effective distributed mass moment of inertia [kg*m^2/m].")

    class Config:
        frozen = True

class LinearStructureSectionProperties(BaseModel):
    """
    Encapsulates discretization parameters and distributed structural properties
    along a one-dimensional axis (e.g., for a beam or rod).

    This class is central for defining the physical characteristics of a structural element
    to be used in analysis. Properties are given as arrays, allowing modeling
    of elements with varying cross-section or material.

    Attributes:
        section_count (int): Number of discrete sections (N).
        delta_x (float): Length of one section (Delta_Z) [m].
        z_coords (np.ndarray): Z-coordinates of the cross-sections (from 0 to L). Length is N+1.
        m_prime_array (np.ndarray): Distributed mass [kg/m] for each point (N+1 points).
        EI_y_array (np.ndarray): Bending stiffness [N*m^2] for each point (N+1 points).
        Im_prime_array (np.ndarray): Distributed mass moment of inertia [kg*m^2/m] for each point (N+1 points).
        GJ_array (np.ndarray): Torsional stiffness [N*m^2] for each point (N+1 points).
    """
    section_count: int = Field(gt=0, description="Number of discrete sections (N).")
    delta_x: float = Field(gt=0, description="Length of one section (Delta_Z) [m].")
    z_coords: np.ndarray = Field(description="Z-coordinates of the cross-sections (from 0 to L). Length is N+1.")

    m_prime_array: np.ndarray = Field(description="Distributed mass [kg/m] for each point (N+1 points).")
    EI_y_array: np.ndarray = Field(description="Bending stiffness [N*m^2] for each point (N+1 points).")
    Im_prime_array: np.ndarray = Field(description="Distributed mass moment of inertia [kg*m^2/m] for each point (N+1 points).")
    GJ_array: np.ndarray = Field(description="Torsional stiffness [N*m^2] for each point (N+1 points).")

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    @classmethod
    def __pydantic_init_validator__(cls, values):
        """
        Pydantic validator that checks if array lengths match the number of sections (N+1).

        Raises:
            ValueError: If any array's length does not match the expected (N+1).
        """
        n = values.get('section_count')
        if n is not None:
            expected_len = n + 1
            for name in ['m_prime_array', 'EI_y_array', 'Im_prime_array', 'GJ_array', 'z_coords']:
                arr = values.get(name)
                if arr is not None and len(arr) != expected_len:
                    raise ValueError(f"Length of array '{name}' ({len(arr)}) does not match expected ({expected_len} for N={n}).")
        return values

    @computed_field
    @property
    def total_length(self) -> float:
        """
        Calculates the total length of the structure based on Z-coordinates.

        Returns:
            float: Total length of the element in meters.
        """
        if len(self.z_coords) > 1:
            return self.z_coords[-1] - self.z_coords[0]
        return 0.0

    @computed_field
    @property
    def total_mass(self) -> float:
        """
        Calculates the total mass of the structure by integrating
        the distributed mass over the length using the trapezoidal rule.

        Returns:
            float: Total mass of the element in kilograms.
        """
        return np.trapezoid(self.m_prime_array, self.z_coords)
