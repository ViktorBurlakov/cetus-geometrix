# 📚 Theory: Structural Element Properties (`properties.py`)

## 1. Module Purpose and Architectural Role
The `properties.py` module is fundamental for any structural analysis. It contains **Data Transfer Objects (DTOs)** that describe the physical characteristics of structural elements:
* **Stiffness Properties**: Resistance to deformation (bending, torsion, axial, shear).
* **Inertial Properties**: Distribution of mass and inertia along the element.
* **Discretization Parameters**: How the element is divided into sections for numerical calculation.

These models are *general* for various analysis types and serve as input data for solvers.

## 2. Key Engineering Concepts

### Distributed and Integral Characteristics

#### 2.1. Distributed (Per Unit Length) Characteristics
These are properties related to a unit length of the element. They allow modeling elements with varying cross-sections or materials along their axis.
* **Distributed mass ($m'$)**: Mass distributed per unit length [kg/m].
* **Distributed mass moment of inertia ($I_m'$)**: Mass moment of inertia distributed per unit length [kg·m²/m].

#### 2.2. Stiffness Characteristics
Describe an element's ability to resist deformation under loads.
* **Bending Stiffness ($EI$)**: Product of Young's Modulus ($E$) and the area moment of inertia of the cross-section ($I$). Characterizes the element's resistance to bending [N·m²].
* **Torsional Stiffness ($GJ$)**: Product of the Shear Modulus ($G$) and the polar moment of inertia of the cross-section ($J$). Characterizes the element's resistance to torsion [N·m²].
* **Axial Stiffness ($EA$)**: Product of Young's Modulus ($E$) and the cross-sectional area ($A$). Characterizes the element's resistance to axial deformation (tension/compression) [N].
* **Shear Stiffness ($GA_{shear}$)**: Product of the Shear Modulus ($G$) and the effective shear area ($A_{shear}$). Characterizes the element's resistance to shear deformation [N].

### 3. Discretization of Linear Structures

For numerical analysis methods (such as the finite element method or the progressive iteration method), a continuous structural model is broken down into a finite number of discrete sections.
* **`section_count` (N)**: The number of discrete sections. This means the element will have $N+1$ points (nodes) where properties are defined.
* **`z_coords`**: An array of Z-coordinates for these $N+1$ points.
* All distributed properties (`m_prime_array`, `EI_y_array`, etc.) are given as arrays of length $N+1$, corresponding to these points.

This allows modeling elements with varying properties along their length (e.g., tapered beams or beams with different materials).