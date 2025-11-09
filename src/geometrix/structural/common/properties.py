import numpy as np
from pydantic import BaseModel, Field, computed_field


class ShearAreas(BaseModel):
    """
    Інкапсулює ефективні площі зсуву (A_shear) перерізу
    вздовж основних осей. Ці площі використовуються для
    врахування деформацій зсуву.
    """
    shear_area_y: float = Field(
        0.0,
        description="Ефективна площа зсуву для Y напрямку ($A_{shear,y}$) [м^2]."
    )
    shear_area_x: float = Field(
        0.0,
        description="Ефективна площа зсуву для X напрямку ($A_{shear,x}$) [м^2]."
    )
    shear_area_z: float = Field(
        0.0,
        description="Ефективна площа зсуву для Z напрямку ($A_{shear,z}$) [м^2]."
    )

    class Config:
        frozen = True


class StiffnessProperties(BaseModel):
    """
    Інкапсулює всі стандартні жорсткісні характеристики елемента.
    Це DTO, що містить вже обчислені значення.
    """
    # Жорсткості на згин
    EI_xx: float = Field(0.0, description="Згинальна жорсткість [Н*м^2] відносно осі X.")
    EI_yy: float = Field(0.0, description="Згинальна жорсткість [Н*м^2] відносно осі Y.")

    # Крутильна жорсткість
    GJ_torsion: float = Field(0.0, description="Крутильна жорсткість [Н*м^2].")

    # Осьова жорсткість
    EA_axial: float = Field(0.0, description="Осьова жорсткість [Н].")

    # Зсувні жорсткості
    GA_shear_x: float = Field(0.0, description="Зсувна жорсткість [Н] по осі X.")
    GA_shear_y: float = Field(0.0, description="Зсувна жорсткість [Н] по осі Y.")
    GA_shear_z: float = Field(0.0, description="Зсувна жорсткість [Н] по осі Z.")

    class Config:
        frozen = True


class DistributedInertialProperties(BaseModel):
    """
    Інкапсулює обчислені погонні масово-інерційні характеристики
    (маса та момент інерції на одиницю довжини).
    """
    m_prime_effective: float = Field(description="Ефективна погонна маса [кг/м].")
    Im_prime_effective: float = Field(description="Ефективний погонний момент інерції маси [кг*м^2/м].")

    class Config:
        frozen = True


class LinearStructureSectionProperties(BaseModel):
    """
    Інкапсулює параметри дискретизації та розподілені структурні властивості
    вздовж одновимірної осі (наприклад, крила або балки).

    Клас забезпечує:
    1.  **Дискретизацію**: Зберігання даних у дискретних точках вздовж осі Z.
    2.  **Погонні властивості**: Інкапсуляцію погонної маси, жорсткості та інерції.
    3.  **Валідацію**: Автоматичну перевірку відповідності розмірів масивів
        кількості секцій (N) для забезпечення математичної коректності подальших розрахунків.
    """
    section_count: int = Field(gt=0, description="Кількість дискретних секцій (N).")
    delta_x: float = Field(gt=0, description="Довжина однієї секції (Delta_Z) [м].")
    z_coords: np.ndarray = Field(description="Координати Z перерізів (від 0 до L). Довжина N+1.")

    m_prime_array: np.ndarray = Field(description="Погонна маса [кг/м] для кожної точки.")
    EI_y_array: np.ndarray = Field(description="Згинальна жорсткість [Н*м^2] для кожної точки.")
    Im_prime_array: np.ndarray = Field(description="Погонний момент інерції [кг*м^2/м] для кожної точки.")
    GJ_array: np.ndarray = Field(description="Крутильна жорсткість [Н*м^2] для кожної точки.")

    class Config:
        arbitrary_types_allowed = True # Дозволяємо np.ndarray
        frozen = True # Якщо дані мають бути незмінними після створення

    @classmethod
    def __pydantic_init_validator__(cls, values):
        n = values.get('section_count')
        if n is not None:
            expected_len = n + 1
            for name in ['m_prime_array', 'EI_y_array', 'Im_prime_array', 'GJ_array', 'z_coords']:
                arr = values.get(name)
                if arr is not None and len(arr) != expected_len:
                    raise ValueError(f"Довжина масиву '{name}' ({len(arr)}) не відповідає очікуваній ({expected_len}).")
        return values

    @computed_field
    @property
    def total_length(self) -> float:
        """Загальна довжина структури."""
        if len(self.z_coords) > 1:
            return self.z_coords[-1] - self.z_coords[0]
        return 0.0

    @computed_field
    @property
    def total_mass(self) -> float:
        """Загальна маса структури (інтеграція погонної маси)."""
        # Інтегруємо m_prime вздовж z
        return np.trapezoid(self.m_prime_array, self.z_coords)
