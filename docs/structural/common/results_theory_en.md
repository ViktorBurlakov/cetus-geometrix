# 📚 Theory: Results Reporting (`results.py`)

## 1. Module Purpose
The `results.py` module contains universal **Data Transfer Objects (DTOs)** for standardized reporting of numerical calculation results. The primary class, `ConvergenceReport`, ensures a clear and consistent presentation of solver execution information.

## 2. Convergence Report

### 2.1. Theoretical Background
Most complex engineering problems are solved using **iterative numerical methods**. This means that the calculation is performed step-by-step, repeating computations until sufficient accuracy is achieved.

A **convergence report** is critically important for evaluating the success and efficiency of such a calculation:
* **Convergence**: Did the algorithm reach the desired accuracy? If not, why? (e.g., due to exceeding the maximum number of iterations or method instability).
* **Efficiency**: How many iterations were required? How much time did the calculation take?

### 2.2. Key Report Attributes

| Attribute | Purpose |
| :--- | :--- |
| `iteration_count` | The total number of iterations performed by the solver. |
| `convergence_met` | A boolean value indicating whether the convergence criterion was met within the specified `tolerance` and `max_iter`. |
| `error_message` | A string containing an error message if the calculation did not converge (e.g., "Max iterations exceeded"). |
| `computation_time_s` | The total time spent on the calculation, in seconds. |

This standardized reporting allows easy integration of solvers into larger systems and automation of result verification.