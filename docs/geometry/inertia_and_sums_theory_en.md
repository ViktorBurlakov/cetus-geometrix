# 📚 Theory: Geometric Sums and Inertia Tensors

## 1. Basic Geometric Structures

### 1.1. Precision and Coordinates
* **`TOLERANCE`**: Defines global tolerance constants. This is crucial for floating-point comparisons and for preventing division-by-zero errors (e.g., during centroid calculation).
* **`Vertex`**: The fundamental DTO for representing a point in space ($x, y, z$). In 2D geometry, the $z$ coordinate typically remains zero.

### 1.2. Boolean Operations (`OperationType`)
This enumerator is used to define the type of operation in Constructive Solid Geometry (CSG) nodes, allowing for the programmatic modeling of complex shapes:
* `UNION`: Property addition.
* `DIFFERENCE`: Property subtraction (e.g., modeling a hole or cutout).

## 2. First Order Moments (Static Moments)

### `StaticMoments`
This class encapsulates the **Static Moments ($S$)** of an object relative to the global coordinate origin $(0, 0, 0)$.

* **Purpose**: Critical for finding the **Centroid (Center of Mass)** of the cross-section or body:
    $$\text{Centroid } (\bar{x}, \bar{y}) = \left( \frac{S_y}{A}, \frac{S_x}{A} \right)$$
* **Operations**: The `__add__` and `__sub__` methods allow for the correct aggregation of static moments according to the Boolean operations.

## 3. Second Order Moments (Inertia Tensor)

### `InertiaTensor`
This class is the universal form for storing **Moments and Products of Inertia** relative to the global origin (Second Order Moments).

| Component | Type | 2D (Area) | 3D (Mass) |
| :--- | :--- | :--- | :--- |
| **Ixx, Iyy, Izz** | Moments of Inertia | Axial Area Moments | Mass Moments of Inertia |
| **Ixy, Ixz, Iyz** | Products of Inertia | Area Products of Inertia | Mass Products of Inertia |
| **J_torsion** | Torsional Constant | Determines torsional stiffness ($GJ$) | - |

* **$I_{\text{polar}}$**: Polar Moment of Inertia (sum of $I_{xx} + I_{yy}$).
* **`ndarray` Method**: Converts the tensor components into a **2x2** (for 2D) or **3x3** (for 3D) matrix.

## 4. Aggregation and Transformation

### 4.1. Aggregated Geometric Sums (`GeometrySums`)
This is the central DTO that stores all "raw" integral properties:
* **Primary Measures**: Cross-sectional Area, Volume, Surface Area.
* **Moments**: `StaticMoments` and `InertiaTensor`.

These "raw" sums are the input for the Parallel Axis Theorem (Steiner's Theorem), which shifts the moments from the global origin to the centroidal axes.

### 4.2. Principal Properties

* **`PrincipalInertia`**: Contains the **Principal Moments of Inertia ($I_1, I_2$)** and the **Angle of Rotation ($\alpha$)**. They represent the minimum and maximum resistance to bending or rotation in the plane.
* **`RadiiOfGyration`**: Contains the **Radii of Gyration ($r$)** relative to the centroidal and principal axes. They are a measure of mass/area distribution and are used in stability (slenderness) calculations:
    $$r = \sqrt{\frac{I_{\text{centroid}}}{M \text{ or } A}}$$