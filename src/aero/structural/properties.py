from geometrix.geometry.models import InertiaTensor
from geometrix.material.models import Material
from geometrix.structural.common.properties import DistributedInertialProperties


def calculate_wing_inertial_properties(
        material: Material,
        plane_area: float,
        centroid_inertia: InertiaTensor,
        r_offset: float,
        additional_mass_factor: float = 1.30
) -> DistributedInertialProperties:
    """
    Обчислює ефективну погонну масу та погонний момент інерції для елемента типу "крило".

    Аргументи:
        plane_area (float): Площа поперечного перерізу елемента [м^2].
        material (Material): Об'єкт матеріалу з властивостями density.
        centroid_inertia (InertiaTensor): Центроїдальні моменти інерції перерізу.
                                         Повинен містити Izz (полярний момент).
        r_offset (float): Відстань між центром мас та віссю зсуву (r) [м].
        additional_mass_factor (float): Коефіцієнт додаткової маси (наприклад, 1.30 для 30% додаткової).

    Повертає:
        DistributedInertialProperties: Об'єкт, що містить обчислені властивості.
    """
    # 1. Обчислення m_prime_effective
    m_l_prime = plane_area * material.density  # Погонна маса основного профілю
    m_prime = m_l_prime * additional_mass_factor # Додаємо додаткову масу

    # 2. Обчислення Im_prime_effective
    # Власний погонний момент інерції маси
    I_vl_prime = material.density * centroid_inertia.Izz
    # Теорема Штейнера для перенесення маси
    Im_prime = I_vl_prime + m_prime * r_offset ** 2

    return DistributedInertialProperties(
        m_prime_effective=m_prime,
        Im_prime_effective=Im_prime
    )
