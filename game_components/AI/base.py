import enum
from abc import abstractmethod
import random
from math import dist
from typing import List, Optional, Callable, Union
from game_components.character.user_character import Character
from game_components.screen import scaled_w, SCREEN_H
from game_components.constants import PosType
from game_components.global_data import GlobalData
from logger import LOGGER


class TaskState(enum.Enum):
    Done = 'done'
    InProgress = 'in_progress'
    Failed = 'failed'


class BaseTask:
    global_data: GlobalData = GlobalData()
    name: str
    verbal_name: str
    STATUS: TaskState = TaskState
    is_blocking: bool = False
    endless: bool = False
    skippable: bool = True

    def __init__(self, timeout: Optional[float] = None):
        self.timeout: Optional[float] = timeout

    @property
    def is_time_out(self) -> float:
        return True if self.timeout is None else self.global_data.time > self.timeout

    def set_timeout(self, time: float) -> None:
        self.timeout = self.global_data.time + time

    @abstractmethod
    def tick(self, character: Character, dt: float, time: float, game_obj, ai: 'BaseAI', **kwargs) -> TaskState:
        raise NotImplementedError

    @staticmethod
    def get_random_time(min_t: int = 5, max_t: int = 10) -> int:
        return random.randint(min_t, max_t)


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

    def default_update(self, dt: float, time: float, game_obj, *_, **__) -> Optional[TaskState]:
        if self.tasks_queue:
            tick_result = self.current_task.tick(character=self.character, dt=dt, time=time, game_obj=game_obj, ai=self)
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
        super().__init__()
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

    def __init__(self, stop_on_timeout: bool = False):
        super().__init__(timeout=self.get_random_time())
        self.subtask: Union[GoTo, DoNothing] = GoTo.get_random_go_to_task()
        self.stop_on_timeout: bool = stop_on_timeout

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        tick_res = self.subtask.tick(character=character, dt=dt, time=time)

        if self.is_time_out and self.stop_on_timeout:
            return self.STATUS.Done

        if tick_res == TaskState.Done or self.is_time_out:
            LOGGER.debug(f'Task {self.name} for {character.name} finished'
                         f'({"timeout" if self.timeout < time else "done"})')

            self.set_timeout(self.get_random_time())
            if random.random():
                self.subtask: GoTo = GoTo.get_random_go_to_task()
            else:
                self.subtask: DoNothing = DoNothing()

        elif tick_res == TaskState.Failed:
            return TaskState.Failed

        return TaskState.InProgress


class DoNothing(BaseTask):
    name = 'do_nothing'

    def __init__(self):
        super().__init__(timeout=self.get_random_time())

    def tick(self, character: Character, dt: float, time: float, game_obj, ai: 'BaseAI', **kwargs) -> TaskState:
        if self.is_time_out:
            return TaskState.Done
        else:
            return TaskState.InProgress


class GoToPerson(GoTo):
    name = 'got_to_person'

    def __init__(self, target: Character, wait_for_flying_person: bool = True):
        self.wait_for_flying_person: bool = wait_for_flying_person
        self.target: Character = target
        super().__init__(tuple(target.position))

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        self.position = self.target.get_center()
        if self.target.dead:
            character.stop()
            return TaskState.Failed

        elif character.rect.colliderect(self.target.rect):
            character.stop()
            LOGGER.debug(f'{character.name} finished task {self.name} with target {self.target.name}')
            return TaskState.Done

        elif character.rect.x < self.target.get_center()[0] < character.rect.right:
            if self.wait_for_flying_person:
                character.stop()
                return TaskState.InProgress
            else:
                return TaskState.Failed

        res = super().tick(character=character, dt=dt, time=time)
        if res == TaskState.Done:
            LOGGER.debug(f'{character.name} finished task {self.name} with target {self.target.name}')
        return res


class FindTarget(BaseTask):
    name = 'find_target'

    def __init__(self, filter_func: Callable):
        super().__init__()
        self.filter_func: Callable = filter_func
        self.found_target: Character = None

    def tick(self, character: Character, dt: float, time: float, game_obj, **kwargs) -> TaskState:
        targets: List[Character] = list(filter(self.filter_func, game_obj.characters.values()))
        if targets:
            self.found_target = min(targets, key=lambda t: dist(character.position, t.position))
            return TaskState.Done

        else:
            return TaskState.Failed
