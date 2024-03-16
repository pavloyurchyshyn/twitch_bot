from typing import Union
from game_components.AI.base import GoToPerson, TaskState, BaseTask
from game_components.character.user_character import Character
from game_components.weapon.fist import Fists


class HitWithFist(BaseTask):
    name = 'hit_with_fist'

    def __init__(self, target: Character):
        super().__init__()
        self.target: Character = target

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        if not isinstance(character.weapon, Fists):
            return self.STATUS.Failed  # unknown weapon

        if character.weapon.ready_to_use:
            if character.rect.colliderect(self.target.rect):
                character.weapon.use(character=character, target=self.target)
                return self.STATUS.Done  # made kick
            else:
                return self.STATUS.Failed  # can`t make hit
        else:
            return self.STATUS.Failed  # on cooldown


class GoAndKill(BaseTask):
    name = 'go_and_kill'

    def __init__(self, target: Character):
        super().__init__()
        self.target: Character = target
        self.go_to_task: GoToPerson = GoToPerson(target=target, wait_for_flying_person=True)
        self.hit_task: HitWithFist = HitWithFist(target=target)
        self.current_task: Union[GoToPerson, HitWithFist] = self.go_to_task

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        if self.target.dead:
            return self.STATUS.Failed

        res = self.current_task.tick(character=character, dt=dt, time=time)
        if self.current_task == self.go_to_task:
            if res == TaskState.Done:
                self.current_task = self.hit_task

        elif self.current_task == self.hit_task:
            if res == self.STATUS.Failed:
                self.current_task = self.go_to_task

            elif res == self.STATUS.Done:
                return self.STATUS.Done if self.target.dead else self.STATUS.InProgress

        return TaskState.InProgress
