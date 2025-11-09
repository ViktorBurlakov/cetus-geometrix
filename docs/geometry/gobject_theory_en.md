# 📚 Theory: Abstract Geometric Object (`GeometryObject`)

## 1. The Base Interface Concept

`GeometryObject` is an **Abstract Base Class (ABC)** that acts as the single interface for all geometric entities in the `geometrix` system. Every object (2D cross-section, 3D solid) inherits the functionality required for:
1.  Integration into **Constructive Solid Geometry (CSG)**.
2.  Calculation of **inertial properties**.

### 1.1. Role in the CSG Tree
Every `GeometryObject` is a node in the CSG tree, where the `op_type` field defines how this node interacts with others.

* **`OperationType.PRIMITIVE`**: Leaf nodes (basic shapes).
* **Boolean Operators (`__add__`, `__sub__`, `__mul__`)**: Overridden in derived classes to create complex objects through union, difference, or intersection.

## 2. Fundamental Properties (Abstract)

Three abstract properties form the basis for all calculations and must be implemented by every concrete geometric class:

| Property | Purpose | Calculated Relative to |
| :--- | :--- | :--- |
| **`sums`** | **Raw Geometric Sums (`GeometrySums`)** – volume, static moments ($S_x, S_y, S_z$), and moments of inertia ($I_{x0}, I_{y0}, \dots$). | The **Global Origin** $(0,0,0)$. |
| **`centroid`** | **Centroidal Properties (`Centroid`)** – coordinates of the center of mass/centroid and moments of inertia translated to the centroidal axes. | The **Center of Mass** $(\bar{x}, \bar{y}, \bar{z})$. |
| **`primary_measure`** | The object's primary measure: **Area** (2D) or **Volume** (3D). | - |

## 3. Centroid Coordinate Calculation

The base class `GeometryObject` contains the implementations for calculating the centroid coordinates ($c_x, c_y, c_z$) based on the raw geometric sums:

* **$c_x$ (X-coordinate)**:
    $$c_x = \frac{S_y}{\text{Primary Measure}}$$
* **$c_y$ (Y-coordinate)**:
    $$c_y = \frac{S_x}{\text{Primary Measure}}$$
* **$c_z$ (Z-coordinate)**:
    $$c_z = \frac{S_z}{\text{Primary Measure}}$$
    
The calculation is protected against division by zero using the global constant `TOLERANCE.AREA_CALC`.