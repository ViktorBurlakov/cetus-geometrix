from abc import ABC, abstractmethod

from pydantic import BaseModel, Field
import shapely.geometry as sg
from shapely.geometry.base import BaseGeometry
import numpy as np

from geometrix.geometry.gobject import Centroid
from geometrix.geometry.models import GeometrySums, Vertex, TOLERANCE, OperationType
from geometrix.geometry.calculations import transfer_properties, calculate_vertices_sums


class CSGOperation(BaseModel, ABC):
    """
    Абстрактна база для всіх булевих операцій у CSG-дереві.
    Визначає, як виконувати Shapely-операції та як обчислювати геометричні властивості
    фінального об'єкта.
    """
    op_type: OperationType = Field(..., frozen=True)

    @abstractmethod
    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        """Виконує булеву операцію над двома Shapely-об'єктами."""
        pass

    @abstractmethod
    def calculate_sums(
        self,
        left_obj: 'GeometryObject2D',
        right_obj: 'GeometryObject2D',
        final_shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        """
        Обчислює геометричні суми фінального об'єкта.
        Логіка залежить від типу операції та може використовувати `final_shapely_geometry`.
        """
        pass

    def calculate_centroid(
        self,
        left_obj: 'GeometryObject2D',
        right_obj: 'GeometryObject2D',
        shapely_geometry: BaseGeometry
    ) -> Centroid:
        """
        Обчислює центроїд фінального об'єкта.
        Цей метод використовує `calculate_sums` для отримання об'єднаних сум, а потім
        перераховує центроїд.
        """
        # Спочатку отримуємо суми, використовуючи метод операції
        total_sums = self.calculate_sums(left_obj, right_obj, shapely_geometry)

        # Якщо площа нульова, повертаємо порожній центроїд
        if abs(total_sums.plane_area) < TOLERANCE.AREA_CALC: # Використовуємо TOLERANCE
            return Centroid()

        # Визначаємо новий глобальний центр мас
        cx_new = total_sums.static_moments.Sy / total_sums.plane_area
        cy_new = total_sums.static_moments.Sx / total_sums.plane_area

        # Переносимо моменти інерції до нового глобального центру мас (зворотний хід Штейнера)
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
    op_type: OperationType = Field(OperationType.UNION, literal=True)

    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        return left_geom.union(right_geom)

    def calculate_sums(
        self,
        left_obj: 'GeometryObject2D',
        right_obj: 'GeometryObject2D',
        final_shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        # Для об'єднання суми просто додаються
        return left_obj.sums + right_obj.sums


class DifferenceOperation(CSGOperation):
    op_type: OperationType = Field(OperationType.DIFFERENCE, literal=True)

    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        return left_geom.difference(right_geom)

    def calculate_sums(
        self,
        left_obj: 'GeometryObject2D',
        right_obj: 'GeometryObject2D',
        final_shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        # Для віднімання суми віднімаються
        return left_obj.sums - right_obj.sums


class IntersectionOperation(CSGOperation):
    op_type: OperationType = Field(OperationType.INTERSECTION, literal=True)

    def execute_shapely(self, left_geom: BaseGeometry, right_geom: BaseGeometry) -> BaseGeometry:
        return left_geom.intersection(right_geom)

    def calculate_sums(
        self,
        left_obj: 'GeometryObject2D',
        right_obj: 'GeometryObject2D',
        final_shapely_geometry: BaseGeometry
    ) -> GeometrySums:
        # Для перетину: ми ПОВИННІ обчислити суми з фінальної shapely_geometry.
        total_sums = GeometrySums()

        polygons: list[sg.Polygon] = []
        if isinstance(final_shapely_geometry, sg.MultiPolygon):
            polygons.extend(list(final_shapely_geometry.geoms))
        elif isinstance(final_shapely_geometry, sg.Polygon):
            polygons.append(final_shapely_geometry)
        else:
            return total_sums

        for poly in polygons:
            total_sums += calculate_vertices_sums(np.array(poly.exterior.coords))
            for interior in poly.interiors:
                interior_coords = np.array(interior.coords)
                total_sums += calculate_vertices_sums(interior_coords[::-1])

        return total_sums

# Фабрична функція для зручного створення об'єктів операцій
def create_operation(op_type: OperationType) -> CSGOperation:
    if op_type == OperationType.UNION:
        return UnionOperation(op_type=op_type)
    elif op_type == OperationType.DIFFERENCE:
        return DifferenceOperation(op_type=op_type)
    elif op_type == OperationType.INTERSECTION:
        return IntersectionOperation(op_type=op_type)
    else:
        raise ValueError(f"Unknown operation type: {op_type}")
