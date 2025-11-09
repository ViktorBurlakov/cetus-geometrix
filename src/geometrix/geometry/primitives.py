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
    Базовий інтерфейс для всіх 2D геометричних об'єктів (Перерізів).
    """

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    @computed_field
    @property
    def volume(self) -> float:
        """Об'єм 2D об'єкта завжди 0.0."""
        return 0.0

    @computed_field
    @property
    def surface_area(self) -> float:
        """Площа поверхні 2D об'єкта завжди 0.0."""
        return 0.0

    @computed_field
    @property
    def plane_area(self) -> float:
        """Повертає фінальну площу перерізу (береться з обчислених сум)."""
        return self.sums.plane_area

    @computed_field
    @property
    @abstractmethod
    def shapely_geometry(self) -> BaseGeometry:
        """[ABSTRACT] Повертає об'єкт Shapely для топологічних операцій."""
        pass

    def __add__(self, other: "GeometryObject2D") -> "Compound":
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.UNION), left=self, right=other)

    def __sub__(self, other: "GeometryObject2D") -> "Compound":
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.DIFFERENCE), left=self, right=other)

    def __mul__(self, other: "GeometryObject2D") -> "Compound":
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.INTERSECTION), left=self, right=other)


class Rectangle(GeometryObject2D):
    """Прямокутник. Аналітичний розрахунок I_c -> I_0 (Прямий трансфер Штейнера)."""
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)
    x: float = Field(0.0)
    y: float = Field(0.0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """Аналітичний розрахунок I_c."""
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
        """Прямий трансфер Штейнера (I_c -> I_0)."""
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
        """Генерація вершин."""
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
        """Універсальна 3D/2D трансляція."""
        return self.__class__(x=self.x + dx, y=self.y + dy, width=self.width, height=self.height)


class Circle(GeometryObject2D):
    """Коло. Аналітичний розрахунок I_c -> I_0."""
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)
    x: float = Field(0.0)
    y: float = Field(0.0)
    radius: float = Field(..., gt=0)
    segments: int = Field(64, ge=3)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """Аналітичний розрахунок I_c."""
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
        """Прямий трансфер Штейнера (I_c -> I_0)."""
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
        """Генерація вершин для полігональної апроксимації."""
        angles = np.linspace(0, 2 * math.pi, self.segments, endpoint=False)
        x = self.x + self.radius * np.cos(angles)
        y = self.y + self.radius * np.sin(angles)
        return np.stack([x, y], axis=1)

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        return sg.Polygon(self.vertices)

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> 'Circle':
        """Універсальна 3D/2D трансляція."""
        return self.__class__(x=self.x + dx, y=self.y + dy, radius=self.radius, segments=self.segments)


class Polygon(GeometryObject2D):
    """Багатокутник. Чисельний розрахунок I_0 -> I_c (Зворотний трансфер Штейнера)."""
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)
    vertices_list: List[Vertex] = Field(default_factory=list)

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
        """I_0: Обчислення через формулу Гаусса-Гріна."""
        return calculate_vertices_sums(self.vertices)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """I_c: Зворотний трансфер Штейнера (I_0 -> I_c)."""
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
        """Універсальна 3D/2D трансляція."""
        new_vertices = [Vertex(x=v.x + dx, y=v.y + dy) for v in self.vertices_list]
        return self.__class__(vertices_list=new_vertices)


class CircularArc(Polygon):
    """Круговий сектор. Чисельна апроксимація полігоном."""
    x: float = Field(0.0)
    y: float = Field(0.0)
    radius: float = Field(..., gt=0)
    start_angle: float = Field(0.0)
    end_angle: float = Field(math.pi / 2)
    segments: int = Field(20, ge=3)

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """Генерація точок дуги та замикання їх до центру (сектор)."""
        angles = np.linspace(self.start_angle, self.end_angle, self.segments, endpoint=True)
        x_arc = self.x + self.radius * np.cos(angles)
        y_arc = self.y + self.radius * np.sin(angles)
        coords = np.stack([x_arc, y_arc], axis=1)
        coords = np.vstack([coords, [self.x, self.y]])  # Замикаємо до центру для сектора
        return coords

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> 'CircularArc':
        """Універсальна 3D/2D трансляція."""
        return self.__class__(
            x=self.x + dx, y=self.y + dy, radius=self.radius,
            start_angle=self.start_angle, end_angle=self.end_angle,
            segments=self.segments
        )


class BSpline(Polygon):
    """
    Сплайн. Генерує багатокутник з контрольних точок за допомогою CubicSpline (SciPy).
    """
    vertices_list: List[Vertex] = Field(default_factory=list, min_items=3)
    num_points: int = Field(100, ge=10)  # Кількість точок для апроксимації кривої

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """Обчислення точок сплайна на основі контрольних точок."""

        coords = np.array([(v.x, v.y) for v in self.vertices_list])
        if len(coords) < 3:
            return np.array([])

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

        if not np.allclose(final_vertices[0], final_vertices[-1], atol=TOLERANCE.GEOMETRY):
            final_vertices = np.vstack([final_vertices, final_vertices[0]])

        return final_vertices

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "BSpline":
        """Трансляція всіх контрольних вершин."""
        new_vertices = [Vertex(x=v.x + dx, y=v.y + dy) for v in self.vertices_list]
        return self.__class__(vertices_list=new_vertices, num_points=self.num_points)


class Compound(GeometryObject2D):
    """
    Вузол CSG-дерева. Бінарний вузол, що зберігає об'єкт операції та два операнди.
    """
    op_type: OperationType = Field(OperationType.COMPOUND,
                                   frozen=True)  # Можна використати COMPOUND як op_type для вузла дерева
    operation: CSGOperation = Field(default_factory=lambda: create_operation(OperationType.UNION), frozen=True)
    left: GeometryObject2D
    right: GeometryObject2D

    # --- Зручні оператори для створення Compound ---
    def __add__(self, other: "GeometryObject2D") -> "Compound":
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.UNION), left=self, right=other)

    def __sub__(self, other: "GeometryObject2D") -> "Compound":
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.DIFFERENCE), left=self, right=other)

    def __mul__(self, other: "GeometryObject2D") -> "Compound":
        if not isinstance(other, GeometryObject2D):
            return NotImplemented
        return Compound(operation=create_operation(OperationType.INTERSECTION), left=self, right=other)

    # --- Реалізація абстрактних методів ---

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        """Рекурсивно обчислює фінальну геометрію, делегуючи операцію."""
        geom_left = self.left.shapely_geometry
        geom_right = self.right.shapely_geometry
        return self.operation.execute_shapely(geom_left, geom_right)

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """
        Обчислює геометричні суми, делегуючи логіку об'єкту операції.
        """
        final_geom = self.shapely_geometry  # Обчислюємо один раз
        return self.operation.calculate_sums(self.left, self.right, final_geom)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """
        Обчислює центроїд, делегуючи логіку об'єкту операції.
        """
        final_geom = self.shapely_geometry  # Обчислюємо один раз
        return self.operation.calculate_centroid(self.left, self.right, final_geom)

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> 'Compound':
        """Транслює обидва дочірні вузли, зберігаючи структуру CSG-дерева."""
        new_left = self.left.translate(dx, dy, dz)
        new_right = self.right.translate(dx, dy, dz)
        return self.__class__(operation=self.operation, left=new_left, right=new_right)

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """Повертає вершини зовнішнього контуру фінальної геометрії."""
        final_geom = self.shapely_geometry
        if isinstance(final_geom, sg.Polygon):
            return np.array(final_geom.exterior.coords)
        return np.array([])
