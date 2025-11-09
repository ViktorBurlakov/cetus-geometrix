# 📚 Theory: Common Utility Solvers (`solvers.py`)

## 1. Module Purpose
The `solvers.py` module within the `common` package contains a **set of utility functions**. These are not full iterative solvers but perform intermediate, direct calculations necessary for data preparation or for basic computations used by other solvers.

## 2. Theoretical Background: Stiffness and Mass Calculations

The functions in this module apply basic principles from mechanics of materials and structural mechanics.

### 2.1. Calculation of Stiffness Characteristics (`calculate_stiffness`)
The stiffness characteristics of an element describe its resistance to deformation under various types of loads. They are calculated based on material properties (Young's Modulus $E$, Shear Modulus $G$) and geometric characteristics of the element's cross-section (Area $A$, Moments of Inertia $I, J$).

* **Bending Stiffness ($EI$)**:
    $$EI = E \cdot I$$
    where $E$ is Young's Modulus, and $I$ is the area moment of inertia of the cross-section with respect to the relevant axis.
* **Torsional Stiffness ($GJ$)**:
    $$GJ = G \cdot J$$
    where $G$ is the Shear Modulus, and $J$ is the torsional constant (or polar moment of inertia for circular sections). The function includes a provision to use $I_{zz}$ as an approximation if $J_{torsion}$ is not explicitly provided.
* **Axial Stiffness ($EA$)**:
    $$EA = E \cdot A$$
    where $A$ is the cross-sectional area.
* **Shear Stiffness ($GA_{shear}$)**:
    $$GA_{shear} = G \cdot A_{shear}$$
    where $A_{shear}$ is the effective shear area (which may differ from the full area for certain cross-sectional shapes).

### 2.2. Calculation of Total Mass (`calculate_total_mass`)
The total mass of an element is a primary inertial parameter.
* **Mass ($M$)**:
    $$M = \rho \cdot V$$
    where $\rho$ is the material density, and $V$ is the element's volume.