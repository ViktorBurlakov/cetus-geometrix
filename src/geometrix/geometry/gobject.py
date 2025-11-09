from abc import ABC, abstractmethod
from typing import TypeVar, Generic

import numpy as np
from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.centroid import Centroid
from geometrix.geometry.models import TOLERANCE, GeometrySums, OperationType

T = TypeVar('T', bound='GeometryObject')


class GeometryObject(BaseModel, ABC, Generic[T]):
    """
    Абстрактний базовий інтерфейс для всіх геометричних об'єктів (2D та 3D).
    Кожен об'єкт є вузлом у CSG-дереві (хоча для 3D CSG може бути окрема ієрархія).
    """
    op_type: OperationType = Field(OperationType.PRIMITIVE, frozen=True)

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    @computed_field
    @property
    @abstractmethod
    def sums(self) -> GeometrySums:
        """
        [ABSTRACT] Повертає агреговані геометричні суми (площа/об'єм,
        статичні моменти, моменти інерції) об'єкта відносно ГЛОБАЛЬНОГО початку координат (0,0,0).
        """
        pass

    @computed_field
    @property
    @abstractmethod
    def centroid(self) -> Centroid:
        """
        [ABSTRACT] Повертає об'єкт Centroid, що містить центр мас/центроїд
        та моменти інерції ВІДНОСНО цього центру.
        """
        pass

    @computed_field
    @property
    @abstractmethod
    def vertices(self) -> np.ndarray: # np.ndarray для гнучкості (2D [N,2] або 3D [N,3])
        """
        [ABSTRACT] Повертає список вершин, що визначають зовнішній контур
        (або апроксимацію) об'єкта.
        """
        pass

    @computed_field
    @property
    @abstractmethod
    def plane_area(self) -> float:
        """
        [ABSTRACT] Повертає площу 2D перерізу об'єкта. Для 3D тіл це 0.0,
        якщо тіло не є плоским об'єктом.
        """
        pass

    @computed_field
    @property
    @abstractmethod
    def volume(self) -> float:
        """
        [ABSTRACT] Повертає об'єм 3D об'єкта. Для 2D перерізів це 0.0.
        """
        pass

    @computed_field
    @property
    @abstractmethod
    def surface_area(self) -> float:
        """
        [ABSTRACT] Повертає площу поверхні 3D об'єкта. Для 2D перерізів це 0.0.
        """
        pass

    @computed_field
    @property
    def primary_measure(self) -> float:
        """
        Повертає основну міру об'єкта (площу для 2D, об'єм для 3D).
        Залежить від конкретної реалізації.
        """
        # ✅ Використання TOLERANCE для безпечного порівняння з нулем
        if self.volume > TOLERANCE.AREA_CALC:
            return self.volume
        return self.plane_area

    @abstractmethod
    def translate(self: T, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> T:
        """
        [ABSTRACT] Переміщує геометричний об'єкт на задані відхилення.
        Повертає новий об'єкт (immutable).
        """
        pass

    # Булеві оператори, які можуть бути перевизначені в похідних класах (наприклад, GeometryObject2D)
    def __add__(self: T, other: 'GeometryObject') -> 'GeometryObject':
        return NotImplemented

    def __sub__(self: T, other: 'GeometryObject') -> 'GeometryObject':
        return NotImplemented

    def __mul__(self: T, other: 'GeometryObject') -> 'GeometryObject':
        return NotImplemented

    @computed_field
    @property
    def cx(self) -> float:
        """X-координата фінального центроїда (Sy_0 / Primary_Measure)."""
        sums = self.sums
        measure = self.primary_measure
        return sums.static_moments.Sy / measure if abs(measure) > TOLERANCE.AREA_CALC else 0.0

    @computed_field
    @property
    def cy(self) -> float:
        """Y-координата фінального центроїда (Sx_0 / Primary_Measure)."""
        sums = self.sums
        measure = self.primary_measure
        return sums.static_moments.Sx / measure if abs(measure) > TOLERANCE.AREA_CALC else 0.0

    @computed_field
    @property
    def cz(self) -> float:
        """Z-координата фінального центроїда (Sz_0 / Primary_Measure)."""
        sums = self.sums
        measure = self.primary_measure
        return sums.static_moments.Sz / measure if abs(measure) > TOLERANCE.AREA_CALC else 0.0
