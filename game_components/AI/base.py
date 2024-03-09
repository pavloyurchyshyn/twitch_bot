import enum
from abc import abstractmethod
import random
from math import dist
from typing import List, Optional, Callable
from game_components.character.user_character import Character
from game_components.screen import scaled_w, SCREEN_H
from game_components.constants import PosType
from logger import LOGGER


class TaskState(enum.Enum):
    Done = 'done'
    InProgress = 'in_progress'
    Failed = 'failed'


class BaseTask:
    name: str
    verbal_name: str
    STATUS: TaskState = TaskState
    is_blocking: bool = False
    endless: bool = False
    skippable: bool = True

    @abstractmethod
    def tick(self, character: Character, dt: float, time: float, game_obj, **kwargs) -> TaskState:
        raise NotImplementedError
    # TODO think about it
    # @abstractmethod
    # def get_dict(self) -> dict:
    #     raise NotImplementedError
    #
    # @abstractmethod
    # def load(self, save: dict) -> None:
    #     raise NotImplementedError


class BaseAI:
    def __init__(self, character: Character):
        self.character: Character = character
        self.tasks_queue: List[BaseTask] = []

    def run_idle_walking(self):
        self.add_task(IdleWalk())

    def add_task(self, task: BaseTask) -> None:
        self.tasks_queue.append(task)

    @abstractmethod
    def update(self, dt: float, time: float, game_obj) -> None:
        raise NotImplementedError

    def default_update(self, dt: float, time: float, game_obj) -> Optional[TaskState]:
        if self.tasks_queue:
            tick_result = self.current_task.tick(character=self.character, dt=dt, time=time, game_obj=game_obj)
            if tick_result in (TaskState.Done, TaskState.Failed):
                self.finish_current_task()

            return tick_result

    def finish_current_task(self):
        if self.tasks_queue:
            self.tasks_queue.pop(0)

    def clear(self):
        return self.tasks_queue.clear()

    @property
    def current_task(self) -> Optional[BaseTask]:
        if self.tasks_queue:
            return self.tasks_queue[0]
        else:
            return None


class AI(BaseAI):
    def update(self, dt: float, time: float, game_obj) -> None:
        return self.default_update(dt=dt, time=time, game_obj=game_obj)


class GoTo(BaseTask):
    name = 'go_to'

    def __init__(self, position: PosType, look_direction: Optional[int] = None):
        self.position: PosType = position
        self.look_direction: Optional[int] = look_direction

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        if not character.is_falling:
            if self.position[0] == character.position[0]:
                character.move_direction = 0
            else:
                character.move_direction = -1 if self.position[0] < character.position[0] else 1
            if character.rect.collidepoint(*self.position):
                LOGGER.debug(f'Walking for {character.name} to {self.position} is done.')
                character.stop()
                if self.look_direction is not None:
                    character.set_look_direction(self.look_direction)
                return TaskState.Done

        return TaskState.InProgress

    @staticmethod
    def get_random_go_to_task() -> 'GoTo':
        # TODO fix numbers
        return GoTo((scaled_w(random.uniform(0.05, 0.95)), SCREEN_H - 5))


class IdleWalk(BaseTask):
    endless = True
    name = 'idle_walk'

    def __init__(self):
        self.subtask: GoTo = None
        self.timeout: float = None

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        if self.timeout is None:
            self.timeout = time + random.randint(3, 10)
            self.subtask = GoTo.get_random_go_to_task()

        tick_res = self.subtask.tick(character=character, dt=dt, time=time)

        # TODO make one if
        if tick_res == TaskState.Done or self.timeout < time:
            LOGGER.debug(f'Task {self.name} for {character.name} finished'
                         f'({"timeout" if self.timeout < time else "done"})')
            self.timeout = None
        elif tick_res == TaskState.Failed:
            return TaskState.Failed

        return TaskState.InProgress


class GoToPerson(GoTo):
    name = 'got_to_person'

    def __init__(self, target: Character, wait_for_flying_person: bool = True):
        self.wait_for_flying_person: bool = wait_for_flying_person
        self.target: Character = target
        super().__init__(tuple(target.position))

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        self.position = self.target.position
        if self.target.dead:
            character.stop()
            return TaskState.Failed
        elif self.target.rect.colliderect(character.rect):
            character.stop()
            return TaskState.Done
        elif self.target.rect.bottom < character.rect.y - character.h_size and not self.wait_for_flying_person:
            return TaskState.Failed

        res = super().tick(character=character, dt=dt, time=time)
        if res == TaskState.Done:
            LOGGER.debug(f'{character.name} finished task {self.name} with target {self.target.name}')
        return res


class FindTarget(BaseTask):
    name = 'find_target'

    def __init__(self, filter_func: Callable):
        self.filter_func: Callable = filter_func
        self.found_target: Character = None

    def tick(self, character: Character, dt: float, time: float, game_obj, **kwargs) -> TaskState:
        targets: List[Character] = list(filter(self.filter_func, game_obj.characters.values()))
        if targets:
            self.found_target = min(targets, key=lambda t: dist(character.position, t.position))
            return TaskState.Done

        else:
            return TaskState.Failed
