import math
from typing import List
from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
from pydantic import BaseModel, Field, computed_field
import shapely.geometry as sg
from shapely.geometry.base import BaseGeometry
from scipy.interpolate import CubicSpline

from .calculations import transfer_properties, calculate_vertices_sums
from .models import Vertex, GeometrySums, AreaInertia, TOLERANCE
from .centroid import Centroid


class OperationType(str, Enum):
    """Типи булевих операцій, що зберігаються у вузлах CSG-дерева."""
    UNION = "UNION"  # Об'єднання (+)
    DIFFERENCE = "DIFFERENCE"  # Віднімання (-)
    INTERSECTION = "INTERSECTION"  # Перетин (*)
    PRIMITIVE = "PRIMITIVE"  # Для листових вузлів (Rectangle, Circle, Polygon, BSpline)


# =========================================================================
# АБСТРАКТНИЙ БАЗОВИЙ КЛАС
# =========================================================================

class GeometryObject(BaseModel, ABC):
    """
    Базовий інтерфейс для всіх геометричних об'єктів.
    Кожен об'єкт є вузлом у CSG-дереві.
    """
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    # --- АБСТРАКТНІ ВЛАСТИВОСТІ ---

    @computed_field
    @property
    @abstractmethod
    def centroid(self) -> Centroid:
        """[ABSTRACT] Фінальні центроїдальні властивості I_c (відносно центру мас)."""
        pass

    @computed_field
    @property
    @abstractmethod
    def sums(self) -> GeometrySums:
        """[ABSTRACT] Фінальні агреговані суми I_0 (відносно Глобального Початку 0,0)."""
        pass

    @abstractmethod
    def translate(self, dx: float, dy: float) -> "GeometryObject":
        """[ABSTRACT] Транслює об'єкт, створюючи новий екземпляр."""
        pass

    @computed_field
    @property
    @abstractmethod
    def shapely_geometry(self) -> BaseGeometry:
        """[ABSTRACT] Повертає об'єкт Shapely для топологічних операцій."""
        pass

    # --- CSG: Об'єднання (+), Віднімання (-), Перетин (*) ---
    # Створюють новий Compound-вузол (батьківський вузол у дереві)

    def __add__(self, other: "GeometryObject") -> "Compound":
        """Оператор (+): Об'єднання (Union)."""
        if not isinstance(other, GeometryObject):
            return NotImplemented
        return Compound(op_type=OperationType.UNION, left=self, right=other)

    def __sub__(self, other: "GeometryObject") -> "Compound":
        """Оператор (-): Віднімання (Difference)."""
        if not isinstance(other, GeometryObject):
            return NotImplemented
        return Compound(op_type=OperationType.DIFFERENCE, left=self, right=other)

    def __mul__(self, other: "GeometryObject") -> "Compound":
        """Оператор (*): Перетин (Intersection)."""
        if not isinstance(other, GeometryObject):
            return NotImplemented
        return Compound(op_type=OperationType.INTERSECTION, left=self, right=other)

    # --- Допоміжні властивості ---

    @computed_field
    @property
    def area(self) -> float:
        """Повертає фінальну площу фігури."""
        return self.centroid.area

    @computed_field
    @property
    @abstractmethod
    def vertices(self) -> np.ndarray:
        """[ABSTRACT] Повертає фінальні (зміщені) координати вершин."""
        pass

    @computed_field
    @property
    def cx(self) -> float:
        """X-координата фінального центроїда (Sy_0 / A)."""
        sums = self.sums
        area = sums.area
        return sums.Sy_0 / area if abs(area) > TOLERANCE else 0.0

    @computed_field
    @property
    def cy(self) -> float:
        """Y-координата фінального центроїда (Sx_0 / A)."""
        sums = self.sums
        area = sums.area
        return sums.Sx_0 / area if abs(area) > TOLERANCE else 0.0


# =========================================================================
# АНАЛІТИЧНІ ПРИМІТИВИ (ЛИСТОВІ ВУЗЛИ CSG)
# =========================================================================

