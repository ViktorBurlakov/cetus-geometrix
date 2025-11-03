from pydantic import BaseModel, Field
from typing import Callable

from engine.geometry.core import GeometryObject
from engine.geometry.sections import create_i_beam, create_c_channel, create_l_section, create_box_section


class GeometryModel(BaseModel):
    """
    Абстрактна база для всіх моделей параметричної геометрії.
    Містить універсальний метод-фабрику.
    """
    class Config:
        factory_func = None

    def get_factory_params(self) -> dict:
        """Повертає словник параметрів, необхідних для виклику функції-конструктора."""
        # Усі поля моделі передаються як аргументи
        return self.model_dump()

    def create_geometry(self, factory_func: Callable | None = None) -> GeometryObject:
        """
        Метод-фабрика: Створює об'єкт Compound, викликаючи зовнішню функцію-конструктор.

        :param factory_func: Одна з функцій з geometry/sections.py (наприклад, create_i_beam).
        :return: Об'єкт GeometryObject, створений конструктором.
        """
        factory_func = factory_func or self.Config.factory_func
        params = self.get_factory_params()
        return factory_func(**params)


class IBeamModel(GeometryModel):
    """Параметри Двотавра. Відповідає create_i_beam(H, B, t_f, t_w, R)."""
    H: float = Field(description="Загальна висота (H) [м]")
    B: float = Field(description="Ширина полиці (B) [м]")
    t_f: float = Field(description="Товщина полиці (t_f) [м]")
    t_w: float = Field(description="Товщина стінки (t_w) [м]")
    R: float = Field(0.0, description="Радіус заокруглення (R) [м]")

    class Config:
        factory_func = create_i_beam


class CChannelModel(GeometryModel):
    """Параметри Швелера. Відповідає create_c_channel(H, B, t_w, t_f)."""
    H: float = Field(description="Загальна висота (H) [м]")
    B: float = Field(description="Ширина полиці (B) [м]")
    t_w: float = Field(description="Товщина стінки (t_w) [м]")
    t_f: float = Field(description="Товщина полиці (t_f) [м]")

    class Config:
        factory_func = create_c_channel


class LSectionModel(GeometryModel):
    """Параметри Кутика. Відповідає create_l_section(B, H, t)."""
    B: float = Field(description="Ширина полиці 1 (B) [м]")
    H: float = Field(description="Ширина полиці 2 (H) [м]")
    t: float = Field(description="Рівномірна товщина (t) [м]")

    class Config:
        factory_func = create_l_section


class RHSModel(GeometryModel):
    """Параметри Box Section. Відповідає create_box_section(B, H, t)."""
    B: float = Field(description="Зовнішня ширина (B) [м]")
    H: float = Field(description="Зовнішня висота (H) [м]")
    t: float = Field(description="Рівномірна товщина стінки (t) [м]")

    class Config:
        factory_func = create_box_section
