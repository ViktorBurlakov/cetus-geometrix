# 📚 Expanded Theory: `centroid.py` (Engineering Significance)

The `centroid.py` module defines the **Centroid** class, which serves as the **final, minimal property set** for a 2D cross-section or 3D solid. It encapsulates all key geometric and inertial properties calculated relative to the body's **Center of Mass (CM)**.

---

## 1. 🎯 Center of Mass (CM) and Static Moments

The field **`center`** ($X_c, Y_c$) defines the CM. This location is mathematically significant because:
* **Minimal Inertia:** Moments of inertia ($I$) are always minimized when calculated with respect to an axis passing through the CM (a consequence of the **Steiner Theorem**).
* **Zero Static Moments:** At the CM, the static moments are zero: $S_x = \int y \cdot dA = 0$ and $S_y = \int x \cdot dA = 0$. This ensures that when calculating bending stresses, the neutral axis automatically coincides with the CM axis.

## 2. 🛡️ Centroidal Inertia Tensor (`inertia`)

The **`inertia`** field holds the minimum, base moments ($I_{xx}^c, I_{yy}^c, I_{xy}^c$) required for all subsequent engineering calculations.

### Application in Mechanics of Materials:
The primary role is in the Euler–Bernoulli bending stress formula:
$$\sigma = \frac{M \cdot y}{I}$$
For this formula to accurately determine maximum normal stresses ($\sigma$) in a beam, the Moment of Inertia ($I$) **must** be the **centroidal moment** ($I_{xx}^c$ or $I_{yy}^c$). Non-centroidal moments cannot be used directly in standard stress formulas.

## 3. 🌀 Principal Moments (`principal_moments`)

This property derives the inherent strength and orientation of the cross-section from the centroidal moments ($I_{xx}^c, I_{yy}^c, I_{xy}^c$) using **Mohr's Circle** principles.

* **$I_1$ (Maximum):** The moment of inertia around the stiffest axis.
* **$I_2$ (Minimum):** The moment of inertia around the weakest axis.
* **$\alpha$ (Angle of Rotation):** The angle required to align the local axes with the Principal Axes.

### Application in Structural Stability (Buckling):
For calculating the **critical buckling load** ($P_{cr}$) on a column (Euler's formula), the moment $I$ must be the **minimum principal moment ($I_2$)**, as the column will always buckle about its weakest axis. 

## 4. ⚖️ Radii of Gyration (`radii_of_gyration`)

The radius of gyration ($r$) is an abstract measure of how effectively the cross-sectional area ($A$) is distributed around an axis to resist bending.

$$\text{Radius of Gyration} \quad r = \sqrt{I / A}$$

### Application in Slenderness Ratio:
The minimum radius of gyration ($r_{min} = r_2$) is essential for calculating the **slenderness ratio** ($\lambda$) of a column:
$$\lambda = \frac{L_{eff}}{r_{min}}$$
This ratio ($\lambda$) dictates the column's behavior (short, intermediate, or long) and directly informs the design against instability, providing an area-independent measure of geometric efficiency.