class Rectangle(GeometryObject):
    """Прямокутник. Аналітичний розрахунок I_c -> I_0 (Прямий трансфер Штейнера)."""
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
            area=A, center=Vertex(x=self.x, y=self.y),
            inertia=AreaInertia(Ix=I_x_own, Iy=I_y_own, Ixy=0.0)
        )

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """Прямий трансфер Штейнера."""
        data = self.centroid
        return transfer_properties(data=data, dx=data.center.x, dy=data.center.y, reverted=False)

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

    def translate(self, dx: float, dy: float) -> 'Rectangle':
        return self.__class__(x=self.x + dx, y=self.y + dy, width=self.width, height=self.height)


class Circle(GeometryObject):
    """Коло. Аналітичний розрахунок I_c -> I_0."""
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
            area=A, center=Vertex(x=self.x, y=self.y),
            inertia=AreaInertia(Ix=I_c, Iy=I_c, Ixy=0.0)
        )

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """Прямий трансфер Штейнера."""
        data = self.centroid
        return transfer_properties(data=data, dx=data.center.x, dy=data.center.y, reverted=False)

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

    def translate(self, dx: float, dy: float) -> 'Circle':
        return self.__class__(x=self.x + dx, y=self.y + dy, radius=self.radius, segments=self.segments)


# =========================================================================
# ЧИСЕЛЬНІ ПРИМІТИВИ (ЛИСТОВІ ВУЗЛИ CSG)
# =========================================================================

class Polygon(GeometryObject):
    """Багатокутник. Чисельний розрахунок I_0 -> I_c (Зворотний трансфер Штейнера)."""
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
        """I_c: Зворотний трансфер Штейнера."""
        sums_0 = self.sums
        area = sums_0.area
        cx = sums_0.Sy_0 / area if abs(area) > TOLERANCE else 0.0
        cy = sums_0.Sx_0 / area if abs(area) > TOLERANCE else 0.0

        temp_centroid_with_I0 = Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=sums_0.inertia)
        # Зворотний трансфер I_0 -> I_c
        centroidal_sums = transfer_properties(data=temp_centroid_with_I0, dx=cx, dy=cy, reverted=True)

        return Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=centroidal_sums.inertia)

    def translate(self, dx: float, dy: float) -> "Polygon":
        new_vertices = [Vertex(x=v.x + dx, y=v.y + dy) for v in self.vertices_list]
        return self.__class__(vertices_list=new_vertices)


class CircularArc(GeometryObject):
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
        coords = np.vstack([coords, [self.x, self.y]])
        return coords

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        return sg.Polygon(self.vertices)

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        return calculate_vertices_sums(self.vertices)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """I_c: Зворотний трансфер Штейнера."""
        sums_0 = self.sums
        area = sums_0.area
        cx = sums_0.Sy_0 / area if abs(area) > TOLERANCE else 0.0
        cy = sums_0.Sx_0 / area if abs(area) > TOLERANCE else 0.0

        temp_centroid_with_I0 = Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=sums_0.inertia)
        centroidal_sums = transfer_properties(data=temp_centroid_with_I0, dx=cx, dy=cy, reverted=True)

        return Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=centroidal_sums.inertia)

    def translate(self, dx: float, dy: float) -> 'CircularArc':
        return self.__class__(
            x=self.x + dx, y=self.y + dy, radius=self.radius,
            start_angle=self.start_angle, end_angle=self.end_angle,
            segments=self.segments
        )


class BSpline(GeometryObject):
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

        # Визначення параметричного шляху t (кумулятивна довжина)
        dx = np.diff(coords[:, 0])
        dy = np.diff(coords[:, 1])
        distances = np.sqrt(dx ** 2 + dy ** 2)
        t = np.insert(np.cumsum(distances), 0, 0)

        # Перевірка на замкненість (для bc_type='periodic')
        is_closed = np.allclose(coords[0], coords[-1], atol=TOLERANCE)
        bc_type = 'periodic' if is_closed else 'natural'

        # Побудова кубічного сплайна
        cs_x = CubicSpline(t, coords[:, 0], bc_type=bc_type)
        cs_y = CubicSpline(t, coords[:, 1], bc_type=bc_type)

        # Генерування фінальних точок
        t_new = np.linspace(t[0], t[-1], self.num_points)
        x_new = cs_x(t_new)
        y_new = cs_y(t_new)

        return np.stack([x_new, y_new], axis=1)

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        """Створення Shapely Polygon з апроксимованих вершин сплайна."""
        if self.vertices.size > 0:
            # Shapely автоматично закриває контур, якщо він не замкнений
            return sg.Polygon(self.vertices)
        return sg.Polygon()

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """I_0: Обчислення через Гаусса-Гріна (чисельно)."""
        return calculate_vertices_sums(self.vertices)

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """I_c: Зворотний трансфер Штейнера."""
        sums_0 = self.sums
        area = sums_0.area
        cx = sums_0.Sy_0 / area if abs(area) > TOLERANCE else 0.0
        cy = sums_0.Sx_0 / area if abs(area) > TOLERANCE else 0.0

        temp_centroid_with_I0 = Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=sums_0.inertia)
        centroidal_sums = transfer_properties(data=temp_centroid_with_I0, dx=cx, dy=cy, reverted=True)

        return Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=centroidal_sums.inertia)

    def translate(self, dx: float, dy: float) -> "BSpline":
        """Трансляція всіх контрольних вершин."""
        new_vertices = [Vertex(x=v.x + dx, y=v.y + dy) for v in self.vertices_list]
        return self.__class__(vertices_list=new_vertices, num_points=self.num_points)


