from typing import Union
from game_components.AI.base import FindTarget, BaseTask, TaskState, IdleWalk, AI
from game_components.AI.go_and_kill import GoAndKill
from game_components.character.user_character import Character
from game_components.character.zombie import Zombie


class DefendFromZombies(BaseTask):
    def __init__(self):
        super().__init__()
        self.find_target_task: FindTarget = FindTarget(filter_func=lambda z: isinstance(z, Zombie))
        self.current_task: Union[GoAndKill, FindTarget] = self.find_target_task

    def tick(self, character: Character, dt: float, time: float, ai: AI, **kwargs) -> TaskState:
        tick_res = self.current_task.tick(character=character, dt=dt, time=time, ai=ai, **kwargs)
        if isinstance(self.current_task, FindTarget):
            if tick_res == self.STATUS.Failed:
                ai.add_task(IdleWalk())
                return self.STATUS.Done
            else:
                self.set_timeout(self.get_random_time())
                self.current_task = GoAndKill(target=self.current_task.found_target)
                return self.STATUS.InProgress

        elif isinstance(self.current_task, GoAndKill):
            if tick_res != self.STATUS.InProgress or self.is_time_out:
                self.current_task = self.find_target_task
                return self.STATUS.InProgress

        else:
            return self.STATUS.Done
