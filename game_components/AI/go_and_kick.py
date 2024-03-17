from game_components.AI.base import GoToPerson, TaskState
from game_components.character.user_character import Character
from game_components.constants import KICK_VELOCITY, FIST_HIT_DAMAGE, DEFAULT_ROTATION_SPEED
from game_components.sounds import play_kick_sound


class GoAndKick(GoToPerson):
    name = 'go_and_kick'

    def tick(self, character: Character, dt: float, time: float, **kwargs) -> TaskState:
        res = super().tick(character=character, dt=dt, time=time)
        if res == self.STATUS.Done:
            kick_direction = -1 if self.target.x < character.x else 1
            self.target.push(horizontal_velocity=kick_direction * KICK_VELOCITY,
                             vertical_velocity=KICK_VELOCITY, rotation_speed=kick_direction * DEFAULT_ROTATION_SPEED)
            self.target.damage(damage=FIST_HIT_DAMAGE, reason=f'копняк від @{character.name}')
            play_kick_sound()

        return res
