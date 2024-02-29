from typing import Optional, Tuple
from pygame import Surface
import math

from game_components.events.base import BaseEvent
from game_components.screen import MAIN_DISPLAY, is_rect_out_of_screen


class CharacterGhost(BaseEvent):
    name: str = 'character_ghost'
    SPEED = -50

    def __init__(self, position: Tuple[int, int], ghost_surface: Surface, name_surface: Optional[Surface] = None):
        super().__init__(characters_list=[], characters_ai={})
        self.surface_position: list = list(position)
        self.ghost_surface: Surface = ghost_surface
        self.name_surface: Surface = name_surface

    def update(self, dt: float, time: float) -> None:
        self.surface_position[1] += self.SPEED * dt
        self.surface_position[0] += math.cos(time * 2) * self.ghost_surface.get_width() * 0.025

        self.is_done = is_rect_out_of_screen((self.surface_position, self.ghost_surface.get_size()))

    def draw(self) -> None:
        MAIN_DISPLAY.blit(self.ghost_surface, self.surface_position)
        if self.name_surface:
            x, y = self.surface_position
            y -= self.name_surface.get_height()
            MAIN_DISPLAY.blit(self.name_surface, (x, y))
