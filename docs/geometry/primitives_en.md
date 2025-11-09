# 💡 Theoretical Foundations of the `primitives.py` Module (2D Cross-Sections)

The `primitives.py` module serves as the engineering core of the library for modeling and calculating **Geometric Properties** of 2D cross-sections. Its primary objective is to ensure accurate calculation of **Area (A)**, **Static Moments ($S_x, S_y$)**, and **Moments of Inertia ($I_{xx}, I_{yy}, I_{xy}$)**.

---

## 1. Fundamental Data Models

The `primitives.py` module heavily relies on data models defined in `geometrix.geometry.models` for structure and type safety:

1.  **`Vertex`:** The minimum structure for storing point coordinates (x, y).
2.  **`InertiaTensor`:** Holds the moments of inertia ($I_{xx}, I_{yy}$) and the product of inertia ($I_{xy}$).
3.  **`Centroid`:** Combines the area, center coordinates ($c_x, c_y$), and the centroidal moments of inertia ($I_c$).
4.  **`GeometrySums`:** Contains the final calculated properties relative to the global origin $(0, 0)$.

---

## 2. Property Calculation Methodology

The module divides primitives into two categories based on their calculation method.

### A. Analytical Primitives (`Rectangle`, `Circle`)

Calculations are based on **exact, closed-form formulas**.

* **Step 1: Own Centroid ($I_c$)**
    Properties (e.g., $A, I_{xx}, I_{yy}$) are computed using classical formulas relative to the object's own center of mass. For a rectangle, $I_{xx, c} = \frac{bh^3}{12}$, $I_{yy, c} = \frac{hb^3}{12}$.
* **Step 2: Steiner Transfer**
    To obtain the final `GeometrySums` (relative to the global origin $I_0$), the **Direct Steiner Transfer Theorem** is used (`transfer_properties` from `calculations`):
    $$\text{Direct Steiner Transfer: } I_{0} = I_{c} + A \cdot d^2$$
    where $d$ is the displacement of the object's centroid relative to the axis (e.g., $d=c_y$ for $I_{xx}$).

### B. Numerical Primitives (`Polygon`, `CircularArc`, `BSpline`)

These objects rely on **numerical integration** of the boundary contour. `CircularArc` and `BSpline` are first approximated as a `Polygon`.

* **Step 1: Calculation Relative to the Origin ($I_0$)**
    The **Gauss-Green Formula** (implemented in `calculate_vertices_sums`) is used for a sequence of vertices $(x_i, y_i)$:
    * **Area ($A$):**
        $$A = \frac{1}{2} \sum_{i=1}^{n} (x_i y_{i+1} - x_{i+1} y_i)$$
    * **Static Moments ($S_x, S_y$):**
        $$S_x = \frac{1}{6} \sum_{i=1}^{n} (x_i y_{i+1} - x_{i+1} y_i) (y_i + y_{i+1})$$
        $$S_y = \frac{1}{6} \sum_{i=1}^{n} (x_i y_{i+1} - x_{i+1} y_i) (x_i + x_{i+1})$$
    * **Moments of Inertia ($I_{xx}, I_{yy}, I_{xy}$) relative to $(0, 0)$:**
        $$I_{xx, 0} = \frac{1}{12} \sum_{i=1}^{n} (x_i y_{i+1} - x_{i+1} y_i) (y_i^2 + y_i y_{i+1} + y_{i+1}^2)$$
        $$I_{yy, 0} = \frac{1}{12} \sum_{i=1}^{n} (x_i y_{i+1} - x_{i+1} y_i) (x_i^2 + x_i x_{i+1} + x_{i+1}^2)$$
* **Step 2: Centroid Calculation and Inverse Transfer**
    * Centroid Coordinates: $c_x = S_y / A$ and $c_y = S_x / A$.
    * The **Inverse Steiner Transfer** is applied (`transfer_properties` with `reverted=True`) to find $I_c$:
    $$\text{Inverse Steiner Transfer: } I_{c} = I_{0} - A \cdot d^2$$

---

## 3. Constructive Solid Geometry (CSG)

The **`Compound`** class builds the binary CSG tree and handles complex shapes created by Boolean operations.

### A. Topology (Shapely)

The `shapely_geometry` property is responsible for creating the final contour. It recursively executes Boolean operations (`UNION`, `DIFFERENCE`, `INTERSECTION`) on the operands (`left`, `right`) using the robust **Shapely** (GEOS) library.

### B. Property Calculation for `Compound`

The calculation of properties (specifically `sums` and `centroid`) is delegated to the `CSGOperation` object.

1.  **Final Shape First:** The final Shapely geometry is obtained.
2.  **Calculation:** To get the accurate properties of the final composite shape (especially those with holes), the calculation is performed **numerically** based on the **vertices of the final contour**, using the same $I_0 \to I_c$ mechanism as for a standard `Polygon`.

This methodology ensures that the properties are always consistent with the actual geometry of the resulting cross-section, regardless of the complexity of the CSG tree.