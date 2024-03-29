import random
from math import dist
from typing import List, Optional, Dict, Callable
from pygame import Surface

from logger import LOGGER
from game_components.events.base import BaseEvent
from game_components.events.prediction_mixin import EventPredictionMixin
from game_components.character.user_character import Character
from game_components.AI.cheer import Cheer
from game_components.AI.base import AI, GoTo, IdleWalk
from game_components.AI.go_and_kill import GoAndKill
from game_components.screen import scaled_w, SCREEN_H, MAIN_DISPLAY
from game_components.utils import FONT_25_px, load_image, add_outline_to_image, DEFAULT_FONT
from game_components.sounds import play_sound

PREPARE_TIME = 60
DUEL_TIME = 45
BATTLE_HORN_SOUND = 'battle_horn.mp3'
BATTLE_END_SOUND = 'fanfare.mp3'
try:
    FLAG_IMG: Surface = load_image('flag.png', size=(50, 150))
except Exception:
    FLAG_IMG: Optional[Surface] = None


class DuelEvent(BaseEvent, EventPredictionMixin):
    name = 'duel'
    is_blocking = True
    behind = True

    def __init__(self, duelist_1: Character, duelist_2: Character,
                 characters_dict: Dict[str, Character], characters_ai: Dict[str, AI],
                 update_prediction: Callable):
        super().__init__(characters_dict=characters_dict, characters_ai=characters_ai)
        EventPredictionMixin.__init__(self, update_method=update_prediction)
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
            ld_1 = 1
            ld_2 = -1
        else:
            self.duelist_1_pos = duelist_pos_right
            self.duelist_2_pos = duelist_pos_left
            ld_1 = -1
            ld_2 = 1

        self.duelist_1_ai.add_task(GoTo(self.duelist_1_pos, look_direction=ld_1))
        self.duelist_2_ai.add_task(GoTo(self.duelist_2_pos, look_direction=ld_2))

        bottom_y = SCREEN_H - 5
        viewers_pos_left = (scaled_w(0.1), bottom_y)
        viewers_pos_right = (scaled_w(0.9), bottom_y)
        for character in self.characters:
            if character.name in (self.duelist_1.name, self.duelist_2.name):
                continue
            ai = self.characters_ai.get(character.name)
            if ai.current_task and not ai.current_task.is_blocking:
                ai.clear()

            if dist(character.position, viewers_pos_left) < dist(character.position, viewers_pos_right):
                pos = random.randint(0, int(viewers_pos_left[0])), bottom_y
                ai.add_task(GoTo(pos))
                ai.add_task(Cheer(event_to_follow=self, direction_to_look=1))
            else:
                pos = random.randint(int(viewers_pos_right[0]), MAIN_DISPLAY.get_width()), bottom_y
                ai.add_task(GoTo(pos))
                ai.add_task(Cheer(event_to_follow=self, direction_to_look=-1))

        self.prepare_timer: float = PREPARE_TIME
        self.preparing_stage: bool = True
        self.prepare_stage_text_render_time: int = int(self.prepare_timer)
        self.prepare_stage_surface: Surface = self.get_preparing_stage_surface()

        self.duel_timer: float = DUEL_TIME
        self.fight_stage: bool = False
        self.fight_stage_text_render_time: int = int(self.prepare_timer)
        self.fight_stage_surface: Surface = self.get_duel_stage_surface()
        self.title_text_surface: Surface = self.get_title_text_surface()
        self.title_text_surface_pos: tuple = MAIN_DISPLAY.get_rect().midtop[0]-self.title_text_surface.get_width()//2, 0

        self.update_stage: Callable = self.prepare_stage_update
        self.winner: Character = None

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
                self.winner = self.duelist_2
            elif self.duelist_2.dead:
                LOGGER.info(f'Duel result: between {self.duelist_1.name}(winner) and {self.duelist_2.name}')
                self.end_prediction(winner=self.duelist_1.name)
                self.is_done = True
                self.winner = self.duelist_1

        elif self.duel_timer <= 0:
            if self.duelist_1.health_points == self.duelist_2.health_points:
                LOGGER.info(f'Duel result: draw between {self.duelist_1.name} and {self.duelist_2.name}')
                self.cancel_prediction(reason='Нічия!')
            elif self.duelist_1.health_points < self.duelist_2.health_points:
                LOGGER.info(f'Duel result: between {self.duelist_1.name} and {self.duelist_2.name}(winner)')
                self.end_prediction(winner=self.duelist_2.name)
                self.winner = self.duelist_2
            else:
                LOGGER.info(f'Duel result: between {self.duelist_1.name}(winner) and {self.duelist_2.name}')
                self.end_prediction(winner=self.duelist_1.name)
                self.winner = self.duelist_1

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

            for ai in self.characters_ai.values():
                if ai not in (self.duelist_1_ai, self.duelist_2_ai):
                    if self.winner:
                        ai.add_task(GoAndKiss(self.winner))
                    ai.add_task(IdleWalk())
            play_sound(BATTLE_END_SOUND)



    def draw(self) -> None:
        if FLAG_IMG:
            MAIN_DISPLAY.blit(FLAG_IMG, self.flag_1_pos)
            MAIN_DISPLAY.blit(FLAG_IMG, self.flag_2_pos)

        MAIN_DISPLAY.blit(self.title_text_surface, self.title_text_surface_pos)

        if self.preparing_stage:
            # TODO replace by timer check
            if int(self.prepare_timer) != self.prepare_stage_text_render_time:
                self.prepare_stage_surface = self.get_preparing_stage_surface()
                self.prepare_stage_text_render_time = int(self.prepare_timer)
            pos = scaled_w(0.5) - self.prepare_stage_surface.get_width() // 2, self.title_text_surface.get_height()
            MAIN_DISPLAY.blit(self.prepare_stage_surface, pos)
        else:
            if int(self.duel_timer) != self.fight_stage_text_render_time:
                self.fight_stage_text_render_time = int(self.duel_timer)
                self.fight_stage_surface = self.get_duel_stage_surface()

            pos = scaled_w(0.5) - self.fight_stage_surface.get_width() // 2, self.title_text_surface.get_height()
            MAIN_DISPLAY.blit(self.fight_stage_surface, pos)

    def get_preparing_stage_text(self) -> str:
        return f'Час на ставки: {int(self.prepare_timer)}'

    def get_preparing_stage_surface(self) -> Surface:
        return add_outline_to_image(DEFAULT_FONT.render(self.get_preparing_stage_text(), 1, 'white'))

    def get_duel_stage_text(self) -> str:
        return f'{int(self.duel_timer)}'

    def get_duel_stage_surface(self) -> Surface:
        return add_outline_to_image(DEFAULT_FONT.render(self.get_duel_stage_text(), 1, 'white'))

    def get_title_text_surface(self) -> Surface:
        text = f'{self.duelist_1.name.upper()} vs {self.duelist_2.name.upper()}'
        return add_outline_to_image(FONT_25_px.render(text, 1, 'white'))

    @property
    def duelists_are_on_positions(self) -> bool:
        return self.duelist_1.on_position(self.duelist_1_pos) and self.duelist_2.on_position(self.duelist_2_pos)
