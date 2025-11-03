"""## 🛠️ Функції-Конструктори Структурних Профілів (Section Factories)"""
import math
from .core import Compound, Rectangle, CircularArc, TOLERANCE


def create_i_beam(
        H: float,  # Загальна висота профілю
        B: float,  # Ширина полиці
        t_f: float,  # Товщина полиці (flange thickness)
        t_w: float,  # Товщина стінки (web thickness)
        R: float = 0.0,  # Радіус заокруглення
) -> Compound:
    """
    Створює параметричний двотавровий профіль (I-beam).

    Геометрія:
    - Профіль симетричний відносно осей X та Y.
    - Центр (стик осей) знаходиться у геометричному центрі.
    - Використовує операцію UNION (+) для об'єднання трьох прямокутників
      (стінка та дві полиці) та чотирьох CircularArc (радіуси заокруглення).

    Параметри:
    :param H: Загальна висота перерізу (мм).
    :param B: Ширина полиці (мм).
    :param t_f: Товщина верхньої та нижньої полиці (мм).
    :param t_w: Товщина вертикальної стінки (мм).
    :param R: Радіус заокруглення в кутах між стінкою та полицями (мм).
    :return: Об'єкт Compound (корінь CSG-дерева I-beam).
    """
    h_web = H - 2 * t_f
    y_flange = H / 2 - t_f / 2

    web = Rectangle(x=0, y=0, width=t_w, height=h_web)
    flange_top = Rectangle(x=0, y=y_flange, width=B, height=t_f)
    flange_bottom = Rectangle(x=0, y=-y_flange, width=B, height=t_f)

    i_beam_base = web + flange_top + flange_bottom

    if R <= TOLERANCE:
        return i_beam_base

    x_c = t_w / 2 + R
    y_junct = H / 2 - t_f
    y_c = y_junct - R

    arc_tl = CircularArc(x=-x_c, y=y_c, radius=R, start_angle=math.pi, end_angle=1.5 * math.pi)
    arc_tr = CircularArc(x=x_c, y=y_c, radius=R, start_angle=1.5 * math.pi, end_angle=2 * math.pi)
    arc_bl = CircularArc(x=-x_c, y=-y_c, radius=R, start_angle=0.5 * math.pi, end_angle=math.pi)
    arc_br = CircularArc(x=x_c, y=-y_c, radius=R, start_angle=0, end_angle=0.5 * math.pi)

    final_i_beam = i_beam_base + arc_tl + arc_tr + arc_bl + arc_br
    return final_i_beam


def create_c_channel(
        H: float,  # Загальна висота профілю
        B: float,  # Ширина полиці
        t_w: float,  # Товщина стінки
        t_f: float,  # Товщина полиці
) -> Compound:
    """
    Створює параметричний швелер (C-channel).

    Геометрія:
    - Профіль симетричний відносно осі X (горизонтальної).
    - Вертикальна стінка розташована по осі Y (на x=0).
    - Центр мас буде зміщений по осі X (потрібне обчислення .cx для знаходження ЦМ).
    - Використовує операцію UNION (+) трьох прямокутників.

    Параметри:
    :param H: Загальна висота перерізу (мм).
    :param B: Ширина зовнішніх полиць (мм).
    :param t_w: Товщина вертикальної стінки (мм).
    :param t_f: Товщина верхньої та нижньої полиці (мм).
    :return: Об'єкт Compound (корінь CSG-дерева C-channel).
    """
    h_web = H - 2 * t_f
    y_flange = H / 2 - t_f / 2

    web = Rectangle(x=0, y=0, width=t_w, height=h_web)
    x_flange_center = t_w / 2 + B / 2

    flange_top = Rectangle(x=x_flange_center, y=y_flange, width=B, height=t_f)
    flange_bottom = Rectangle(x=x_flange_center, y=-y_flange, width=B, height=t_f)

    return web + flange_top + flange_bottom


def create_l_section(
        B: float,  # Ширина полиці 1
        H: float,  # Ширина полиці 2 (висота)
        t: float,  # Товщина
) -> Compound:
    """
    Створює параметричний кутовий профіль (L-section).

    Геометрія:
    - Профіль створюється в першому квадранті, з кутом у точці (0, 0).
    - Використовує метод CSG DIFFERENCE (-) :
      (Великий прямокутник B x H) - (Внутрішній прямокутник (B-t) x (H-t)).

    Параметри:
    :param B: Довжина горизонтальної полиці (мм).
    :param H: Довжина вертикальної полиці (мм).
    :param t: Рівномірна товщина полиць (мм).
    :return: Об'єкт Compound (корінь CSG-дерева L-section).
    """
    outer_rect = Rectangle(x=B / 2, y=H / 2, width=B, height=H)

    inner_width = B - t
    inner_height = H - t

    inner_x = t + inner_width / 2
    inner_y = t + inner_height / 2

    hole_rect = Rectangle(x=inner_x, y=inner_y, width=inner_width, height=inner_height)

    l_section = outer_rect - hole_rect
    return l_section


def create_box_section(
        B: float,  # Зовнішня ширина
        H: float,  # Зовнішня висота
        t: float,  # Товщина стінки (рівномірна)
) -> Compound:
    """
    Створює параметричний прямокутний трубний профіль (RHS).

    Геометрія:
    - Профіль симетричний відносно осей X та Y.
    - Центр (0, 0) знаходиться у геометричному центрі.
    - Використовує метод CSG DIFFERENCE (-):
      (Зовнішній прямокутник B x H) - (Внутрішній отвір (B-2t) x (H-2t)).

    Параметри:
    :param B: Зовнішня ширина профілю (мм).
    :param H: Зовнішня висота профілю (мм).
    :param t: Рівномірна товщина стінок (мм).
    :return: Об'єкт Compound (корінь CSG-дерева Box Section).
    """
    outer_rect = Rectangle(x=0, y=0, width=B, height=H)

    inner_width = B - 2 * t
    inner_height = H - 2 * t

    hole_rect = Rectangle(x=0, y=0, width=inner_width, height=inner_height)

    box_section = outer_rect - hole_rect
    return box_section
