from pydantic import Field, BaseModel, computed_field


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

    @computed_field
    @property
    def shear_modulus(self) -> float:
        """
        Обчислює **модуль зсуву** (G) за законом Гука для ізотропних матеріалів.
        Формула: G = E / (2 * (1 + nu)).
        """
        return self.E / (2.0 * (1.0 + self.nu))
