from abc import ABC, abstractmethod

from pydantic import BaseModel, Field
import shapely.geometry as sg
from shapely.geometry.base import BaseGeometry
import numpy as np

from geometrix.geometry.centroid import Centroid
from geometrix.geometry.models import GeometrySums, OperationType, TOLERANCE, Vertex
from geometrix.geometry.calculations import calculate_vertices_sums, transfer_properties


def _calculate_sums_from_shapely(shapely_geometry: BaseGeometry) -> GeometrySums:
    """
    Helper function to calculate aggregate geometric sums (Area, S, I)
    by integrating over the contour of the provided Shapely geometry object.

    This handles MultiPolygons and Polygons with holes.
    """
    total_sums = GeometrySums()

    # 1. Normalize geometry to a list of Polygons
    polygons: list[sg.Polygon] = []
    if isinstance(shapely_geometry, sg.MultiPolygon):
        polygons.extend(list(shapely_geometry.geoms))
    elif isinstance(shapely_geometry, sg.Polygon):
        polygons.append(shapely_geometry)
    else:
        # Result is an empty geometry, point, or line (zero area)
        return total_sums

    # 2. Integrate each Polygon (exterior + holes)
    for poly in polygons:
        # Add outer boundary sums
        total_sums += calculate_vertices_sums(np.array(poly.exterior.coords))

        # Subtract hole sums (by reversing the order of vertices)
        for interior in poly.interiors:
            interior_coords = np.array(interior.coords)
            total_sums += calculate_vertices_sums(interior_coords[::-1])  # Subtraction via reversed order

    return total_sums


# --- Base CSG Operation ---

class CSGOperation(BaseModel, ABC):
    """
    Abstract base class for all Boolean operations (Union, Difference, Intersection)
    in the Constructive Solid Geometry (CSG) tree.

    This class defines the interface for two critical tasks:
    1. Executing the Boolean operation using the Shapely library.
    2. Calculating the final aggregate geometric sums (Area, S, I) based on
       the result of the operation.
    """
    op_type: OperationType = Field(..., frozen=True,
                                   description="The type of the CSG operation (e.g., UNION, DIFFERENCE).")

    class Config:
        frozen = True
        arbitrary_types_allowed = True

    @abstractmethod
    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        """
        [ABSTRACT] Executes the core Boolean operation on two Shapely geometry objects.
        """
        pass

    @abstractmethod
    def calculate_sums(
            self,
            left_obj: 'GeometryObject2D',
            right_obj: 'GeometryObject2D',
            shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        """
        [ABSTRACT] Calculates the aggregate geometric sums of the final object.

        The shapely_geometry parameter represents the result of the Shapely operation
        and is used for robust contour integration.
        """
        pass

    def calculate_centroid(
            self,
            left_obj: 'GeometryObject2D',
            right_obj: 'GeometryObject2D',
            shapely_geometry: BaseGeometry
    ) -> Centroid:
        """
        Calculates the centroid based on the final geometric sums.

        This method is generally non-abstract as the centroid is always derived
        from the calculated sums using a standard formula (c = S / A).
        """
        total_sums = self.calculate_sums(left_obj, right_obj, shapely_geometry)

        # If the area is zero, return an empty centroid
        if abs(total_sums.plane_area) < TOLERANCE.AREA_CALC:
            return Centroid()  # Assumes Centroid() returns an object with zeroed properties

        # Determine the new global center of mass
        cx_new = total_sums.static_moments.Sy / total_sums.plane_area
        cy_new = total_sums.static_moments.Sx / total_sums.plane_area

        # Transfer moments of inertia to the new global center of mass (reverse Steiner's theorem)
        centroidal_inertia_c = transfer_properties(
            area=total_sums.plane_area,
            inertia=total_sums.inertia,
            dx=cx_new,
            dy=cy_new,
            reverted=True
        ).inertia

        return Centroid(
            plane_area=total_sums.plane_area,
            center=Vertex(x=cx_new, y=cy_new),
            inertia=centroidal_inertia_c
        )


class UnionOperation(CSGOperation):
    """Implements the CSG UNION operation (Addition: A + B)."""

    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        """Performs Shapely's union operation."""
        return left_geom.union(right_geom)

    def calculate_sums(self,
            left_obj: 'GeometryObject2D',
            right_obj: 'GeometryObject2D',
            shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        """
        Calculates sums robustly by integrating the final Shapely geometry contour.
        """
        return _calculate_sums_from_shapely(shapely_geometry)


class DifferenceOperation(CSGOperation):
    """Implements the CSG DIFFERENCE operation (Subtraction: A - B, where B is a cutout/hole)."""

    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        """Performs Shapely's difference operation."""
        return left_geom.difference(right_geom)

    def calculate_sums(
            self,
            left_obj: 'GeometryObject2D',
            right_obj: 'GeometryObject2D',
            shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        """
        Calculates sums robustly by integrating the final Shapely geometry contour.
        """
        return _calculate_sums_from_shapely(shapely_geometry)


class IntersectionOperation(CSGOperation):
    """Implements the CSG INTERSECTION operation (Multiplication: A * B)."""

    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        """Performs Shapely's intersection operation."""
        return left_geom.intersection(right_geom)

    def calculate_sums(
            self,
            left_obj: 'GeometryObject2D',
            right_obj: 'GeometryObject2D',
            shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        """
        Calculates sums robustly by integrating the final Shapely geometry contour.
        """
        return _calculate_sums_from_shapely(shapely_geometry)


# --- Factory Function ---

def create_operation(op_type: OperationType) -> CSGOperation:
    """
    Factory function to instantiate the correct concrete CSG operation object
    based on the specified operation type.
    """
    if op_type == OperationType.UNION:
        return UnionOperation(op_type=op_type)
    elif op_type == OperationType.DIFFERENCE:
        return DifferenceOperation(op_type=op_type)
    elif op_type == OperationType.INTERSECTION:
        return IntersectionOperation(op_type=op_type)
    else:
        raise ValueError(f"Unknown CSG operation type: {op_type}")
