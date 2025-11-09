from pydantic import BaseModel, Field
from abc import ABC

from geometrix.structural.common.properties import LinearStructureSectionProperties


class AbstractStructuralTask(ABC, BaseModel):
    """
    Абстрактний базовий клас для всіх інженерних задач (Task Context).
    Визначає спільні атрибути, які потрібні солверам.
    """
    model_data: LinearStructureSectionProperties = Field(
        description="Розподілені структурні властивості елемента."
    )
    max_iter: int = Field(
        default=15, ge=1, description="Максимальна кількість ітерацій для солвера."
    )
    tolerance: float = Field(
        default=0.005, gt=0, description="Відносна похибка збіжності для солвера."
    )

    class Config:
        arbitrary_types_allowed = True
        frozen = True
