from pydantic import Field, computed_field

from engine.structural.element import StructuralElement


class WingStructuralElement(StructuralElement):
    """
    Інженерний елемент, спеціалізований для крила.
    Поєднує профіль, матеріал і довжину.
    """
    profile: WingProfile
    r_offset: float = Field(0.0125, description="Відстань між центром мас та віссю зсуву (r) [м].")
    section_count: int = Field(description="Кількість секцій (N)")
    delta_x: float = Field(description="Довжина однієї секції (Delta_Z) [м]")

    # # Масиви властивостей (повинні мати довжину N_SECTIONS + 1)
    # m_prime_array: np.ndarray = Field(description="Погонна маса [кг/м] для кожної точки")
    # EI_y_array: np.ndarray = Field(description="Згинальна жорсткість [Н*м^2] для кожної точки")
    # Im_prime_array: np.ndarray = Field(description="Погонний момент інерції [кг*м^2] для кожної точки")
    # GJ_array: np.ndarray = Field(description="Крутильна жорсткість [Н*м^2] для кожної точки")
    # z_coords: np.ndarray = Field(description="Координати Z перерізів (від 0 до L)")

    class Config:
        arbitrary_types_allowed = True

    # =================================================================
    # 2. МАСОВІ ХАРАКТЕРИСТИКИ
    # =================================================================

    @computed_field
    @property
    def mass(self) -> float:
        """Обчислює масу секції: Mass = Area * Length * Density [кг]."""
        return self.profile.area * self.length * self.material.density

    @computed_field
    @property
    def m_prime_effective(self) -> float:
        """
        Ефективна погонна маса (m') [кг/м].
        Включає погонну масу лонжерону та додаткову масу (наприклад, 30% від лонжерону).
        """
        m_l_prime = self.profile.area * self.material.density  # Погонна маса лонжерону
        m_prime = m_l_prime * 1.30  # Додаємо 30% на обшивку/пластик
        return m_prime

    @computed_field
    @property
    def Im_prime_effective(self) -> float:
        """
        Ефективний погонний момент інерції (Im') [кг*м^2].
        Im' = I_vl_prime + m' * r^2
        """
        # I_vl_prime (Власний момент інерції) ≈ Density * J
        I_vl_prime = self.material.density * self.profile.J_torsion

        # Використовуємо r (r_offset) та ефективну погонну масу
        return I_vl_prime + self.m_prime_effective * self.r_offset ** 2

    @computed_field
    @property
    def EI_y(self) -> float:
        """Згинальна жорсткість (EI_y) [Н*м^2]. EI_y = E * I_y."""
        return self.material.E * self.profile.I_y

    @computed_field
    @property
    def GJ_torsion(self) -> float:
        """Крутильна жорсткість (GJ) [Н*м^2]. GJ = G * J_torsion."""
        # Використовуємо модуль зсуву G та крутильний момент J
        return self.material.G * self.profile.J_torsion
