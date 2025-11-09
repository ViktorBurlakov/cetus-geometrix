import math
from typing import List
from abc import ABC, abstractmethod
import numpy as np
from pydantic import Field, computed_field
import shapely.geometry as sg
from shapely.geometry.base import BaseGeometry
from scipy.interpolate import CubicSpline

from geometrix.geometry.calculations import transfer_properties, calculate_vertices_sums
from geometrix.geometry.gobject import GeometryObject, Centroid
from geometrix.geometry.models import Vertex, InertiaTensor, TOLERANCE, GeometrySums, OperationType
from geometrix.geometry.csg import CSGOperation, create_operation


class GeometryObject2D(GeometryObject, ABC):
    """
    Base interface for all 2D geometric objects (cross-sections).
    Defines common properties and methods for all 2D shapes, including
    basic CSG operators for combining shapes.
    """

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    @computed_field
    @property
    def volume(self) -> float:
        """The volume of a 2D object is always 0.0."""
        return 0.0

    @computed_field
    @property
    def surface_area(self) -> float:
        """The surface area of a 2D object is always 0.0."""
        return 0.0

    @computed_field
    @property
    def plane_area(self) -> float:
        """
        Returns the final cross-section area, derived from the calculated sums.

        :return: The area of the 2D geometry.
        :rtype: float
        """
        return self.sums.plane_area

    @computed_field
    @property
    @abstractmethod
    def shapely_geometry(self) -> BaseGeometry:
        """
        [ABSTRACT] Returns the Shapely object representation for topological operations.

        Must be implemented by all derived classes.
        :return: A shapely geometry object (e.g., Polygon).
        :rtype: BaseGeometry
        """
        pass

    def __add__(self, other: "GeometryObject2D") -> "Compound":
        """Overloads the '+' operator for performing a UNION operation."""
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.UNION), left=self, right=other)

    def __sub__(self, other: "GeometryObject2D") -> "Compound":
        """Overloads the '-' operator for performing a DIFFERENCE operation."""
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.DIFFERENCE), left=self, right=other)

    def __mul__(self, other: "GeometryObject2D") -> "Compound":
        """Overloads the '*' operator for performing an INTERSECTION operation."""
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.INTERSECTION), left=self, right=other)


class Rectangle(GeometryObject2D):
    """
    Represents a Rectangle. Uses analytical calculation for centroidal properties (I_c)
    and then applies a direct Steiner transfer (I_c -> I_0).
    """
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)
    x: float = Field(0.0, description="The X-coordinate of the rectangle's center.")
    y: float = Field(0.0, description="The Y-coordinate of the rectangle's center.")
    width: float = Field(gt=0, description="The width of the rectangle.")
    height: float = Field(gt=0, description="The height of the rectangle.")

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """Analytical calculation of centroidal properties (I_c)."""
        A = self.width * self.height
        I_x_own = self.width * self.height ** 3 / 12.0
        I_y_own = self.height * self.width ** 3 / 12.0
        return Centroid(
            plane_area=A,
            center=Vertex(x=self.x, y=self.y),
            inertia=InertiaTensor(Ixx=I_x_own, Iyy=I_y_own, Ixy=0.0)
        )

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """Direct Steiner transfer calculation (I_c -> I_0)."""
        data = self.centroid
        return transfer_properties(
            area=data.plane_area,
            inertia=data.inertia,
            dx=data.center.x,
            dy=data.center.y,
            reverted=False
        )

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """Generates the vertices of the rectangle in counter-clockwise order."""
        half_w, half_h = self.width / 2, self.height / 2
        vertices_ccw = np.array([
            [self.x - half_w, self.y - half_h], [self.x + half_w, self.y - half_h],
            [self.x + half_w, self.y + half_h], [self.x - half_w, self.y + half_h],
        ])
        return vertices_ccw

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        return sg.Polygon(self.vertices)

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> 'Rectangle':
        """
        Performs a universal 3D/2D translation. Only affects X and Y coordinates for 2D.

        :param dx: Translation distance along the X-axis.
        :param dy: Translation distance along the Y-axis.
        :param dz: Translation distance along the Z-axis (ignored for 2D).
        :return: A new Rectangle object at the translated position.
        """
        return self.__class__(x=self.x + dx, y=self.y + dy, width=self.width, height=self.height)


