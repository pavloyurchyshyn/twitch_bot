from typing import Dict, Callable
from game_components.events.base import BaseEvent
from game_components.events.prediction_mixin import EventPredictionMixin
from game_components.events.title import TitleEvent
from game_components.character.user_character import Character
from game_components.AI.base import AI
from game_components.character.zombie import Zombie
from logger import LOGGER

from game_components.AI.defend_from_zombies import DefendFromZombies
from game_components.character.zombie import add_zombie


class ZombieEvent(BaseEvent, EventPredictionMixin):
    name = 'zombies_event'
    is_blocking = True

    class Const:
        Users = 'Люди'
        Zombie = 'Зомбі'
        time_to_predict = 60

    def __init__(self, characters_dict: Dict[str, Character],
                 characters_ai: Dict[str, AI],
                 update_prediction: Callable):
        super().__init__(characters_dict=characters_dict, characters_ai=characters_ai)
        EventPredictionMixin.__init__(self, update_method=update_prediction)
        self.prediction_time = self.global_data.time + self.Const.time_to_predict
        self.update_method: Callable = self.wait_time

    def update(self, dt: float, time: float) -> None:
        self.update_method()

    def wait_time(self):
        if self.global_data.time > self.prediction_time:
            self.update_method = self.fight_time
            self.lock_prediction()

            for ai in self.characters_ai.values():
                ai.clear()
                ai.add_task(DefendFromZombies())

            users_number = len(tuple(filter(lambda c: c.is_player, self.characters))) // 3
            if users_number == 0:
                users_number = 1

            from game_components.game import Game
            game_obj = Game()
            for i in range(users_number):
                pos = self.global_data.get_random_spawn_position()
                add_zombie(name=f'patient_{i}', position=pos, game_obj=game_obj)

            LOGGER.info('Started zombies fight')

    def fight_time(self):
        any_not_zombie = False
        any_zombie = False
        for char in self.characters:
            if isinstance(char, Zombie):
                any_zombie = True
            else:
                any_not_zombie = True

        if not (any_zombie and any_not_zombie):
            self.finish()
            LOGGER.info('Zombies event finished')

            if any_zombie and not any_not_zombie:
                self.end_prediction(winner=self.Const.Zombie)
                for char in self.characters:
                    if isinstance(char, Zombie):
                        char.enable_destruction()

            elif any_not_zombie and not any_zombie:
                self.end_prediction(winner=self.Const.Users)
            else:
                self.cancel_prediction()

    def draw(self) -> None:
        pass

