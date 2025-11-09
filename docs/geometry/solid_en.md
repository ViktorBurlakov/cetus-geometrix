# 📚 THEORY & API Reference: solid.py (3D Geometry)

The `solid.py` module establishes the object hierarchy for modeling **3D geometric bodies (Solids)**. Its primary role is to connect the calculated properties of **2D cross-sections** (`GeometryObject2D`) with the third dimension (length/height) to derive key 3D metrics: **Volume** and **Surface Area**.

---

## I. The `Solid` Abstraction

The `Solid` class serves as the abstract base for all 3D geometric objects, enforcing the required properties and methods for spatial geometry.

### Class: `Solid` (Abstract Base)

| Property | Type | Description |
| :--- | :--- | :--- |
| `plane_area` | `float` | Always returns **0.0**. For 3D solids, the cross-sectional area is not the primary measure. |
| `primary_measure` | `float` | Returns `self.volume`. This is the core measure for 3D objects. |
| **`volume`** | `float` | **[ABSTRACT, REQUIRED]** The volume of the solid ($V$). |
| **`surface_area`** | `float` | **[ABSTRACT, REQUIRED]** The total surface area of the solid. |

---

## II. `PrismaticSolid` (Extruded Geometry)

The `PrismaticSolid` class models a shape created by **extruding** a 2D cross-section along an axis for a defined length.

### A. Model Definition

| Field | Type | Description |
| :--- | :--- | :--- |
| `section` | `GeometryObject2D` | The 2D cross-section (e.g., `Rectangle`, `Compound`) that defines the shape. |
| `length` | `float` | The length of the extrusion ($L$). Must be greater than zero. |

### B. Property Calculation

1.  **Volume Calculation:** The volume is computed analytically using the area of the base cross-section (`section.plane_area`).

    $$\text{Volume} = A_{\text{section}} \cdot L$$

2.  **Surface Area (Conceptual Formula):** The total surface area consists of the two end caps (cross-sections) and the lateral area (perimeter times length).

    $$\text{Surface Area} = 2 \cdot A_{\text{section}} + P_{\text{section}} \cdot L$$

    ***NOTE on Implementation:*** *The current implementation of `surface_area` in `solid.py` is a placeholder (`return 0.0`) because the base class `GeometryObject2D` lacks the necessary `perimeter` property ($P_{\text{section}}$).*

3.  **Translation:** The `translate` method implements 3D movement by delegating the translation to the base 2D cross-section (`self.section.translate(dx, dy, dz)`) while preserving the length.