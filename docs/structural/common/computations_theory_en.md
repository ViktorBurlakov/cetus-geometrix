# 📚 Theory: Common Direct Computations (`computations.py` or `formulas.py`)

## 1. Module Purpose and Terminology Correction
The **`computations.py`** module (formerly `solvers.py`) contains a **set of utility functions for direct computation**.

Unlike "solvers" (which use complex iterative methods to find approximate solutions), the functions in this module perform **direct, closed-form** mathematical operations. They serve as intermediate steps necessary for preparing data for more complex solvers.

### ⚠️ Distinction: Computation vs. Solver
| Term | Description | Example Functionality |
| :--- | :--- | :--- |
| **Computation** | Direct application of a formula. The result is achieved in a single step. | `calculate_total_mass`, `calculate_stiffness` |
| **Solver** | An iterative or numerical algorithm. The result is achieved over multiple steps (iterations) with convergence control. | `ProgressiveIterationSolver` (for modal analysis) |

## 2. Theoretical Background: Stiffness and Mass Calculations

The functions in this module apply basic principles from mechanics of materials and structural mechanics.

### 2.1. Calculation of Stiffness Characteristics (`calculate_stiffness`)
The stiffness of an element describes its resistance to deformation. It is calculated based on material properties (Young's Modulus $E$, Shear Modulus $G$) and geometric characteristics of the cross-section ($A$, $I$, $J$).

* **Bending Stiffness ($EI$)**: $$EI = E \cdot I$$
* **Torsional Stiffness ($GJ$)**: $$GJ = G \cdot J$$
* **Axial Stiffness ($EA$)**: $$EA = E \cdot A$$
* **Shear Stiffness ($GA_{shear}$)**: $$GA_{shear} = G \cdot A_{shear}$$

### 2.2. Calculation of Total Mass (`calculate_total_mass`)
* **Mass ($M$)**: $$M = \rho \cdot V$$
    where $\rho$ is the material density, and $V$ is the element volume.