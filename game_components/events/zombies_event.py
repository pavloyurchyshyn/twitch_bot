from typing import Dict, Callable

from game_components.events.base import BaseEvent
from game_components.events.title import TitleEvent
from game_components.events.prediction_mixin import EventPredictionMixin
from game_components.screen import scaled_w
from game_components.constants import KICK_VELOCITY, HOOK_VELOCITY
from game_components.AI.base import AI
from game_components.AI.defend_from_zombies import DefendFromZombies

from game_components.character.user_character import Character
from game_components.character.zombie import Zombie, add_zombie

from logger import LOGGER

LEFT_BORDER = scaled_w(0.01)
RIGHT_BORDER = scaled_w(0.99)


class ZombieEvent(BaseEvent, EventPredictionMixin):
    name = 'zombies_event'
    is_blocking = True
    process_user_spawn = True

    class Const:
        Users = 'Люди'
        Zombie = 'Зомбі'
        time_to_predict = 60
        time_to_fight = 90

    def __init__(self, characters_dict: Dict[str, Character],
                 characters_ai: Dict[str, AI],
                 update_prediction: Callable):
        super().__init__(characters_dict=characters_dict, characters_ai=characters_ai)
        EventPredictionMixin.__init__(self, update_method=update_prediction)
        self.fight_stage: bool = False
        self.prediction_time = self.global_data.time + self.Const.time_to_predict
        self.time_to_fight = self.prediction_time + self.Const.time_to_fight
        self.update_method: Callable = self.wait_time

    def update(self, dt: float, time: float) -> None:
        self.update_method()

    def wait_time(self):
        if self.global_data.time > self.prediction_time:
            self.fight_stage = True
            self.update_method = self.fight_time
            self.lock_prediction()

            for ai in self.characters_ai.values():
                ai.clear()
                ai.add_task(DefendFromZombies())

            users_number = len(tuple(filter(lambda c: c.is_player, self.characters))) // 2
            if users_number == 0:
                users_number = 1

            from game_components.game import Game
            game_obj: Game = Game()
            for i in range(users_number):
                pos = self.global_data.get_random_spawn_position()
                add_zombie(position=pos, game_obj=game_obj)
            game_obj.add_event(TitleEvent(text='Survive for', event_to_follow=self,
                                          timeout=self.Const.time_to_fight, draw_time=True))
            LOGGER.info('Started zombies fight')

    def process_new_user(self, character: Character):
        if self.fight_stage:
            ai = self.characters_ai.get(character.name)
            if ai:
                ai.clear()
                ai.add_task(DefendFromZombies())

    def fight_time(self):
        any_not_zombie = False
        any_zombie = False
        for char in self.characters:
            if isinstance(char, Zombie):
                any_zombie = True
                if self.time_to_fight < self.global_data.time:
                    char.enable_destruction()
            else:
                any_not_zombie = True

            if char.x < LEFT_BORDER:
                char.push(horizontal_velocity=KICK_VELOCITY, vertical_velocity=HOOK_VELOCITY)
            elif char.rect.right > RIGHT_BORDER:
                char.push(horizontal_velocity=-KICK_VELOCITY, vertical_velocity=HOOK_VELOCITY)

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
        if self.time_to_fight < self.global_data.time:
            self.time_to_fight += float('inf')

    def draw(self) -> None:
        pass
