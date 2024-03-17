import random
from pygame import Color
from uuid import uuid1
from game_components.character.user_character import Character
from game_components.constants import PosType, DEFAULT_HP, MOVE_SPEED
from game_components.weapon.fist import Fists
from game_components.AI.base import BaseAI, FindTarget, TaskState, GoTo, IdleWalk
from game_components.AI.go_and_kill import GoAndKill


class Zombie(Character):
    def __init__(self, position: PosType, kind: str = 'cat', name='zombie'):
        super().__init__(position=position,
                         kind=kind,
                         make_ghost=False, is_player=False,
                         name=name,
                         max_health_points=DEFAULT_HP * 2,
                         speed=MOVE_SPEED * 1.2,
                         body_color=Color(200, 200, 250), eyes_color=Color('red'),
                         weapon=Fists(position))
        self.destruction_enabled: bool = False
        self.__destruction_damage = self.max_health_points / random.randrange(5, 10)

    def update(self, dt: float, time: float):
        super().update(dt=dt, time=time)

        if self.destruction_enabled:
            self.damage(dt * self.__destruction_damage)

    def enable_destruction(self):
        self.destruction_enabled = True


class ZombieAI(BaseAI):
    GO_AND_KILL_TIME = 5
    WALK_TIME = 10

    def __init__(self, zombie: Zombie):
        super().__init__(character=zombie)
        self.go_and_kill_timeout: float = 0
        self.walk_timeout: float = 10

    def update(self, dt: float, time: float, game_obj) -> None:
        tick_result = None
        if self.tasks_queue:
            tick_result = self.current_task.tick(character=self.character, dt=dt, time=time, game_obj=game_obj, ai=self)
        else:
            self.add_task(self.get_find_target_zombie_task())

        if isinstance(self.current_task, FindTarget):
            if tick_result == TaskState.Done:
                self.add_task(GoAndKill(self.current_task.found_target))
                self.go_and_kill_timeout = time + self.GO_AND_KILL_TIME
                self.finish_current_task()

            elif tick_result == TaskState.Failed:
                self.clear()
                self.add_task(IdleWalk(stop_on_timeout=True))
                self.add_task(self.get_find_target_zombie_task())

        elif isinstance(self.current_task, GoTo):
            if tick_result == TaskState.Done or time > self.walk_timeout:
                self.finish_current_task()

        elif isinstance(self.current_task, GoAndKill):  # kill task
            current_task: GoAndKill = self.current_task

            if tick_result == TaskState.Done:
                add_zombie(name=f'{current_task.target.name}_zom',
                           position=current_task.target.position,
                           game_obj=game_obj,
                           kind=current_task.target.kind)
                self.clear()
            elif tick_result == TaskState.Failed:
                self.clear()

            elif self.go_and_kill_timeout < time:
                self.clear()
                self.add_task(self.get_find_target_zombie_task())

    @staticmethod
    def get_find_target_zombie_task() -> FindTarget:
        return FindTarget(filter_func=lambda target: not isinstance(target, Zombie) and target.alive)


def add_zombie(name: str, position: PosType, game_obj, kind: str = 'cat'):
    zombie_id: str = str(uuid1())
    zombie = Zombie(name=name, position=position, kind=kind)
    game_obj.characters[zombie_id] = zombie
    game_obj.characters_AI[zombie_id] = ZombieAI(zombie=zombie)
