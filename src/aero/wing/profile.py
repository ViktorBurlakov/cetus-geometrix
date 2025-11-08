from pydantic import BaseModel, Field, computed_field

from geometrix.geometry.spec import GeometrySpec


class WingProfile(GeometrySpec):
    """
    Геометрична модель перерізу крила (порожнистий прямокутник/квадрат - RHS),
    використовувана для обчислення площі та моментів інерції.

    Всі розміри в метрах (СІ).
    """
    B: float = Field(0.05, gt=0, description="Зовнішня ширина профілю (по осі Y)")
    H: float = Field(0.10, gt=0, description="Зовнішня висота профілю (по осі X)")
    t_x: float = Field(0.005, gt=0, description="Товщина стінок, паралельних осі Y (горизонтальні полиці)")
    t_y: float = Field(0.005, gt=0, description="Товщина стінок, паралельних осі X (вертикальні стінки)")

    @computed_field
    @property
    def b_inner(self) -> float:
        """Внутрішня ширина (b) [м]. b = B - 2 * t_y."""
        b = self.B - 2 * self.t_y
        if b <= 0:
            raise ValueError("Внутрішня ширина (b) має бути позитивною. Перевірте B та t_y.")
        return b

    @computed_field
    @property
    def h_inner(self) -> float:
        """Внутрішня висота (h) [м]. h = H - 2 * t_x."""
        h = self.H - 2 * self.t_x
        if h <= 0:
            raise ValueError("Внутрішня висота (h) має бути позитивною. Перевірте H та t_x.")
        return h

    # --- 3. МАСОВО-ГЕОМЕТРИЧНІ ХАРАКТЕРИСТИКИ ---

    @computed_field
    @property
    def area(self) -> float:
        """
        Площа поперечного перерізу (A) [м^2].
        A = (Зовнішня площа) - (Внутрішня площа) = (B*H) - (b*h)
        """
        return (self.B * self.H) - (self.b_inner * self.h_inner)

    @computed_field
    @property
    def I_x(self) -> float:
        """
        Площинний момент інерції відносно осі X (I_x) [м^4].
        Опір згину у вертикальній площині.
        I_x = (B*H^3 - b*h^3) / 12
        """
        return (self.B * self.H ** 3 - self.b_inner * self.h_inner ** 3) / 12.0

    @computed_field
    @property
    def I_y(self) -> float:
        """
        Площинний момент інерції відносно осі Y (I_y) [м^4].
        Опір згину у горизонтальній площині.
        I_y = (H*B^3 - h*b^3) / 12
        """
        return (self.H * self.B ** 3 - self.h_inner * self.b_inner ** 3) / 12.0

    @computed_field
    @property
    def J_torsion(self) -> float:
        """
        Момент інерції для кручення (J) [м^4].
        Використовується спрощена формула для тонкостінної прямокутної труби.
        J ≈ 2 * A_m * t_avg / L_m
        Де A_m - площа, обмежена середньою лінією, L_m - довжина середньої лінії, t_avg - середня товщина.
        Спрощена інженерна формула для товстих стінок: J = (I_x + I_y) (Полярний момент).
        Тут використовуємо формулу для прямокутної труби з постійною товщиною (t=t_x=t_y):
        J ≈ 2 * B * H * t / (B + H)

        Для універсальності та простоти поки використовуємо полярний момент: J = I_x + I_y
        """
        return self.I_x + self.I_y

    # --- 4. АЕРОДИНАМІЧНІ/ГЕОМЕТРИЧНІ СВІВВІДНОШЕННЯ ---

    @computed_field
    @property
    def thickness_ratio(self) -> float:
        """Співвідношення товщини до хорди (у цьому контексті H/B)."""
        if self.B == 0:
            return 0.0
        return self.H / self.B


# --- ДЕМОНСТРАЦІЙНЕ ВИКОРИСТАННЯ ---
if __name__ == '__main__':
    profile = WingProfile(B=0.04, H=0.08, t_x=0.002, t_y=0.002)

    print("--- Характеристики Профілю Крила (RHS) ---")
    print(f"Зовнішні розміри: {profile.B * 100:.2f} x {profile.H * 100:.2f} см")
    print(f"Товщина стінок: {profile.t_x * 1000:.2f} мм")
    print(f"Внутрішні розміри (b x h): {profile.b_inner * 100:.2f} x {profile.h_inner * 100:.2f} см")
    print(f"Площа перерізу (A): {profile.area:.6f} м^2")
    print(f"Момент I_x (згин верт.): {profile.I_x:.8e} м^4")
    print(f"Момент I_y (згин гориз.): {profile.I_y:.8e} м^4")
    print(f"Момент J (кручення): {profile.J_torsion:.8e} м^4")