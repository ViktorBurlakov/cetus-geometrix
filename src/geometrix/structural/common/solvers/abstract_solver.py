from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel

from geometrix.structural.common.tasks.abstract_task import AbstractStructuralTask
from geometrix.structural.common.properties import LinearStructureSectionProperties


TaskType = TypeVar('TaskType', bound=AbstractStructuralTask)
ResultType = TypeVar('ResultType', bound=BaseModel) # Using BaseModel as a generic base for results


class AbstractIterativeSolver(ABC, Generic[TaskType, ResultType]):
    """
    Abstract base class for all iterative numerical solvers.

    This class defines a unified interface for launching calculations (`execute`)
    and encapsulates common attributes extracted from the task context, such as
    model data, maximum iterations, and convergence tolerance.

    It implements the Strategy pattern, where the solver (strategy) processes
    a specific task (context) to produce results.

    Attributes:
        task_context (TaskType): The task object containing input data and solver parameters.
        section_data (LinearStructureSectionProperties): Distributed structural properties of the model,
                                                          extracted from `task_context.model_data`.
        max_iter (int): Maximum number of iterations for the solver, from `task_context.max_iter`.
        tolerance (float): Relative error tolerance for convergence, from `task_context.tolerance`.
    """
    def __init__(self, task_context: TaskType):
        self.task_context: TaskType = task_context
        self.section_data: LinearStructureSectionProperties = task_context.model_data
        self.max_iter: int = task_context.max_iter
        self.tolerance: float = task_context.tolerance

    @abstractmethod
    def perform_iteration(self, *args, **kwargs) -> tuple:
        """
        Abstract method to perform a single step of the numerical iterative calculation.

        Subclasses must implement this method to define the core iterative logic
        of their specific numerical algorithm.

        Returns:
            tuple: A tuple containing the updated state variables and the current
                   error/change for convergence check. The exact content depends
                   on the specific solver implementation.
        """
        pass

    @abstractmethod
    def execute(self) -> ResultType:
        """
        Abstract method to run the full calculation cycle and return the final result.

        This method orchestrates the iterative process, applies convergence checks,
        and constructs the final result object.

        Returns:
            ResultType: An object encapsulating all the results of the calculation.
        """
        pass
