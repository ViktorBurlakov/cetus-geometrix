from pydantic import BaseModel, Field

class ConvergenceReport(BaseModel):
    """
    Звіт про хід та успішність чисельного розрахунку.
    """
    iteration_count: int = Field(description="Кількість виконаних ітерацій.")
    convergence_met: bool = Field(description="Чи досягнута збіжність розрахунку.")
    error_message: str = Field("", description="Повідомлення про помилку, якщо збіжність не досягнута.")
    computation_time_s: float = Field(0.0, description="Час обчислення в секундах.")

    class Config:
        frozen = True