class Circle(GeometryObject2D):
    """
    Represents a Circle. Uses analytical calculation for properties (I_c -> I_0).
    The geometry is approximated by a regular polygon for topological operations.
    """
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)
    x: float = Field(0.0, description="The X-coordinate of the circle's center.")
    y: float = Field(0.0, description="The Y-coordinate of the circle's center.")
    radius: float = Field(..., gt=0, description="The radius of the circle.")
    segments: int = Field(64, ge=3, description="Number of segments for polygonal approximation.")

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """Analytical calculation of centroidal properties (I_c)."""
        A = math.pi * self.radius ** 2
        I_c = math.pi * self.radius ** 4 / 4.0
        return Centroid(
            plane_area=A,
            center=Vertex(x=self.x, y=self.y),
            inertia=InertiaTensor(Ixx=I_c, Iyy=I_c, Ixy=0.0)
        )

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """Direct Steiner transfer calculation (I_c -> I_0)."""
        data = self.centroid
        return transfer_properties(
            area=data.plane_area,
            inertia=data.inertia,
            dx=data.center.x,
            dy=data.center.y,
            reverted=False
        )

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """Generates vertices for polygonal approximation."""
        angles = np.linspace(0, 2 * math.pi, self.segments, endpoint=False)
        x = self.x + self.radius * np.cos(angles)
        y = self.y + self.radius * np.sin(angles)
        return np.stack([x, y], axis=1)

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        return sg.Polygon(self.vertices)

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> 'Circle':
        """
        Performs a universal 3D/2D translation.

        :param dx: Translation distance along the X-axis.
        :param dy: Translation distance along the Y-axis.
        :param dz: Translation distance along the Z-axis (ignored for 2D).
        :return: A new Circle object at the translated position.
        """
        return self.__class__(x=self.x + dx, y=self.y + dy, radius=self.radius, segments=self.segments)


class Polygon(GeometryObject2D):
    """
    Represents a general Polygon defined by a list of vertices.
    Uses numerical calculation for properties: I_0 is calculated using the
    Gauss-Green formula, followed by an inverse Steiner transfer (I_0 -> I_c).
    """
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)
    vertices_list: List[Vertex] = Field(
        default_factory=list, description="List of vertices defining the polygon."
    )

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        return np.array([(v.x, v.y) for v in self.vertices_list])

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        if self.vertices.size > 0:
            return sg.Polygon(self.vertices)
        return sg.Polygon()

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """Calculates I_0 (Moment of Inertia about (0,0)) using the Gauss-Green formula."""
        return calculate_vertices_sums(self.vertices)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """Calculates I_c (Centroidal Moment of Inertia) via inverse Steiner transfer (I_0 -> I_c)."""
        sums_0 = self.sums
        area = sums_0.plane_area

        cx = sums_0.static_moments.Sy / area if abs(area) > TOLERANCE.AREA_CALC else 0.0
        cy = sums_0.static_moments.Sx / area if abs(area) > TOLERANCE.AREA_CALC else 0.0

        centroidal_inertia_c = transfer_properties(
            area=area,
            inertia=sums_0.inertia,
            dx=cx,
            dy=cy,
            reverted=True
        ).inertia

        return Centroid(plane_area=area, center=Vertex(x=cx, y=cy),
                        inertia=centroidal_inertia_c)

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "Polygon":
        """
        Performs a universal 3D/2D translation by translating all vertices.

        :param dx: Translation distance along the X-axis.
        :param dy: Translation distance along the Y-axis.
        :param dz: Translation distance along the Z-axis (ignored for 2D).
        :return: A new Polygon object at the translated position.
        """
        new_vertices = [Vertex(x=v.x + dx, y=v.y + dy) for v in self.vertices_list]
        return self.__class__(vertices_list=new_vertices)


class CircularArc(Polygon):
    """
    Represents a Circular Arc sector (a pie shape).
    It is numerically approximated as a Polygon for property calculations.
    """
    x: float = Field(0.0, description="The X-coordinate of the arc's center.")
    y: float = Field(0.0, description="The Y-coordinate of the arc's center.")
    radius: float = Field(..., gt=0, description="The radius of the arc.")
    start_angle: float = Field(0.0, description="Starting angle in radians.")
    end_angle: float = Field(math.pi / 2, description="Ending angle in radians.")
    segments: int = Field(20, ge=3, description="Number of segments for polygonal approximation.")

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """Generates the arc points and closes them to the center point to form a sector."""
        angles = np.linspace(self.start_angle, self.end_angle, self.segments, endpoint=True)
        x_arc = self.x + self.radius * np.cos(angles)
        y_arc = self.y + self.radius * np.sin(angles)
        coords = np.stack([x_arc, y_arc], axis=1)
        coords = np.vstack([coords, [self.x, self.y]])  # Closes to the center for a sector
        return coords

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> 'CircularArc':
        """
        Performs a universal 3D/2D translation by translating the center coordinates.

        :param dx: Translation distance along the X-axis.
        :param dy: Translation distance along the Y-axis.
        :param dz: Translation distance along the Z-axis (ignored for 2D).
        :return: A new CircularArc object at the translated position.
        """
        return self.__class__(
            x=self.x + dx, y=self.y + dy, radius=self.radius,
            start_angle=self.start_angle, end_angle=self.end_angle,
            segments=self.segments
        )


