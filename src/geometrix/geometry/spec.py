from pydantic import BaseModel
from typing import Callable

from geometrix.geometry import GeometryObject


class GeometrySpec(BaseModel):
    """
    Абстрактна база для всіх моделей параметричної геометрії.
    Містить універсальний метод-фабрику.
    """
    class Config:
        default_factory_func = None

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
        factory_func = factory_func or self.Config.default_factory_func
        params = self.get_factory_params()
        return factory_func(**params)
