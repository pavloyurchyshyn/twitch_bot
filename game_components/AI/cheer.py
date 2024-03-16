import random
from game_components.AI.base import BaseTask, TaskState
from game_components.character.user_character import Character
from game_components.constants import JUMP_VELOCITY
from game_components.events.base import BaseEvent


class Cheer(BaseTask):
    name = 'cheer'
    endless = True

    def __init__(self, event_to_follow: BaseEvent, direction_to_look: int = 1):
        super().__init__()
        self.event_to_follow: BaseEvent = event_to_follow
        self.direction_to_look: int = direction_to_look
        self.jump_cd: int = 0

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        character.set_look_direction(self.direction_to_look)

        if not character.is_falling and self.jump_cd < time:
            character.push(vertical_velocity=JUMP_VELOCITY * random.uniform(0.1, 1),
                           horizontal_velocity=random.randint(-5, 5))

        elif character.is_falling and self.jump_cd < time:
            self.jump_cd = time + random.randint(0, 5)

        if self.event_to_follow.is_done:
            return TaskState.Done
        else:
            return TaskState.InProgress
