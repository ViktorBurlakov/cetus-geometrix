from typing import NamedTuple

import numpy as np
from pydantic import BaseModel, computed_field, Field


class Vertex(BaseModel):
    x: float
    y: float
    z: float = 0.0


class BoundingBox(BaseModel):
    """Модель обмежувального прямокутника (Bounding Box)."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    class Config:
        frozen = True

    @computed_field
    @property
    def width(self):
        return self.max_x - self.min_x

    @computed_field
    @property
    def height(self):
        return self.max_y - self.min_y



class AreaInertia(BaseModel):
    """
    Тензор інерції площі (компоненти 2x2 матриці)
    для Ix, Iy та Ixy відносно заданої системи координат.
    """
    Ix: float = Field(0.0)    # Момент інерції відносно осі X
    Iy: float = Field(0.0)    # Момент інерції відносно осі Y
    Ixy: float = Field(0.0)   # Добуток інерції (центробіжний момент)

    class Config:
        frozen = True # Забезпечує незмінність, якщо потрібно

    def ndarray(self) -> np.ndarray:
        """Повертає компоненти тензора як матрицю NumPy 2x2."""
        return np.array([
            [self.Ix, -self.Ixy],
            [-self.Ixy, self.Iy]
        ], dtype=np.float64)

    def __add__(self, other: 'AreaInertia') -> 'AreaInertia':
        """Додає два тензори (для агрегування)."""
        if not isinstance(other, AreaInertia):
            raise TypeError("Можна додавати лише інші AreaInertiaTensor.")
        return AreaInertia(
            Ix=self.Ix + other.Ix,
            Iy=self.Iy + other.Iy,
            Ixy=self.Ixy + other.Ixy
        )


class Centroid(NamedTuple):
    """Структура для зберігання властивостей фігури відносно її Центроїда (ЦП)."""
    area: float
    center: Vertex
    inertia: AreaInertia



class StaticMoments(BaseModel):
    Sx: float = Field(0.0)  # Статичний момент відносно осі X (Sx_0)
    Sy: float = Field(0.0)  # Статичний момент відносно осі Y (Sy_0)

    def __add__(self, other: 'StaticMoments') -> 'StaticMoments':
        """Реалізує оператор додавання для агрегування (об'єднання)."""
        if not isinstance(other, StaticMoments):
            return NotImplemented
        return StaticMoments(
            Sx=self.Sx + other.Sx,
            Sy=self.Sy + other.Sy
        )

    def __sub__(self, other: 'StaticMoments') -> 'StaticMoments':
        """Реалізує оператор віднімання (для отворів/вирізів)."""
        if not isinstance(other, StaticMoments):
            return NotImplemented

        return StaticMoments(
            Sx=self.Sx - other.Sx,
            Sy=self.Sy - other.Sy
        )


class GeometrySums(BaseModel):
    """
    Модель для виводу сирих геометричних сум відносно глобального початку (0,0).
    """
    # Загальна площа (A)
    area: float = Field(0.0)
    # Статичний момент відносно осі X (Sx_0)
    static_moments: StaticMoments
    # Тензор інерції відносно (0, 0)
    inertia: AreaInertia

    class Config:
        frozen = True

    def __add__(self, other: 'GeometrySums') -> 'GeometrySums':
        """Реалізує оператор додавання для агрегування (об'єднання)."""
        if not isinstance(other, GeometrySums):
            return NotImplemented
        return GeometrySums(
            area=self.area + other.area,
            static_moments=self.static_moments + other.static_moments,
            inertia=self.inertia + other.inertia  # Викликає AreaInertia.__add__
        )

    def __sub__(self, other: 'GeometrySums') -> 'GeometrySums':
        """Реалізує оператор віднімання (для отворів/вирізів)."""
        if not isinstance(other, GeometrySums):
            return NotImplemented

        subtracted_tensor = AreaInertia(
            Ix=self.inertia.Ix - other.inertia.Ix,
            Iy=self.inertia.Iy - other.inertia.Iy,
            Ixy=self.inertia.Ixy - other.inertia.Ixy,
        )

        return GeometrySums(
            area=self.area - other.area,
            static_moments=self.static_moments - other.static_moments,
            inertia=subtracted_tensor
        )


class PrincipalInertia(BaseModel):
    """
    Модель для головних моментів інерції та кута повороту.
    """
    I1: float = Field(0.0)      # Головний момент інерції (максимальний)
    I2: float = Field(0.0)      # Головний момент інерції (мінімальний)
    alpha: float = Field(0.0)   # Кут повороту (в радіанах) від осі X до осі I1

    class Config:
        frozen = True


class RadiiOfGyration(BaseModel):
    """
    Модель для радіусів інерції перерізу.
    """
    rx: float = Field(0.0)    # Радіус інерції відносно центроїдальної осі X
    ry: float = Field(0.0)    # Радіус інерції відносно центроїдальної осі Y
    r1: float = Field(0.0)    # Радіус інерції відносно головної осі 1 (максимальний)
    r2: float = Field(0.0)    # Радіус інерції відносно головної осі 2 (мінімальний)

    class Config:
        frozen = True
