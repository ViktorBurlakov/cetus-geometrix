# geometrix/structural/common/solvers/abstract_solver.py

from abc import ABC, abstractmethod
import numpy as np

# ✅ Залежності від Common моделей, а не від Modal
from geometrix.structural.common.properties import LinearStructureSectionProperties
# AbstractStructuralTask має бути тут або в Common, щоб уникнути циклічної залежності
# або винести її на більш високий рівень.
# Для простоти, припустимо, що ModalAnalysisResults теж є загальним (що не так),
# тому ми повинні зробити AbstractIterativeSolver ТРОХИ БІЛЬШ ЗАГАЛЬНИМ.

# Важлива деталь: AbstractIterativeSolver має повертати AbstractStructuralResults
# (якого у нас ще немає), а не конкретний ModalAnalysisResults.
# Щоб уникнути циклічної залежності:
#  - AbstractStructuralTask (який потребує LinearStructureSectionProperties)
#  - AbstractIterativeSolver (який потребує AbstractStructuralTask)

# Краще AbstractStructuralTask залишити в modal.tasks (або в кожному пакеті задач)
# і зробити AbstractIterativeSolver дженериком, або приймати AbstractStructuralTask
# і повертати AbstractResults.

# Найкраще рішення: AbstractIterativeSolver приймає AbstractStructuralTask і
# повертає просто "Any" або "BaseModel". Конкретний солвер (pr_solver) буде
# уточнювати тип повернення.

from pydantic import BaseModel
from typing import TypeVar, Generic

# Визначаємо TypeVar для типів задач та результатів
TaskType = TypeVar('TaskType', bound=BaseModel)
ResultType = TypeVar('ResultType', bound=BaseModel)


class AbstractIterativeSolver(ABC, Generic[TaskType, ResultType]):
    """
    Абстрактний базовий клас для ітераційних солверів.
    Параметризований типом задачі (TaskType) та типом результату (ResultType).
    """

    def __init__(self,
                 task_context: TaskType):
        self.task_context = task_context

        # Ми не можемо тут прямо звертатися до self.task_context.model_data,
        # self.task_context.max_iter, self.task_context.tolerance,
        # оскільки TaskType - це generic.
        # Тому ці поля повинні бути явно визначені в будь-якому TaskType,
        # який буде використовуватися з цим солвером.
        # Або AbstractIterativeSolver має приймати AbstractStructuralTask (з modal/tasks),
        # що створює залежність від modal.

        # Для цього підходу, AbstractIterativeSolver повинен приймати тільки те,
        # що є абсолютно спільним, або бути абстрактним настільки,
        # щоб concrete солвер міг витягнути дані.

        # Якщо ми хочемо, щоб AbstractIterativeSolver сам витягував дані,
        # то він має залежати від AbstractStructuralTask (який ми щойно перемістили з modal в common)
        # щоб уникнути циклічної залежності (modal.tasks -> common.solvers.abstract_solver -> modal.results)

        # Давайте зробимо AbstractStructuralTask також в common, як базовий для всіх задач
        # Тоді:
        # common.properties
        # common.results
        # common.tasks.abstract_task (новий файл)
        # common.solvers.abstract_solver (залежить від common.tasks.abstract_task)

        # Це найбільш логічний поділ.
        # AbstractStructuralTask буде жити в geometrix/structural/common/tasks/abstract_task.py
        # Або просто geometrix/structural/common/abstract_task.py

        # Для поточного сценарію, де AbstractIterativeSolver ініціалізує self.section_data
        # з task_context.model_data, ми ПОВИННІ мати:
        # task_context: AbstractStructuralTask (з common)
        # та повертати AbstractStructuralResults (з common).
        # Оскільки ModalAnalysisResults не є AbstractStructuralResults,
        # ми зіштовхуємося з типовою проблемою.

        # Пропоную: залишити AbstractStructuralTask там де він є (у modal.tasks),
        # а AbstractIterativeSolver зробити простішим, щоб він не мав жорстких залежностей.
        # Конкретний солвер (pr_solver) буде виконувати витягування.

        # Варіант 1: AbstractIterativeSolver не витягує дані, а лише визначає інтерфейс
        # (що робить його менш корисним для shared logic)

        # Варіант 2: AbstractIterativeSolver залишається в modal/solvers
        # (якщо він специфічний для ітерацій Modal, а не загальних ітерацій)

        # Варіант 3: Створити AbstractStructuralTask в common
        # Це найбільш коректно.

        # Давайте створимо AbstractStructuralTask у `geometrix/structural/common/tasks.py`
        # Це також спростить ModalAnalysisTask, який буде успадковувати з Common.

        # ----- Повторна зміна для оптимізації архітектури -----
        # Якщо AbstractIterativeSolver є загальним, то він має залежати від загальних абстракцій.
        # 1. geometrix/structural/common/properties.py
        # 2. geometrix/structural/common/results.py (ConvergenceReport)
        # 3. geometrix/structural/common/tasks/abstract_task.py (AbstractStructuralTask)
        # 4. geometrix/structural/common/solvers/abstract_solver.py (AbstractIterativeSolver залежить від AbstractStructuralTask)
        # 5. geometrix/modal/tasks.py (ModalAnalysisTask успадковує від AbstractStructuralTask)
        # 6. geometrix/modal/results.py (ModalAnalysisResults)
        # 7. geometrix/modal/solvers/pr_solver.py (успадковує від AbstractIterativeSolver, повертає ModalAnalysisResults)

        # Це виглядає як найбільш логічна іерархія.
        # Спочатку оновимо `geometrix/structural/common/tasks.py` (новий файл).

        # НОВИЙ ІМПОРТ: AbstractStructuralTask буде жити тут
        # from geometrix.structural.common.tasks import AbstractStructuralTask

        # Щоб не створювати циклічну залежність з `results` (ModalAnalysisResults),
        # AbstractIterativeSolver має повертати загальний `BaseModel` або `Any`.
        # Конкретний солвер (PRSolver) буде вказувати конкретний тип повернення.

        # Тут ми приймаємо, що `task_context` має атрибути `model_data`, `max_iter`, `tolerance`.
        # Це вимагає, щоб `TaskType` був сумісним з `AbstractStructuralTask` (з нового common/tasks).

        # Щоб AbstractIterativeSolver був повністю generic і не залежав від конкретних `ModalAnalysisResults`
        # ми зробимо його абстрактним щодо типу результату `ResultType`.

        # Приймаємо, що TaskType має такі атрибути:
        # - model_data: LinearStructureSectionProperties
        # - max_iter: int
        # - tolerance: float

        self.section_data: LinearStructureSectionProperties = task_context.model_data
        self.max_iter: int = task_context.max_iter
        self.tolerance: float = task_context.tolerance

        self.N_SECTIONS: int = self.section_data.section_count
        self.DELTA_Z: float = self.section_data.delta_x

    @abstractmethod
    def perform_iteration(self, *args, **kwargs) -> tuple:
        """
        Виконує одну ітерацію розрахунку.
        Аргументи та повернення будуть специфічними для реалізації.
        """
        pass

    @abstractmethod
    def execute(self) -> ResultType:
        """Запускає ітераційний розрахунок та повертає результат."""
        pass
