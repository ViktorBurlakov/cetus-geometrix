from enum import Enum
import numpy as np
from pydantic import BaseModel, Field, computed_field


class TOLERANCE:
    """
    Global tolerance constants used for floating-point comparisons within the geometry module.
    """
    AREA_CALC = 1e-9  # Tolerance for checking division by zero (e.g., when calculating centroid)
    GEOMETRY = 1e-6  # General tolerance for geometric comparisons


class OperationType(str, Enum):
    """
    Types of Boolean operations used in Constructive Solid Geometry (CSG) nodes.
    """
    UNION = "UNION"  # Union operation (+)
    DIFFERENCE = "DIFFERENCE"  # Difference operation (-)
    INTERSECTION = "INTERSECTION"  # Intersection operation (*)
    PRIMITIVE = "PRIMITIVE"  # For leaf nodes (Rectangle, Circle, Polygon, BSpline)
    COMPOUND = "COMPOUND"  # For CSG tree nodes representing a combination


class Vertex(BaseModel):
    """
    Represents a universal 3D/2D coordinate point.
    In 2D contexts, the z-coordinate is typically 0.0.
    """
    x: float = Field(0.0, description="X-coordinate [m].")
    y: float = Field(0.0, description="Y-coordinate [m].")
    z: float = Field(0.0, description="Z-coordinate [m]. Default is 0.0 for 2D geometry.")

    class Config:
        frozen = True


class BoundingBox(BaseModel):
    """
    Universal model for a Bounding Box in 2D or 3D space.
    """
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float = Field(0.0, description="Minimum Z-coordinate [m].")
    max_z: float = Field(0.0, description="Maximum Z-coordinate [m].")

    class Config:
        frozen = True

    @computed_field
    @property
    def width(self):
        """Width of the bounding box (Max X - Min X) [m]."""
        return self.max_x - self.min_x

    @computed_field
    @property
    def height(self):
        """Height of the bounding box (Max Y - Min Y) [m]."""
        return self.max_y - self.min_y

    @computed_field
    @property
    def depth(self):
        """Depth of the bounding box (Max Z - Min Z) [m]. For 2D, this is 0.0."""
        return self.max_z - self.min_z


class StaticMoments(BaseModel):
    """
    Universal Static Moments (Sx, Sy, Sz) relative to the global origin (0,0,0).
    In 2D (Area): Area Static Moments. In 3D (Volume/Mass): Volume or Mass Static Moments.
    These are the moments of the first order, crucial for centroid calculation.
    """
    Sx: float = Field(0.0, description="Static moment with respect to the X-axis ($S_{y0}$) [m^3 or kg*m].")
    Sy: float = Field(0.0, description="Static moment with respect to the Y-axis ($S_{x0}$) [m^3 or kg*m].")
    Sz: float = Field(0.0, description="Static moment with respect to the Z-axis ($S_{z0}$) [m^3 or kg*m]. 0.0 for 2D.")

    class Config:
        frozen = True

    def __add__(self, other: 'StaticMoments') -> 'StaticMoments':
        """Implements the addition operator for aggregation (CSG UNION)."""
        if not isinstance(other, StaticMoments):
            return NotImplemented
        return StaticMoments(
            Sx=self.Sx + other.Sx,
            Sy=self.Sy + other.Sy,
            Sz=self.Sz + other.Sz
        )

    def __sub__(self, other: 'StaticMoments') -> 'StaticMoments':
        """Implements the subtraction operator (for holes/cutouts - CSG DIFFERENCE)."""
        if not isinstance(other, StaticMoments):
            return NotImplemented
        return StaticMoments(
            Sx=self.Sx - other.Sx,
            Sy=self.Sy - other.Sy,
            Sz=self.Sz - other.Sz
        )