class BSpline(Polygon):
    """
    Represents a closed B-Spline curve. Generates a polygon from control points
    using the CubicSpline method from SciPy. This resulting polygon is then used
    for property calculations.
    """
    vertices_list: List[Vertex] = Field(
        default_factory=list, min_items=3, description="List of control points for the B-Spline."
    )
    num_points: int = Field(100, ge=10, description="Number of points to approximate the curve.")

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """
        Calculates the spline points based on the control points using a natural cubic spline.
        The resulting curve is closed by adding the first point as the last point if necessary.
        """
        coords = np.array([(v.x, v.y) for v in self.vertices_list])
        if len(coords) < 3:
            return np.array([])

        # Calculate parameter t based on chord length
        dx = np.diff(coords[:, 0])
        dy = np.diff(coords[:, 1])
        distances = np.sqrt(dx ** 2 + dy ** 2)
        t = np.insert(np.cumsum(distances), 0, 0)

        bc_type = 'natural'

        cs_x = CubicSpline(t, coords[:, 0], bc_type=bc_type)
        cs_y = CubicSpline(t, coords[:, 1], bc_type=bc_type)

        t_new = np.linspace(t[0], t[-1], self.num_points, endpoint=True)
        x_new = cs_x(t_new)
        y_new = cs_y(t_new)

        final_vertices = np.stack([x_new, y_new], axis=1)

        # Close the polygon if the start and end points are not close enough
        if not np.allclose(final_vertices[0], final_vertices[-1], atol=TOLERANCE.GEOMETRY):
            final_vertices = np.vstack([final_vertices, final_vertices[0]])

        return final_vertices

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "BSpline":
        """
        Translates all control vertices of the B-Spline.

        :param dx: Translation distance along the X-axis.
        :param dy: Translation distance along the Y-axis.
        :param dz: Translation distance along the Z-axis (ignored for 2D).
        :return: A new BSpline object at the translated position.
        """
        new_vertices = [Vertex(x=v.x + dx, y=v.y + dy) for v in self.vertices_list]
        return self.__class__(vertices_list=new_vertices, num_points=self.num_points)


class Compound(GeometryObject2D):
    """
    Represents a CSG (Constructive Solid Geometry) tree node.
    This is a binary node that stores the operation object and the two operand
    GeometryObject2D objects (left and right).
    """
    op_type: OperationType = Field(OperationType.COMPOUND,
                                   frozen=True)  # Use COMPOUND as op_type for the tree node
    operation: CSGOperation = Field(default_factory=lambda: create_operation(OperationType.UNION), frozen=True)
    left: GeometryObject2D
    right: GeometryObject2D

    # --- Convenience operators for creating a Compound ---
    def __add__(self, other: "GeometryObject2D") -> "Compound":
        """Overloads the '+' operator for performing a UNION operation."""
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.UNION), left=self, right=other)

    def __sub__(self, other: "GeometryObject2D") -> "Compound":
        """Overloads the '-' operator for performing a DIFFERENCE operation."""
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.DIFFERENCE), left=self, right=other)

    def __mul__(self, other: "GeometryObject2D") -> "Compound":
        """Overloads the '*' operator for performing an INTERSECTION operation."""
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.INTERSECTION), left=self, right=other)

    # --- Implementation of abstract methods ---

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        """
        Recursively computes the final geometry by delegating the operation execution.

        :return: The resulting shapely geometry object after the CSG operation.
        :rtype: BaseGeometry
        """
        geom_left = self.left.shapely_geometry
        geom_right = self.right.shapely_geometry
        return self.operation.execute_shapely(geom_left, geom_right)

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """
        Calculates the geometric sums (Area, Static Moments, Moments of Inertia)
        by delegating the logic to the operation object.
        """
        final_geom = self.shapely_geometry  # Compute once
        return self.operation.calculate_sums(self.left, self.right, final_geom)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """
        Calculates the centroid and centroidal inertia by delegating the logic
        to the operation object.
        """
        final_geom = self.shapely_geometry  # Compute once
        return self.operation.calculate_centroid(self.left, self.right, final_geom)

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> 'Compound':
        """
        Translates both child nodes recursively, preserving the CSG tree structure.

        :param dx: Translation distance along the X-axis.
        :param dy: Translation distance along the Y-axis.
        :param dz: Translation distance along the Z-axis (ignored for 2D).
        :return: A new Compound object with translated children.
        """
        new_left = self.left.translate(dx, dy, dz)
        new_right = self.right.translate(dx, dy, dz)
        return self.__class__(operation=self.operation, left=new_left, right=new_right)

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """
        Returns the vertices of the exterior boundary of the final geometry.

        :return: An array of shape (N, 2) containing the boundary vertices.
        :rtype: np.ndarray
        """
        final_geom = self.shapely_geometry
        if isinstance(final_geom, sg.Polygon):
            return np.array(final_geom.exterior.coords)
        return np.array([])
