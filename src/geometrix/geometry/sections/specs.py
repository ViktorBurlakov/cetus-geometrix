from pydantic import Field
from geometrix.geometry.sections.factory import create_i_beam, create_c_channel, create_l_section, create_box_section
from geometrix.geometry.spec import GeometrySpec


class IBeamSpec(GeometrySpec):
    """Параметри Двотавра. Відповідає create_i_beam(H, B, t_f, t_w, R)."""
    H: float = Field(description="Загальна висота (H) [м]")
    B: float = Field(description="Ширина полиці (B) [м]")
    t_f: float = Field(description="Товщина полиці (t_f) [м]")
    t_w: float = Field(description="Товщина стінки (t_w) [м]")
    R: float = Field(0.0, description="Радіус заокруглення (R) [м]")

    class Config:
        default_factory_func = create_i_beam


class CChannelSpec(GeometrySpec):
    """Параметри Швелера. Відповідає create_c_channel(H, B, t_w, t_f)."""
    H: float = Field(description="Загальна висота (H) [м]")
    B: float = Field(description="Ширина полиці (B) [м]")
    t_w: float = Field(description="Товщина стінки (t_w) [м]")
    t_f: float = Field(description="Товщина полиці (t_f) [м]")

    class Config:
        default_factory_func = create_c_channel


class LSectionSpec(GeometrySpec):
    """Параметри Кутика. Відповідає create_l_section(B, H, t)."""
    B: float = Field(description="Ширина полиці 1 (B) [м]")
    H: float = Field(description="Ширина полиці 2 (H) [м]")
    t: float = Field(description="Рівномірна товщина (t) [м]")

    class Config:
        default_factory_func = create_l_section


class RHSSpec(GeometrySpec):
    """Параметри Box Section. Відповідає create_box_section(B, H, t)."""
    B: float = Field(description="Зовнішня ширина (B) [м]")
    H: float = Field(description="Зовнішня висота (H) [м]")
    t: float = Field(description="Рівномірна товщина стінки (t) [м]")

    class Config:
        default_factory_func = create_box_section
