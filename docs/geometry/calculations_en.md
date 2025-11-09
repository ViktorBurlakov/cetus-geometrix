# 📚 Theory and API Reference: calculations.py (Core Mathematical Algorithms)

The `calculations.py` module is the mathematical core of the library, housing universal functions for the numerical calculation and transformation of 2D geometric properties.

---

## 1. `calculate_vertices_sums` (Gauss-Green Method)

This function performs numerical integration for polygons, calculating the **raw geometric sums ($I_0$)** relative to the global origin $(0, 0)$.

### Purpose
It provides accurate calculation of Area ($A$), Static Moments ($S_{x0}, S_{y0}$), and Moments of Inertia ($I_{xx0}, I_{yy0}, I_{xy0}$) for closed polygons. It is used by numerical primitives and complex CSG objects.

### Key Formulas (I_0)
The calculations are based on the Gauss-Green Method.

* **Area ($A$):**
    $$A = \frac{1}{2} \sum (x_i y_{i+1} - x_{i+1} y_i)$$
* **Moment of Inertia ($I_{xx0}$) relative to $(0, 0)$:**
    $$I_{xx, 0} = \frac{1}{12} \sum (y_i^2 + y_i y_{i+1} + y_{i+1}^2) (x_i y_{i+1} - x_{i+1} y_i)$$

---

## 2. `transfer_properties` (Steiner's Theorem)

A universal function for transferring moments of inertia between parallel axes.

### Steiner's Theorem Formula
The general formula is used for transferring moments ($I$) based on area ($A$) and displacement ($d$):
$$I_{\text{new}} = I_{\text{old}} \pm A \cdot d^2$$

### Modes (`reverted` Parameter)
| `reverted` | Mode | Purpose | Formula Used |
| :---: | :--- | :--- | :--- |
| **`False`** | **Direct Transfer** | $I_c \to I_0$. Transfers from the centroid to the origin $(0, 0)$. | $I_{0} = I_{c} + A \cdot d^2$ |
| **`True`** | **Inverse Transfer** | $I_0 \to I_c$. Transfers from the origin $(0, 0)$ to the centroid. | $I_{c} = I_{0} - A \cdot d^2$ |

### Static Moments During Transfer
* **Direct Transfer (`reverted=False`):** Calculates the static moments relative to $(0, 0)$: $S_{x0} = A \cdot c_y$ and $S_{y0} = A \cdot c_x$ (where $c_x = dx, c_y = dy$).
* **Inverse Transfer (`reverted=True`):** Sets static moments to zero, as they are being calculated relative to the centroid.

---

## 3. `calculate_principal_axes` (Principal Moments)

Calculates the **principal moments of inertia** ($I_1, I_2$) and the **angle of rotation** ($\alpha$) for the principal axes using the principles of **Mohr's Circle**.

### Key Concepts
* **Average Moment ($I_{\text{avg}}$):** The center of the circle.
    $$I_{\text{avg}} = \frac{I_{xx}^c + I_{yy}^c}{2.0}$$
* **Radius ($R$):** Used to determine the maximum and minimum moments.
    $$R = \sqrt{\left(\frac{I_{xx}^c - I_{yy}^c}{2.0}\right)^2 + (I_{xy}^c)^2}$$

### Property Calculation
* **Principal Moments:**
    $$I_1 = I_{\text{avg}} + R \quad (\text{Maximum})$$
    $$I_2 = I_{\text{avg}} - R \quad (\text{Minimum})$$
* **Angle of Rotation ($\alpha$):**
    $$\alpha = \frac{1}{2} \arctan \left( \frac{2 I_{xy}^c}{I_{y}^c - I_{x}^c} \right)$$
    *The implementation uses `math.atan2` for robust quadrant handling of the angle*.

---

## 4. `calculate_radii_of_gyration` (Radii of Gyration)

Calculates the radii of gyration ($r_x, r_y, r_1, r_2$) for the cross-section.

### Formula
The radius of gyration ($r$) is calculated from the moment of inertia ($I$) and the area ($A$):
$$r = \sqrt{I / A}$$

### Calculated Radii
* $r_x, r_y$: Radii of gyration relative to the centroidal axes ($I_{xx}^c, I_{yy}^c$).
* $r_1, r_2$: Radii of gyration relative to the principal axes ($I_1, I_2$).