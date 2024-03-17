import random
from typing import Dict
from pygame import Surface, Rect, draw

from game_components.character.user_character import Character
from game_components.events.base import BaseEvent
from game_components.screen import MAIN_DISPLAY, is_rect_out_of_screen
from game_components.utils import load_image
from game_components.constants import CHAR_SIZE
from game_components.sounds import play_sound
from logger import LOGGER

SOUNDS_NAME: str = 'thunder_strike.mp3'
DAMAGE: int = 51
CLOUD_IMG = 'storm_clouds.png'


class StormEvent(BaseEvent):
    is_blocking = False
    name = 'StormLight'

    def __init__(self, characters_dict: Dict[str, Character]):
        super().__init__(characters_dict=characters_dict, characters_ai={})
        self.cloud_surface: Surface = load_image(CLOUD_IMG)
        self.direction: int = random.choice((1, -1))

        self.speed = MAIN_DISPLAY.get_width() // 5
        if self.direction == 1:
            self.cloud_x_pos = -self.cloud_surface.get_width() + 2
        else:
            self.cloud_x_pos = MAIN_DISPLAY.get_width() - 2

        self.target: Character = self.get_random_character()
        hit_box_pos = [self.cloud_x_pos + self.cloud_surface.get_width() // 2, 0]
        hit_box_size = [CHAR_SIZE, CHAR_SIZE]
        self.hit_box: Rect = Rect(hit_box_pos, hit_box_size)
        self.made_hit: bool = False

    def update(self, dt: float, time: float) -> None:
        self.cloud_x_pos += dt * self.speed * self.direction
        self.hit_box.x = self.cloud_x_pos + self.cloud_surface.get_width() // 2
        if self.target is None or self.target.dead:
            self.target = self.get_random_character()

        if not self.made_hit and self.target:
            if self.hit_box.left <= self.target.center_x <= self.hit_box.right:
                self.made_hit = True
                self.target.damage(DAMAGE, reason=self.name)
                play_sound(SOUNDS_NAME)
                LOGGER.info(f'{self.target.name} got hit by {self.name}')

        self.is_done = self.cloud_went_away()

    def cloud_went_away(self) -> bool:
        return is_rect_out_of_screen(Rect(self.cloud_position, self.cloud_surface.get_size()))

    def draw(self) -> None:
        MAIN_DISPLAY.blit(self.cloud_surface, self.cloud_position)
        # draw.rect(MAIN_DISPLAY, [255, 0, 0], self.hit_box)

        # TODO lighting image
        if self.target:
            if self.hit_box.left <= self.target.center_x <= self.hit_box.right:
                draw.line(MAIN_DISPLAY, [255, 255, 255], self.hit_box.center, self.target.center, 3)

    @property
    def cloud_position(self):
        return [self.cloud_x_pos, 0]