# =========================================================================
# CSG-ВУЗОЛ (Compound)
# =========================================================================

class Compound(GeometryObject):
    """
    Вузол CSG-дерева. Бінарний вузол, що зберігає операцію та два операнди (left, right).
    """
    op_type: OperationType = Field(OperationType.UNION, frozen=True)
    left: GeometryObject  # Лівий операнд (піддерево або примітив)
    right: GeometryObject  # Правий операнд

    @computed_field
    @property
    def shapely_geometry(self) -> BaseGeometry:
        """Рекурсивно обчислює фінальну геометрію, слідуючи op_type."""

        # Рекурсивно отримуємо геометрію операндів
        geom_left = self.left.shapely_geometry
        geom_right = self.right.shapely_geometry

        # Виконання булевої операції
        if self.op_type == OperationType.UNION:
            return geom_left.union(geom_right)
        elif self.op_type == OperationType.DIFFERENCE:
            return geom_left.difference(geom_right)
        elif self.op_type == OperationType.INTERSECTION:
            return geom_left.intersection(geom_right)

        # Цей випадок не повинен відбутися, якщо дерево побудовано коректно
        return geom_left

    @computed_field
    @property
    def sums(self) -> GeometrySums:
        """
        I_0: Розрахунок через Shapely-топологію + Гаусса-Гріна.
        Обчислюється лише для фінального результату топологічної операції.
        """
        final_geometry = self.shapely_geometry
        total_sums = GeometrySums()

        polygons: List[sg.Polygon] = []
        if isinstance(final_geometry, sg.MultiPolygon):
            polygons.extend(list(final_geometry.geoms))
        elif isinstance(final_geometry, sg.Polygon):
            polygons.append(final_geometry)
        else:
            return GeometrySums()

        # Обхід кожного контуру для формули Гаусса-Гріна
        for poly in polygons:
            total_sums += calculate_vertices_sums(np.array(poly.exterior.coords))
            for interior in poly.interiors:
                total_sums += calculate_vertices_sums(np.array(interior.coords))

        return total_sums

    @computed_field
    @property
    def centroid(self) -> Centroid:
        """I_c: Обчислення через Зворотний Хід Штейнера (I_0 -> I_c)."""
        sums_0 = self.sums
        area = sums_0.area
        cx = sums_0.Sy_0 / area if abs(area) > TOLERANCE else 0.0
        cy = sums_0.Sx_0 / area if abs(area) > TOLERANCE else 0.0

        temp_centroid_with_I0 = Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=sums_0.inertia)
        centroidal_sums = transfer_properties(data=temp_centroid_with_I0, dx=cx, dy=cy, reverted=True)

        return Centroid(area=area, center=Vertex(x=cx, y=cy), inertia=centroidal_sums.inertia)

    def translate(self, dx: float, dy: float) -> 'Compound':
        """Транслює обидва дочірні вузли, зберігаючи структуру CSG-дерева."""
        new_left = self.left.translate(dx, dy)
        new_right = self.right.translate(dx, dy)
        return self.__class__(op_type=self.op_type, left=new_left, right=new_right)

    @computed_field
    @property
    def vertices(self) -> np.ndarray:
        """Повертає вершини зовнішнього контуру фінальної геометрії."""
        final_geom = self.shapely_geometry
        if isinstance(final_geom, sg.Polygon):
            return np.array(final_geom.exterior.coords)
        return np.array([])
