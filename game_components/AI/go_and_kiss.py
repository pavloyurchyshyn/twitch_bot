from game_components.AI.base import GoToPerson, TaskState
from game_components.character.user_character import Character
from game_components.game import Game
from game_components.events.flying_heart import FlyingHeart


class GoAndKiss(GoToPerson):
    name = 'go_and_kiss'

    def tick(self, character: Character, dt: float, time: float, game_obj: Game, **kwargs) -> TaskState:
        res = super().tick(character=character, dt=dt, time=time)
        if res == self.STATUS.Done:
            game_obj.add_event(FlyingHeart(self.target.get_rect().topleft))
            game_obj.add_event(FlyingHeart(character.get_rect().topleft))

        return res
