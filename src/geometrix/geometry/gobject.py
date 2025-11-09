from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.centroid import Centroid
from geometrix.geometry.models import TOLERANCE, GeometrySums, OperationType


T = TypeVar('T', bound='GeometryObject')


class GeometryObject(BaseModel, ABC, Generic[T]):
    """
    Abstract base interface for all geometric objects (2D and 3D).

    Every object acts as a node in the Constructive Solid Geometry (CSG) tree.
    This class defines the fundamental abstract methods for calculating geometric
    properties and provides base implementations for centroid calculation.
    """
    op_type: OperationType = Field(
        OperationType.PRIMITIVE,
        frozen=True,
        description="The type of CSG operation represented by this node (e.g., PRIMITIVE, UNION, DIFFERENCE)."
    )

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    @computed_field
    @property
    @abstractmethod
    def sums(self) -> GeometrySums:
        """
        [ABSTRACT] Returns the aggregated raw geometric sums (area/volume,
        static moments, moments of inertia) of the object relative to the
        GLOBAL coordinate origin (0,0,0).

        This property is the foundation for all further centroidal calculations.
        """
        pass

    @computed_field
    @property
    @abstractmethod
    def centroid(self) -> Centroid:
        """
        [ABSTRACT] Returns the Centroid object, which contains the center of mass/centroid
        coordinates and the moments of inertia RELATIVE to this centroid.
        """
        pass

    @computed_field
    @property
    @abstractmethod
    def primary_measure(self) -> float:
        """
        [ABSTRACT] Returns the object's primary measure: cross-sectional area (2D) or volume (3D).
        """
        pass

    @abstractmethod
    def translate(self: T, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> T:
        """
        [ABSTRACT] Translates the geometric object by the specified offsets (dx, dy, dz).
        Returns a new, translated, immutable object instance.

        Args:
            dx (float): Displacement along the X-axis [m].
            dy (float): Displacement along the Y-axis [m].
            dz (float): Displacement along the Z-axis [m].

        Returns:
            T: A new instance of the geometric object at the translated location.
        """
        pass

    # Boolean Operators
    def __add__(self: T, other: 'GeometryObject') -> 'GeometryObject':
        """
        Implements the addition operator for CSG UNION.
        This method should be overridden in concrete geometric classes (e.g., GeometryObject2D).
        """
        return NotImplemented

    def __sub__(self: T, other: 'GeometryObject') -> 'GeometryObject':
        """
        Implements the subtraction operator for CSG DIFFERENCE (cutouts/holes).
        This method should be overridden in concrete geometric classes.
        """
        return NotImplemented

    def __mul__(self: T, other: 'GeometryObject') -> 'GeometryObject':
        """
        Implements the multiplication operator for CSG INTERSECTION.
        This method should be overridden in concrete geometric classes.
        """
        return NotImplemented

    @computed_field
    @property
    def cx(self) -> float:
        """
        X-coordinate of the final centroid (calculated from Sy_0 / Primary_Measure).
        """
        sums = self.sums
        measure = self.primary_measure
        # Centroid X-coord = Sy / Area (or Volume)
        return sums.static_moments.Sy / measure if abs(measure) > TOLERANCE.AREA_CALC else 0.0

    @computed_field
    @property
    def cy(self) -> float:
        """
        Y-coordinate of the final centroid (calculated from Sx_0 / Primary_Measure).
        """
        sums = self.sums
        measure = self.primary_measure
        # Centroid Y-coord = Sx / Area (or Volume)
        return sums.static_moments.Sx / measure if abs(measure) > TOLERANCE.AREA_CALC else 0.0

    @computed_field
    @property
    def cz(self) -> float:
        """
        Z-coordinate of the final centroid (calculated from Sz_0 / Primary_Measure).
        For 2D cross-sections, this is typically 0.0.
        """
        sums = self.sums
        measure = self.primary_measure
        # Centroid Z-coord = Sz / Area (or Volume)
        return sums.static_moments.Sz / measure if abs(measure) > TOLERANCE.AREA_CALC else 0.0
