from geometrix.geometry.models import InertiaTensor
from geometrix.material.models import Material

from geometrix.structural.common.properties import ShearAreas, StiffnessProperties


def calculate_stiffness(material: Material, plane_area: float,
                        centroid_inertia: InertiaTensor, shear_areas: ShearAreas) -> StiffnessProperties:
    """
    Calculates all stiffness properties of an element based on its material,
    cross-sectional area, moments of inertia, and shear areas.

    This function applies classical mechanics of materials formulas to derive
    the distributed stiffness parameters.

    Args:
        material (Material): Material properties (Young's Modulus E, Shear Modulus G).
        plane_area (float): Cross-sectional area of the element [m^2].
        centroid_inertia (InertiaTensor): Moments of inertia of the cross-section
                                         (I_xx, I_yy, J_torsion).
        shear_areas (ShearAreas): Effective shear areas (A_shear_x, A_shear_y, A_shear_z).

    Returns:
        StiffnessProperties: An object containing all calculated stiffness values.
    """
    E = material.E
    G = material.shear_modulus # G is a computed property of Material

    # Bending Stiffness
    EI_xx = E * centroid_inertia.I_xx
    EI_yy = E * centroid_inertia.I_yy

    # Torsional Stiffness
    # If explicit J_torsion is provided, use it. Otherwise, a common approximation is I_zz for round sections.
    GJ_torsion = G * (centroid_inertia.J_torsion if centroid_inertia.J_torsion != 0 else centroid_inertia.I_zz)

    # Axial Stiffness
    EA_axial = E * plane_area

    # Shear Stiffness
    GA_shear_x = G * shear_areas.shear_area_x
    GA_shear_y = G * shear_areas.shear_area_y
    GA_shear_z = G * shear_areas.shear_area_z

    return StiffnessProperties(
        EI_xx=EI_xx,
        EI_yy=EI_yy,
        GJ_torsion=GJ_torsion,
        EA_axial=EA_axial,
        GA_shear_x=GA_shear_x,
        GA_shear_y=GA_shear_y,
        GA_shear_z=GA_shear_z,
    )

def calculate_total_mass(material: Material, volume: float) -> float:
    """
    Calculates the total mass of an element.

    This is a straightforward calculation based on the element's volume and material density.

    Args:
        material (Material): Material properties (density).
        volume (float): Volume of the element [m^3].

    Returns:
        float: Total mass of the element in kilograms [kg].
    """
    return material.density * volume