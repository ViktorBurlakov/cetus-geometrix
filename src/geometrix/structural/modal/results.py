from pydantic import BaseModel, Field
import pandas as pd
from typing import List

from geometrix.structural.common.results import ConvergenceReport


class ModeShapeData(BaseModel):
    """Дані про форму коливань для одного власного тону."""
    mode_number: int = Field(description="Номер власного тону.")
    df_mode_shape: pd.DataFrame = Field(description="DataFrame з координатами Z та амплітудами форми коливань.")

    class Config:
        arbitrary_types_allowed = True
        frozen = True


class ModalFrequencyResult(BaseModel):
    """Результати власної частоти для одного власного тону."""
    mode_number: int = Field(description="Номер власного тону.")
    frequency_rad_s: float = Field(description="Власна частота в радіанах/секунду.")
    frequency_hz: float = Field(description="Власна частота в Герцах.")

    class Config:
        frozen = True


class ModalAnalysisResults(BaseModel):
    """Агреговані результати модального аналізу."""
    report: ConvergenceReport = Field(description="Звіт про збіжність розрахунку (зазвичай для першого режиму).")
    frequencies: List[ModalFrequencyResult] = Field(description="Список обчислених власних частот.")
    mode_shapes: List[ModeShapeData] = Field(description="Список обчислених форм коливань.")

    class Config:
        frozen = True
