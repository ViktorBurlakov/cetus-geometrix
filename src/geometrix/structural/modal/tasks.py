from pydantic import Field
import numpy as np

from geometrix.structural.common.tasks.abstract_task import AbstractStructuralTask


class ModalAnalysisTask(AbstractStructuralTask):
    """
    Контекст вхідних даних для задачі розрахунку власних частот
    методом послідовних наближень.
    Успадковує model_data, max_iter, tolerance від AbstractStructuralTask.
    """
    initial_bending_f0: np.ndarray = Field(
        description="Початкове наближення форми коливань для згину."
    )
    initial_torsion_phi0: np.ndarray = Field(
        description="Початкове наближення форми коливань для кручення."
    )

    class Config(AbstractStructuralTask.Config): # Важливо успадкувати конфігурацію
        pass