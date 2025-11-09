# 📚 Theory: Progressive Iteration Method (P.I.M.) (`pr_solver.py`)

## 1. Module Purpose
The `pr_solver.py` module contains a concrete implementation of a solver for **modal analysis** of one-dimensional beam-like structures. The `ProgressiveIterationSolver` class utilizes the **Progressive Iteration Method (P.I.M.)**, also known as the Stodola-Vianello or Rayleigh-Ritz iteration method.

This solver is designed to find the **first natural mode** (frequency and shape) for:
* **Bending vibrations** (bending modes).
* **Torsional vibrations** (torsional modes).

## 2. Theoretical Foundations of the Progressive Iteration Method (P.I.M.)

The P.I.M. is an iterative method for determining the lowest natural frequencies, particularly effective for systems with distributed masses and stiffnesses. It is based on the numerical integration of the differential equations of free vibration of an element.

### 2.1. P.I.M. Algorithm

1.  **Initial Approximation of Mode Shape ($f_0$)**:
    * At the beginning of the calculation, an initial mode shape must be assumed. For bending, this could be, for example, the static deflection from a uniformly distributed load. For torsion, it might be a static twist angle. The quality of this approximation influences the convergence rate.

2.  **Hypothesis of Inertial Loading**:
    * In each iteration $k$, the current mode shape $f_{k-1}$ is used to calculate a hypothetical distribution of **inertial loading** ($q_i$):
        $$q_{i, k-1}(z) = \omega_{k-1}^2 \cdot m'(z) \cdot f_{k-1}(z)$$
    * where $\omega_{k-1}^2$ is the squared natural frequency from the previous iteration, and $m'(z)$ is the distributed mass.

3.  **Numerical Integration**:
    * The inertial loading $q_{i, k-1}(z)$ is treated as a static load, and by successive integration (with appropriate boundary conditions), a **new, refined mode shape** $f_k(z)$ is determined.
    * **For bending vibrations**: A four-fold integration is performed:
        $$f_k(z) = \frac{1}{EI(z)} \iiint \int q_{i, k-1}(z) dz dz dz dz$$
    * **For torsional vibrations**: A two-fold integration is performed:
        $$\phi_k(z) = \frac{1}{GJ(z)} \iint m_t(z) dz dz$$
        where $m_t(z)$ is the distributed inertial torque.

4.  **Refinement of Natural Frequency ($\omega_k$)**:
    * The new natural frequency value is usually calculated based on the ratio of the maximum amplitudes of the old and new mode shapes, or through energy relationships (Rayleigh's formula). For example:
        $$\omega_k^2 = \frac{\int m'(z) f_{k-1}(z)^2 dz}{\int m'(z) f_{k-1}(z) f_k(z) dz} \approx \frac{\max(f_{k-1})}{\max(f_k)}$$

5.  **Convergence Check**:
    * The iteration process is repeated until the relative difference between two successive natural frequency values ($\omega_k$ and $\omega_{k-1}$) becomes smaller than the specified `tolerance`.

### 2.2. Application in `ProgressiveIterationSolver`

* The `_run_single_mode` method manages the iterative loop for a single vibration type (bending or torsion).
* The `perform_iteration` method executes a single step of the P.I.M. algorithm (load calculation, integration).
* The `execute` method coordinates the analysis for both vibration types and aggregates the final results.

**Limitations**: P.I.M. typically finds only the **first (lowest)** natural mode for each vibration type. Finding higher modes requires more complex methods (e.g., progressive iteration with deflation or matrix-based methods).