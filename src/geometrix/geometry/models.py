from enum import Enum

import numpy as np
from pydantic import BaseModel, Field, computed_field


class TOLERANCE:
    """Глобальна точність для порівнянь з плаваючою комою."""
    AREA_CALC = 1e-9  # Для перевірки поділу на нуль при обчисленні ЦМ
    GEOMETRY = 1e-6   # Загальна точність для геометричних порівнянь


class OperationType(str, Enum):
    """Типи булевих операцій, що зберігаються у вузлах CSG-дерева."""
    UNION = "UNION"  # Об'єднання (+)
    DIFFERENCE = "DIFFERENCE"  # Віднімання (-)
    INTERSECTION = "INTERSECTION"  # Перетин (*)
    PRIMITIVE = "PRIMITIVE"  # Для листових вузлів (Rectangle, Circle, Polygon, BSpline)
    COMPOUND = "COMPOUND"  # Для вузлів CSG-дерева, що представляють комбінацію


class Vertex(BaseModel):
    """Універсальна 3D/2D координата."""
    x: float = Field(0.0, description="X-координата (м).")
    y: float = Field(0.0, description="Y-координата (м).")
    z: float = Field(0.0, description="Z-координата (м). Для 2D: 0.0.")

    class Config:
        frozen = True


class BoundingBox(BaseModel):
    """Універсальна модель обмежувальної коробки (Bounding Box) для 2D/3D."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float = Field(0.0)
    max_z: float = Field(0.0)

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

    @computed_field
    @property
    def depth(self):
        """Для 3D: глибина (по осі Z). Для 2D: 0.0."""
        return self.max_z - self.min_z


class StaticMoments(BaseModel):
    """
    Універсальні Статичні Моменти (Sx, Sy, Sz).
    2D: Моменти Площі; 3D: Моменти Об'єму/Маси.
    """
    Sx: float = Field(0.0)  # Статичний момент відносно осі X (Sx_0)
    Sy: float = Field(0.0)  # Статичний момент відносно осі Y (Sy_0)
    Sz: float = Field(0.0)  # Статичний момент відносно осі Z (Sz_0). Для 2D: 0.0.

    class Config:
        frozen = True

    def __add__(self, other: 'StaticMoments') -> 'StaticMoments':
        """Реалізує оператор додавання для агрегування."""
        if not isinstance(other, StaticMoments):
            return NotImplemented
        return StaticMoments(
            Sx=self.Sx + other.Sx,
            Sy=self.Sy + other.Sy,
            Sz=self.Sz + other.Sz
        )

    def __sub__(self, other: 'StaticMoments') -> 'StaticMoments':
        """Реалізує оператор віднімання (для отворів/вирізів)."""
        if not isinstance(other, StaticMoments):
            return NotImplemented
        return StaticMoments(
            Sx=self.Sx - other.Sx,
            Sy=self.Sy - other.Sy,
            Sz=self.Sz - other.Sz
        )


class InertiaTensor(BaseModel):
    """
    Універсальний Тензор Інерції (2D: Площа, 3D: Маса/Об'єм).
    Використовує 6 незалежних компонент (симетрична 3x3 матриця).
    """
    # Моменти інерції (діагональні)
    Ixx: float = Field(0.0, description="Момент відносно осі X. У 2D: Ix.")
    Iyy: float = Field(0.0, description="Момент відносно осі Y. У 2D: Iy.")
    Izz: float = Field(0.0, description="Момент відносно осі Z (Полярний момент). У 2D: 0.0.")

    # Добутки інерції (недіагональні)
    Ixy: float = Field(0.0, description="Добуток інерції Ixy. У 2D: Ixy.")
    Ixz: float = Field(0.0, description="Добуток інерції Ixz. У 2D: 0.0.")
    Iyz: float = Field(0.0, description="Добуток інерції Iyz. У 2D: 0.0.")

    J_torsion: float | None = Field(None, description="Константа кручення (J). Використовується для GJ_torsion.")

    class Config:
        frozen = True

    def ndarray(self, dim: int = 3) -> np.ndarray:
        """Повертає компоненти тензора як матрицю NumPy 2x2 або 3x3."""
        if dim == 2:
            # 2D випадок (площа)
            return np.array([
                [self.Ixx, -self.Ixy],
                [-self.Ixy, self.Iyy]
            ], dtype=np.float64)
        else:
            # 3D випадок (маса/об'єм)
            return np.array([
                [self.Ixx, -self.Ixy, -self.Ixz],
                [-self.Ixy, self.Iyy, -self.Iyz],
                [-self.Ixz, -self.Iyz, self.Izz]
            ], dtype=np.float64)

    @computed_field
    @property
    def I_polar(self) -> float:
        """
        Полярний момент інерції (J_polar) [м^4].
        Дорівнює сумі моментів у площині XY.
        """
        return self.Ixx + self.Iyy

    def __add__(self, other: 'InertiaTensor') -> 'InertiaTensor':
        """Додає два тензори (для агрегування)."""
        if not isinstance(other, InertiaTensor):
            raise TypeError("Можна додавати лише InertiaTensor.")
        return InertiaTensor(
            Ixx=self.Ixx + other.Ixx, Iyy=self.Iyy + other.Iyy, Izz=self.Izz + other.Izz,
            Ixy=self.Ixy + other.Ixy, Ixz=self.Ixz + other.Ixz, Iyz=self.Iyz + other.Iyz,
            J_torsion=self.J_torsion + other.J_torsion  # Додаємо J_torsion
        )

    def __sub__(self, other: 'InertiaTensor') -> 'InertiaTensor':
        """Віднімає два тензори (для отворів/вирізів)."""
        if not isinstance(other, InertiaTensor):
            raise TypeError("Можна віднімати лише InertiaTensor.")
        return InertiaTensor(
            Ixx=self.Ixx - other.Ixx, Iyy=self.Iyy - other.Iyy, Izz=self.Izz - other.Izz,
            Ixy=self.Ixy - other.Ixy, Ixz=self.Ixz - other.Ixz, Iyz=self.Iyz - other.Iyz,
            J_torsion=self.J_torsion - other.J_torsion  # Віднімаємо J_torsion
        )


class GeometrySums(BaseModel):
    """
    Універсальна Модель для сирих геометричних сум I_0 відносно глобального початку (0,0).
    Включає площу перерізу, об'єм та площу поверхні.
    """
    plane_area: float = Field(0.0, description="Площа перерізу (2D), інакше 0.0.")
    volume: float = Field(0.0, description="Об'єм тіла (3D), інакше 0.0.")
    surface_area: float = Field(0.0, description="Площа поверхні тіла (3D), інакше 0.0.")

    static_moments: StaticMoments
    inertia: InertiaTensor

    class Config:
        frozen = True

    @computed_field
    @property
    def primary_measure(self) -> float:
        """Повертає основну ненульову міру (Площа перерізу або Об'єм)."""
        return self.plane_area if self.plane_area > TOLERANCE else self.volume

    def __add__(self, other: 'GeometrySums') -> 'GeometrySums':
        """Реалізує оператор додавання для агрегування (об'єднання)."""
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
        """Реалізує оператор віднімання (для отворів/вирізів)."""
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
    Модель для головних моментів інерції та кута повороту (зазвичай 2D).
    """
    I1: float = Field(0.0)  # Головний момент інерції (максимальний)
    I2: float = Field(0.0)  # Головний момент інерції (мінімальний)
    alpha: float = Field(0.0)  # Кут повороту (в радіанах) від осі X до осі I1

    class Config:
        frozen = True


class RadiiOfGyration(BaseModel):
    """
    Модель для радіусів інерції перерізу (зазвичай 2D).
    """
    rx: float = Field(0.0)  # Радіус інерції відносно центроїдальної осі X
    ry: float = Field(0.0)  # Радіус інерції відносно центроїдальної осі Y
    r1: float = Field(0.0)  # Радіус інерції відносно головної осі 1 (максимальний)
    r2: float = Field(0.0)  # Радіус інерції відносно головної осі 2 (мінімальний)

    class Config:
        frozen = True
