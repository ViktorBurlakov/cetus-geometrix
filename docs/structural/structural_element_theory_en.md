# 📚 Theory: Structural Element (`structural/models.py`)

## 1. Module Purpose
The `structural/models.py` module contains the high-level **`StructuralElement` model**. This class is a key aggregator that combines two main aspects of any physical engineering component:
1.  **Geometry (`Solid`)**: What shape does the element have?
2.  **Material (`Material`)**: What is it made of?

This is a central DTO (Data Transfer Object) that creates a complete context for describing an object before its properties are prepared for numerical analysis (discretized, converted to stiffnesses, etc.).

## 2. Architectural Pattern: Aggregation (Composition)

The `StructuralElement` class implements the **Aggregation (Composition)** pattern. Instead of containing all geometric and material properties directly, it *has* references to other objects that encapsulate this data:
* `solid`: An object of type `Solid`, which provides information about volume, center of mass, and moments of inertia.
* `material`: An object of type `Material`, which provides information about density, moduli of elasticity.

This ensures:
* **Separation of Concerns**: Each class is responsible only for its own aspect (Solid for geometry, Material for material).
* **Flexibility**: Easy to replace or extend geometry or material types without changing `StructuralElement`.
* **Clarity**: The code becomes easier to understand and maintain.

## 3. Computed Properties (Derived Properties)

Based on the aggregated data, `StructuralElement` can compute important derived properties:

### 3.1. Mass (`mass`)
* **Description**: The total mass of the element [kg].
* **Formula**: $$M = \text{Solid.volume} \cdot \text{Material.density}$$
* **Engineering Significance**: A fundamental parameter for dynamic analysis, calculation of inertial loads, and determining the self-weight of a structure.

### 3.2. Principal Mass Moments of Inertia (`principal_inertia`)
* **Description**: Inertial characteristics of the mass with respect to the principal axes. They describe the body's resistance to rotational motion [kg·m²].
* **Engineering Significance**: Critically important for dynamic analysis, especially for calculating torsional vibrations and rotational stability. These values are usually already computed by the geometric `Solid` model.

### 3.3. Radii of Gyration (`radii_of_gyration`)
* **Description**: The distance from the axis of rotation at which all the mass of the body should be concentrated so that its moment of inertia with respect to that axis remains unchanged [m].
* **Engineering Significance**: Used for quick estimation of inertial properties and in some stability formulas. Also usually already computed by the geometric `Solid` model.

**Conclusion**: `StructuralElement` serves as a kind of "passport" for an engineering object, collecting all basic characteristics necessary for further, more detailed analysis.