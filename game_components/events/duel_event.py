from math import dist
from typing import List, Optional, Dict, Callable
from twitchAPI.type import PredictionStatus
from pygame import Surface

from logger import LOGGER
from game_components.events.base import BaseEvent
from game_components.character.user_character import Character
from game_components.AI.base import AI, GoTo, IdleWalk
from game_components.AI.go_and_kill import GoAndKill
from game_components.screen import scaled_w, SCREEN_H, MAIN_DISPLAY
from game_components.utils import DEFAULT_FONT, load_image, add_outline_to_image
from game_components.sounds import play_sound


PREPARE_TIME = 60
DUEL_TIME = 45
BATTLE_HORN_SOUND = 'battle_horn.mp3'
try:
    FLAG_IMG: Surface = load_image('flag.png', size=(50, 150))
except Exception:
    FLAG_IMG: Optional[Surface] = None


class DuelEvent(BaseEvent):
    name = 'duel'
    is_blocking = True
    behind = True

    def __init__(self, duelist_1: Character, duelist_2: Character,
                 characters_list: List[Character], characters_ai: Dict[str, AI],
                 update_prediction: Callable):
        super().__init__(characters_list=characters_list, characters_ai=characters_ai)
        self.update_prediction: Callable = update_prediction

        self.duelist_1: Character = duelist_1
        self.duelist_1_ai = self.characters_ai[self.duelist_1.name]
        self.duelist_1.restore_hp()

        self.duelist_2: Character = duelist_2
        self.duelist_2_ai = self.characters_ai[self.duelist_2.name]
        self.duelist_2.restore_hp()

        duelist_pos_left = (scaled_w(0.25), SCREEN_H - 5)
        duelist_pos_right = (scaled_w(0.75), SCREEN_H - 5)
        if FLAG_IMG:
            self.flag_1_pos = duelist_pos_left[0], SCREEN_H - FLAG_IMG.get_height()
            self.flag_2_pos = duelist_pos_right[0], SCREEN_H - FLAG_IMG.get_height()
        else:
            self.flag_1_pos = self.flag_2_pos = None

        self.duelist_1_ai.clear()
        self.duelist_2_ai.clear()

        if dist(self.duelist_1.position, duelist_pos_left) < dist(self.duelist_2.position, duelist_pos_left):
            self.duelist_1_pos = duelist_pos_left
            self.duelist_2_pos = duelist_pos_right
        else:
            self.duelist_1_pos = duelist_pos_right
            self.duelist_2_pos = duelist_pos_left

        self.duelist_1_ai.add_task(GoTo(self.duelist_1_pos))
        self.duelist_2_ai.add_task(GoTo(self.duelist_2_pos))

        viewers_pos_left = (scaled_w(0.1), SCREEN_H - 5)
        viewers_pos_right = (scaled_w(0.9), SCREEN_H - 5)

        for character in self.characters:
            if character.name in (self.duelist_1.name, self.duelist_2.name):
                continue
            ai = self.characters_ai.get(character.name)
            if ai.current_task and not ai.current_task.is_blocking:
                ai.clear()

            if dist(character.position, viewers_pos_left) < dist(character.position, viewers_pos_right):
                ai.add_task(GoTo(viewers_pos_left))
            else:
                ai.add_task(GoTo(viewers_pos_right))

        self.prepare_timer: float = PREPARE_TIME
        self.preparing_stage: bool = True
        self.prepare_stage_text_render_time: int = int(self.prepare_timer)
        self.prepare_stage_surface: Surface = self.get_preparing_stage_surface()

        self.duel_timer: float = DUEL_TIME
        self.fight_stage: bool = False
        self.fight_stage_text_render_time: int = int(self.prepare_timer)
        self.fight_stage_surface: Surface = self.get_duel_stage_surface()

        self.update_stage: Callable = self.prepare_stage_update

    def prepare_stage_update(self, dt: float):
        self.prepare_timer -= dt
        if self.prepare_timer <= 0.:
            self.preparing_stage = False
            self.lock_prediction()
            LOGGER.info(f'Locked prediction')
            self.fight_stage = True
            LOGGER.info(f'Started fight between {self.duelist_1.name} and {self.duelist_2.name}')

            self.duelist_1_ai.clear()
            self.duelist_1_ai.add_task(GoAndKill(self.duelist_2))
            self.duelist_2_ai.clear()
            self.duelist_2_ai.add_task(GoAndKill(self.duelist_1))
            play_sound(BATTLE_HORN_SOUND)
            self.update_stage = self.update_duel_stage

    def update_duel_stage(self, dt: float):
        self.duel_timer -= dt
        if self.duelist_1.dead or self.duelist_2.dead:
            if self.duelist_1.dead and self.duelist_2.dead:
                LOGGER.info(f'Duel result: draw between {self.duelist_1.name} and {self.duelist_2.name}')
                self.cancel_prediction(reason='Нічия!')
                self.is_done = True
            elif self.duelist_1.dead:
                LOGGER.info(f'Duel result: between {self.duelist_1.name} and {self.duelist_2.name}(winner)')
                self.end_prediction(winner=self.duelist_2.name)
                self.is_done = True
            elif self.duelist_2.dead:
                LOGGER.info(f'Duel result: between {self.duelist_1.name}(winner) and {self.duelist_2.name}')
                self.end_prediction(winner=self.duelist_1.name)
                self.is_done = True

        elif self.duel_timer <= 0:
            if self.duelist_1.health_points == self.duelist_2.health_points:
                LOGGER.info(f'Duel result: draw between {self.duelist_1.name} and {self.duelist_2.name}')
                self.cancel_prediction(reason='Нічия!')
            elif self.duelist_1.health_points < self.duelist_2.health_points:
                LOGGER.info(f'Duel result: between {self.duelist_1.name} and {self.duelist_2.name}(winner)')
                self.end_prediction(winner=self.duelist_2.name)
            else:
                LOGGER.info(f'Duel result: between {self.duelist_1.name}(winner) and {self.duelist_2.name}')
                self.end_prediction(winner=self.duelist_1.name)

            self.is_done = True

    def update(self, dt: float, time: float) -> None:
        self.update_stage(dt=dt)

        if self.is_done:
            from game_components.AI.go_and_kiss import GoAndKiss

            self.duelist_1.restore_hp()
            self.duelist_1_ai.clear()

            self.duelist_2.restore_hp()
            self.duelist_2_ai.clear()

            if self.duelist_1.alive and self.duelist_2.alive:
                self.duelist_1_ai.add_task(GoAndKiss(self.duelist_2))
                self.duelist_2_ai.add_task(GoAndKiss(self.duelist_1))

            self.duelist_1_ai.add_task(IdleWalk())
            self.duelist_2_ai.add_task(IdleWalk())

    def end_prediction(self, winner: str, reason: str = ""):
        self.update_prediction(status=PredictionStatus.RESOLVED, winner=winner, reason=reason)

    def lock_prediction(self):
        self.update_prediction(status=PredictionStatus.LOCKED)

    def cancel_prediction(self, reason: str = ""):
        self.update_prediction(status=PredictionStatus.CANCELED, reason=reason)

    def draw(self) -> None:
        if FLAG_IMG:
            MAIN_DISPLAY.blit(FLAG_IMG, self.flag_1_pos)
            MAIN_DISPLAY.blit(FLAG_IMG, self.flag_2_pos)

        if self.preparing_stage:
            # TODO replace by timer check
            if int(self.prepare_timer) != self.prepare_stage_text_render_time:
                self.prepare_stage_surface = self.get_preparing_stage_surface()
                self.prepare_stage_text_render_time = int(self.prepare_timer)
            pos = scaled_w(0.5) - self.prepare_stage_surface.get_width() // 2, 0
            MAIN_DISPLAY.blit(self.prepare_stage_surface, pos)
        else:
            if int(self.duel_timer) != self.fight_stage_text_render_time:
                self.fight_stage_text_render_time = int(self.duel_timer)
                self.fight_stage_surface = self.get_duel_stage_surface()

            pos = scaled_w(0.5) - self.fight_stage_surface.get_width() // 2, 0
            MAIN_DISPLAY.blit(self.fight_stage_surface, pos)

    def get_preparing_stage_text(self) -> str:
        return f'Час на ставки - {int(self.prepare_timer)}'

    def get_preparing_stage_surface(self) -> Surface:
        return add_outline_to_image(DEFAULT_FONT.render(self.get_preparing_stage_text(), 1, 'white', [100, 100, 100]))

    def get_duel_stage_text(self) -> str:
        return f'Duel timer: {int(self.duel_timer)}'

    def get_duel_stage_surface(self) -> Surface:
        return add_outline_to_image(DEFAULT_FONT.render(self.get_duel_stage_text(), 1, 'white', [100, 100, 100]))

    @property
    def duelists_are_on_positions(self) -> bool:
        return self.duelist_1.on_position(self.duelist_1_pos) and self.duelist_2.on_position(self.duelist_2_pos)
