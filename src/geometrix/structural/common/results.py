from pydantic import BaseModel, Field


class ConvergenceReport(BaseModel):
    """
    Report on the progress and success of a numerical calculation.

    This report summarizes the outcome of iterative solvers,
    indicating whether the calculation converged, how many iterations were performed,
    and the computation time.

    Attributes:
        iteration_count (int): Number of iterations performed.
        convergence_met (bool): True if convergence was achieved within tolerance and max_iter.
        error_message (str | None): Error message if convergence was not met, otherwise None.
        computation_time_s (float): Total computation time in seconds.
    """
    iteration_count: int = Field(description="Number of iterations performed.")
    convergence_met: bool = Field(description="True if convergence was achieved within tolerance and max_iter.")
    error_message: str | None = Field(None, description="Error message if convergence was not met, otherwise None.")
    computation_time_s: float = Field(description="Total computation time in seconds.")

    class Config:
        frozen = True
