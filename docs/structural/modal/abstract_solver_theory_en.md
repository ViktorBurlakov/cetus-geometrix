# 📚 Theory: Abstract Iterative Solver (`abstract_solver.py`)

## 1. Purpose and Architectural Pattern
The `abstract_solver.py` module defines the **abstract base class `AbstractIterativeSolver`**. This class is the cornerstone for all numerical solvers in the project that use an iterative approach to find a solution.

It implements the **Strategy pattern** within the **Task-Solver-Results** architecture:
* The **Solver** (as a strategy) encapsulates *how* to solve the problem.
* It takes a **Task** (as context), which defines *what* to solve.
* The Solver returns **Results**.

The abstract class provides a unified interface for launching calculations (`execute`) and defines common attributes (task parameters) that are necessary for any iterative method.

## 2. Generics and Flexibility
The `AbstractIterativeSolver` class is **generic** (`Generic[TaskType, ResultType]`). This means it can work with different types of tasks (`TaskType`) and return different types of results (`ResultType`), provided they meet certain basic requirements:
* `TaskType` must be compatible with `AbstractStructuralTask`.
* `ResultType` must be compatible with `BaseModel` (to ensure structured results).

This ensures high flexibility and code reusability for various engineering problems.

## 3. Key Attributes and Abstract Methods

### 3.1. Attributes (Initialization)

| Attribute | Purpose | Source |
| :--- | :--- | :--- |
| `task_context` | An object containing all input data and parameters specific to the current task. | Provided during solver instantiation. |
| `section_data` | Discretized structural properties of the element (mass, stiffness) necessary for calculation. | Extracted from `task_context.model_data`. |
| `max_iter` | The maximum number of iterations allowed for the solver. | Extracted from `task_context.max_iter`. |
| `tolerance` | The convergence criterion, defining the required accuracy of the result. | Extracted from `task_context.tolerance`. |

### 3.2. Abstract Methods (For Implementation in Subclasses)

| Method | Purpose |
| :--- | :--- |
| `perform_iteration(*args, **kwargs) -> tuple` | **Must be implemented**. This method is responsible for executing **a single step** of the iterative algorithm. Subclasses must define the specific computational logic for each iteration. Returns the updated state and an error metric. |
| `execute() -> ResultType` | **Must be implemented**. This method manages the **full calculation cycle**: it initiates iterations, checks convergence conditions, and constructs the final results object. |

This structure allows for the creation of various solvers, each implementing its unique numerical method, but all adhering to a common interface and processing data in a standardized way.