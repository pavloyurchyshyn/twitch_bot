from game_components.AI.base import GoToPerson, TaskState
from game_components.character.user_character import Character
from game_components.constants import KICK_VELOCITY
from game_components.game import Game
from game_components.sounds import play_kick_sound


class GoAndKick(GoToPerson):
    name = 'go_and_kick'

    def tick(self, character: Character, dt: float, time: float, game_obj: Game, **kwargs) -> TaskState:
        res = super().tick(character=character, dt=dt, time=time)
        if res == self.STATUS.Done:
            kick_direction = -1 if self.target.position[0] < character.position[0] else 1
            self.target.horizontal_velocity = kick_direction * KICK_VELOCITY
            self.target.vertical_velocity -= KICK_VELOCITY
            play_kick_sound()

        return res
