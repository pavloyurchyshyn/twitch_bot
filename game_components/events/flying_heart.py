from typing import Tuple
from pygame import Surface

from game_components.events.base import BaseEvent
from game_components.screen import MAIN_DISPLAY, is_rect_out_of_screen
from game_components.utils import load_image


class FlyingHeart(BaseEvent):
    name = 'flying_heart'
    SPEED = -50
    heart_img: Surface = load_image(path='heart.png')

    def __init__(self, position: Tuple[int, int]):
        super().__init__(characters_list=[], characters_ai={})
        self.surface_position: list = list(position)

    def update(self, dt: float, time: float) -> None:
        self.surface_position[1] += self.SPEED * dt
        self.is_done = is_rect_out_of_screen((self.surface_position, self.heart_img.get_size()))

    def draw(self) -> None:
        MAIN_DISPLAY.blit(self.heart_img, self.surface_position)
