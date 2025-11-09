from geometrix.material.models import Material
from geometrix.structural.common.properties import StiffnessProperties
from geometrix.geometry.models import InertiaTensor
from geometrix.structural.common.properties import ShearAreas  # Для shear_areas


def calculate_stiffness(
        material: Material,
        plane_area: float,
        centroid_inertia: InertiaTensor,
        shear_areas: ShearAreas
) -> StiffnessProperties:
    """
    Обчислює всі жорсткісні властивості елемента.
    """
    E = material.E
    G = material.shear_modulus

    # Використовуємо Izz як полярний момент, якщо J_torsion не визначений
    J_torsion_val = centroid_inertia.J_torsion or centroid_inertia.Izz

    return StiffnessProperties(
        EI_xx=E * centroid_inertia.Ixx,
        EI_yy=E * centroid_inertia.Iyy,
        GJ_torsion=G * J_torsion_val,
        EA_axial=E * plane_area,
        GA_shear_x=G * shear_areas.shear_area_x,
        GA_shear_y=G * shear_areas.shear_area_y,
        GA_shear_z=G * shear_areas.shear_area_z
    )


# Можна додати інші солвери, наприклад:
def calculate_total_mass(
        material: Material,
        volume: float
) -> float:
    """
    Обчислює загальну масу елемента.
    """
    return material.density * volume
