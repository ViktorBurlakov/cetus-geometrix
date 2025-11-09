***

# 📚 Theory: Constructive Solid Geometry (CSG)

## 1. The CSG Concept

Constructive Solid Geometry (CSG) is a modeling technique that allows complex geometric shapes to be built by combining simpler figures (primitives) using boolean operations.

**Key Components:**

1.  **Primitives:** Basic shapes (e.g., `RectangularSection`, circle). These are the **leaf nodes** in the CSG tree.
2.  **Operations:** Boolean functions that define how primitives are combined. These are the **nodes** in the CSG tree.

### 1.1. The CSG Tree
The result of every boolean operation is a new object which can itself be an operand for the next operation. Thus, a complex shape is represented as a **binary tree** (the CSG tree), where the leaves are primitives and the nodes are boolean operations (`UNION`, `DIFFERENCE`, `INTERSECTION`).

## 2. CSG Implementation with Shapely

In 2D systems, such as Geometrix, CSG operations are efficiently implemented using the **Shapely** library (an interface to the high-performance GEOS library).

* **Primitives:** Each primitive has a method that returns its **Shapely representation** (`shapely_geometry`).
* **Operations:** The `UnionOperation`, `DifferenceOperation`, and `IntersectionOperation` classes simply call the corresponding Shapely methods (`.union()`, `.difference()`, `.intersection()`).

This approach guarantees the **accurate and robust** calculation of the resulting contour, which is crucial for the next stage: property calculation.

## 3. Inertial Property Calculation

After a boolean operation (e.g., $A - B$), we need accurate geometric sums ($A_{final}, S_{x, final}, I_{x, final}, \dots$). Due to the complexity of the resulting shape (with holes, multi-part contours), using simple additive/subtractive rules for the sums (*e.g., $S_{x, A-B} = S_{x, A} - S_{x, B}$*) is **inaccurate** and can lead to errors due to double-counting of overlapping areas.

### 3.1. Contour-Based Calculation (Robust Summation)
To ensure accuracy, Geometrix uses a method based on integrating over the contour of the final Shapely geometry (the `_calculate_sums_from_shapely` function):

1.  **Normalization:** The final Shapely shape (Polygon or MultiPolygon) is broken down into individual `Polygon` objects.
2.  **Integration:** For each polygon, a vertex-based formula (like the Shoelace/Gauss area formula extension) is used to calculate the raw geometric sums.
3.  **Holes Handling:** The contours of internal holes (interior rings) are integrated in the **reverse direction**, which automatically results in the **subtraction** of their geometric sums from the exterior contour's sum.

This method guarantees that the aggregate sums **($S_x, I_y, \dots$)** are accurate, regardless of the complexity of the boolean operation.

### 3.2. Centroid and Central Moments
The calculation of the centroid and central moments of inertia is always performed in a unified way:

1.  **Centroid:** $c_x = S_y / A$, $c_y = S_x / A$.
2.  **Central Moments:** To transfer moments of inertia from the global origin $I_{x0}$ to the centroid $I_c$, the **Reverse Steiner's Theorem** is used:
    $$I_c = I_{x0} - A \cdot c_y^2$$
This completes the process, providing an accurate set of inertial properties for any complex shape derived through CSG.