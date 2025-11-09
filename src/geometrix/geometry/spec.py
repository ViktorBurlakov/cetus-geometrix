from pydantic import BaseModel
from typing import Callable

from geometrix.geometry.gobject import GeometryObject


class GeometrySpec(BaseModel):
    """
    Abstract base for all parametric geometry models.
    Contains a universal factory method.
    """
    class Config:
        default_factory_func = None

    def get_factory_params(self) -> dict:
        """Returns a dictionary of parameters required to call the constructor function."""
        # All model fields are passed as arguments
        return self.model_dump()

    def create_geometry(self, factory_func: Callable | None = None) -> GeometryObject:
        """
        Factory method: Creates a Compound object by calling an external constructor function.

        :param factory_func: One of the functions from geometry/sections.py (e.g., create_i_beam).
        :return: A GeometryObject created by the constructor.
        """
        factory_func = factory_func or self.Config.default_factory_func
        params = self.get_factory_params()
        return factory_func(**params)
