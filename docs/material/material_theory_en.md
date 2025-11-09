# 📚 Theory: Material Modeling (`material/models.py`)

## 1. Module Purpose
The `material/models.py` module is fundamental for any engineering analysis involving physical objects. It contains the **basic Data Transfer Object (DTO) `Material`**, which encapsulates the key physical and mechanical properties of an engineering material.

This model is immutable and ensures data validation through the use of Pydantic.

## 2. Key Engineering Concepts and Properties

### 2.1. Density (`density`)
* **Description**: The mass of the material per unit volume [kg/m³].
* **Engineering Significance**: Used to calculate the mass and inertial characteristics of elements, which is critical for dynamic analysis and self-weight load determination.

### 2.2. Young's Modulus (`E`, Modulus of Elasticity)
* **Description**: A measure of the stiffness of an elastic material, defining its resistance to elastic deformation under axial load (tension or compression) [Pa].
* **Formula**: $E = \sigma / \varepsilon$, where $\sigma$ is normal stress, $\varepsilon$ is linear strain.
* **Engineering Significance**: A fundamental parameter for calculating bending and axial stiffness. A high $E$ indicates high stiffness.

### 2.3. Poisson's Ratio (`nu`)
* **Description**: A dimensionless measure of the Poisson effect, describing the ratio of transverse strain to axial strain [dimensionless].
* **Engineering Significance**: Influences the calculation of the shear modulus and is used in elasticity theory to account for transverse deformations.

### 2.4. Shear Modulus (`shear_modulus`, $G$)
* **Description**: A measure of the material's resistance to shear deformation [Pa].
* **Formula (for isotropic materials)**:
    $$G = \frac{E}{2(1 + \nu)}$$
* **Engineering Significance**: Crucial for calculating the torsional and shear stiffness of elements. For most metals, $G \approx 0.38 \cdot E$.

**Important**: The `Material` model serves as the foundation for defining the stiffness properties of any engineering element by aggregating these fundamental constants.