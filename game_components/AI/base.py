from abc import abstractmethod
from typing import List, Sequence
import enum


class State(enum.Enum):
    Done = 'done'
    InProgress = 'in_progress'
    Failed = 'failed'


class BaseTask:
    name: str
    STATES: State = State

    @abstractmethod
    def tick(self, character, dt: float, time: float) -> State:
        raise NotImplementedError

    @abstractmethod
    def get_dict(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def load(self, save: dict) -> None:
        raise NotImplementedError


class AI:
    # TODO use character ABC
    def __init__(self):
        self.tasks_queue: List[BaseTask] = []

    def add_task(self, task: BaseTask) -> None:
        self.tasks_queue.append(task)

    def update(self, character, dt: float, time: float) -> None:
        if self.tasks_queue:
            current_task = self.tasks_queue[0]
            tick_result = current_task.tick(character=character, dt=dt, time=time)
            if tick_result in (State.Done, State.Failed):
                self.tasks_queue.pop(0)


class GoTo(BaseTask):
    name = 'go_to'

    def tick(self, character, dt: float, time: float) -> State:
        pass
