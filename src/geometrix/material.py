from pydantic import Field, BaseModel


class Material(BaseModel):
    """Модель інженерного матеріалу."""
    name: str
    # Щільність (маса на одиницю об'єму), наприклад, кг/м³ або т/мм³
    density: float = Field(description="Density (e.g., kg/mm^3)")
    # Модуль Юнга (Модуль пружності)
    E: float = Field(description="Young's Modulus (MPa)")
    # Коефіцієнт Пуассона
    nu: float = Field(description="Poisson's ratio")

    class Config:
        frozen = True