class InertiaTensor(BaseModel):
    """
    Universal Inertia Tensor (2D: Area, 3D: Mass/Volume) relative to the global origin (0,0,0).
    Uses 6 independent components (symmetric 3x3 matrix) for moments and products of inertia.
    """
    # Moments of Inertia (Diagonal components)
    Ixx: float = Field(0.0, description="Moment of inertia about the X-axis ($I_{x0}$) [m^4 or kg*m^2].")
    Iyy: float = Field(0.0, description="Moment of inertia about the Y-axis ($I_{y0}$) [m^4 or kg*m^2].")
    Izz: float = Field(0.0,
                       description="Moment of inertia about the Z-axis ($I_{z0}$) / Polar moment in 2D [m^4 or kg*m^2].")

    # Products of Inertia (Off-diagonal components)
    Ixy: float = Field(0.0, description="Product of inertia $I_{xy}$ [m^4 or kg*m^2].")
    Ixz: float = Field(0.0, description="Product of inertia $I_{xz}$. 0.0 in 2D geometry [m^4 or kg*m^2].")
    Iyz: float = Field(0.0, description="Product of inertia $I_{yz}$. 0.0 in 2D geometry [m^4 or kg*m^2].")

    J_torsion: float | None = Field(None,
                                    description="Torsional constant ($J$). Used for $GJ_{torsion}$ calculation. [m^4].")

    class Config:
        frozen = True

    def ndarray(self, dim: int = 3) -> np.ndarray:
        """
        Returns the tensor components as a NumPy 2x2 (Area) or 3x3 (Mass/Volume) matrix.
        Note: Products of inertia are stored as negative in the matrix for standard tensor convention.
        """
        if dim == 2:
            # 2D case (Area)
            return np.array([
                [self.Ixx, -self.Ixy],
                [-self.Ixy, self.Iyy]
            ], dtype=np.float64)
        else:
            # 3D case (Mass/Volume)
            return np.array([
                [self.Ixx, -self.Ixy, -self.Ixz],
                [-self.Ixy, self.Iyy, -self.Iyz],
                [-self.Ixz, -self.Iyz, self.Izz]
            ], dtype=np.float64)

    @computed_field
    @property
    def I_polar(self) -> float:
        """
        Polar Moment of Inertia ($I_p$ or $J_{polar}$) [m^4 or kg*m^2].
        Equal to the sum of the moments in the XY-plane ($I_{xx} + I_{yy}$).
        """
        return self.Ixx + self.Iyy

    def __add__(self, other: 'InertiaTensor') -> 'InertiaTensor':
        """Adds two tensors (for aggregation - CSG UNION)."""
        if not isinstance(other, InertiaTensor):
            raise TypeError("Only InertiaTensor can be added.")

        j_self = self.J_torsion if self.J_torsion is not None else 0.0
        j_other = other.J_torsion if other.J_torsion is not None else 0.0

        return InertiaTensor(
            Ixx=self.Ixx + other.Ixx, Iyy=self.Iyy + other.Iyy, Izz=self.Izz + other.Izz,
            Ixy=self.Ixy + other.Ixy, Ixz=self.Ixz + other.Ixz, Iyz=self.Iyz + other.Iyz,
            J_torsion=j_self + j_other
        )

    def __sub__(self, other: 'InertiaTensor') -> 'InertiaTensor':
        """Subtracts one tensor from another (for holes/cutouts - CSG DIFFERENCE)."""
        if not isinstance(other, InertiaTensor):
            raise TypeError("Only InertiaTensor can be subtracted.")

        j_self = self.J_torsion if self.J_torsion is not None else 0.0
        j_other = other.J_torsion if other.J_torsion is not None else 0.0

        return InertiaTensor(
            Ixx=self.Ixx - other.Ixx, Iyy=self.Iyy - other.Iyy, Izz=self.Izz - other.Izz,
            Ixy=self.Ixy - other.Ixy, Ixz=self.Ixz - other.Ixz, Iyz=self.Iyz - other.Iyz,
            J_torsion=j_self - j_other
        )


class GeometrySums(BaseModel):
    """
    Universal Model for raw geometric sums (I_0) relative to the global origin (0,0,0).
    It aggregates primary measures (Area/Volume) and first/second order moments.

    These values are the result of raw integration before translation to the
    centroidal axes using the Parallel Axis Theorem (Steiner's Theorem).
    """
    plane_area: float = Field(0.0, description="Cross-sectional area [m^2]. 0.0 for pure 3D volume.")
    volume: float = Field(0.0, description="Volume of the solid [m^3]. 0.0 for pure 2D cross-section.")
    surface_area: float = Field(0.0, description="Surface area of the solid [m^2]. 0.0 for 2D cross-section.")

    static_moments: StaticMoments = Field(description="First order moments (Static Moments) relative to the origin.")
    inertia: InertiaTensor = Field(description="Second order moments (Inertia Tensor) relative to the origin.")

    class Config:
        frozen = True

    @computed_field
    @property
    def primary_measure(self) -> float:
        """Returns the primary non-zero measure (Cross-Sectional Area or Volume)."""
        return self.plane_area if self.plane_area > TOLERANCE.AREA_CALC else self.volume

    def __add__(self, other: 'GeometrySums') -> 'GeometrySums':
        """Implements the addition operator for aggregation (CSG UNION)."""
        if not isinstance(other, GeometrySums):
            return NotImplemented
        return GeometrySums(
            plane_area=self.plane_area + other.plane_area,
            volume=self.volume + other.volume,
            surface_area=self.surface_area + other.surface_area,
            static_moments=self.static_moments + other.static_moments,
            inertia=self.inertia + other.inertia
        )

    def __sub__(self, other: 'GeometrySums') -> 'GeometrySums':
        """Implements the subtraction operator (for holes/cutouts - CSG DIFFERENCE)."""
        if not isinstance(other, GeometrySums):
            return NotImplemented
        return GeometrySums(
            plane_area=self.plane_area - other.plane_area,
            volume=self.volume - other.volume,
            surface_area=self.surface_area - other.surface_area,
            static_moments=self.static_moments - other.static_moments,
            inertia=self.inertia - other.inertia
        )


class PrincipalInertia(BaseModel):
    """
    Model for Principal Moments of Inertia and the angle of rotation (typically 2D area properties).
    These moments represent the maximum and minimum inertia values in the plane.
    """
    I1: float = Field(0.0, description="First (Maximum) Principal Moment of Inertia [m^4 or kg*m^2].")
    I2: float = Field(0.0, description="Second (Minimum) Principal Moment of Inertia [m^4 or kg*m^2].")
    alpha: float = Field(0.0, description="Angle of rotation (in radians) from the local X-axis to the $I_1$ axis.")

    class Config:
        frozen = True


class RadiiOfGyration(BaseModel):
    """
    Model for the Radii of Gyration of a cross-section or 3D solid relative to centroidal axes.
    The radius of gyration is a measure of how the mass/area is distributed around an axis.
    """
    rx: float = Field(0.0, description="Radius of gyration relative to the centroidal X-axis ($r_x$) [m].")
    ry: float = Field(0.0, description="Radius of gyration relative to the centroidal Y-axis ($r_y$) [m].")
    r1: float = Field(0.0, description="Radius of gyration relative to the Principal Axis 1 (Maximum) ($r_1$) [m].")
    r2: float = Field(0.0, description="Radius of gyration relative to the Principal Axis 2 (Minimum) ($r_2$) [m].")

    class Config:
        frozen = True
