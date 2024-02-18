import enum
from typing import Tuple
from pygame import Vector2
from pygame import Surface, transform
from math import sin
import random

from game_components.utils import DEFAULT_BACK_FONT
from game_components.screen import MAIN_DISPLAY
from game_components.constants import *
from game_components.sprite_builder import get_cat_sprite, recolor_sprite, RecolorKeys, CAT_IMG_NAME


class AttrsCons(enum.Enum):
    name = 'name'
    w_size = 'w_size'
    h_size = 'h_size'
    position = 'position'
    move_direction = 'move_direction'
    speed = 'speed'
    horizontal_velocity = 'horizontal_velocity'
    vertical_velocity = 'vertical_velocity'
    body_color = 'body_color'
    eyes_color = 'eyes_color'


class Character:
    def __init__(self, name: str, position: Tuple[int, int],
                 w_size: int = CHAR_SIZE, h_size: int = CHAR_SIZE,
                 speed: float = MOVE_SPEED, move_direction: int = 0,
                 body_color: Color = DEFAULT_BODY_COLOR,
                 eyes_color: Color = DEFAULT_EYES_COLOR,
                 horizontal_velocity: float = 0,
                 vertical_velocity: float = 0,
                 **__,
                 ):
        self.name = name
        self.w_size: int = w_size
        self.h_size: int = h_size
        self.position: Vector2 = Vector2(position)
        self.move_direction: int = move_direction
        self.speed: float = speed
        self.horizontal_velocity: float = horizontal_velocity
        self.vertical_velocity: float = vertical_velocity + 0.1
        self.body_color: Color = Color(body_color)
        self.eyes_color: Color = Color(eyes_color)
        self.move_anim_deviation: int = random.randrange(-1, 2)

        self.surface: Surface = None
        self.render_surface()
        self.name_surface: Surface = None
        self.render_name_surface()

    def render_surface(self):
        self.surface = get_cat_sprite(path=CAT_IMG_NAME, size=self.size)
        self.surface = recolor_sprite(sprite=self.surface,
                                      color_key=RecolorKeys.BODY_COLOR_KEY,
                                      new_color=self.body_color)

        self.surface = recolor_sprite(sprite=self.surface,
                                      color_key=RecolorKeys.EYES_COLOR_KEY,
                                      new_color=self.eyes_color)

    def render_name_surface(self):
        name_surface = DEFAULT_BACK_FONT.render(self.name, True, 'white')
        size = name_surface.get_size()
        self.name_surface: Surface = transform.smoothscale(name_surface, [size[0] * 0.75, size[1]])

    def update(self, dt: float, time: float):
        self.fall(dt)
        self.move(dt)
        self.draw(time)

    def draw(self, time: float):
        position = Vector2(self.position)
        if self.horizontal_velocity != 0:
            dy = sin(time * 5 + self.move_anim_deviation) * self.h_size * 0.05
            position.y += dy
        else:
            dy = 0

        if self.horizontal_velocity > 0:
            MAIN_DISPLAY.blit(transform.flip(self.surface, True, False), position)
        else:
            MAIN_DISPLAY.blit(self.surface, position)
        name_x = self.position.x - (self.name_surface.get_width() - self.w_size) // 2
        name_y = self.position.y - self.name_surface.get_height() + dy
        MAIN_DISPLAY.blit(self.name_surface, (name_x, name_y))

    def move(self, dt: float):
        if self.move_direction or self.horizontal_velocity:
            if self.is_falling and self.horizontal_velocity:
                self.horizontal_velocity -= self.horizontal_velocity * FALLING_RESIST * dt
                self.horizontal_velocity = round(self.horizontal_velocity, 2)
            elif not self.is_falling:
                self.horizontal_velocity = self.move_direction * self.speed

            self.position.x += self.horizontal_velocity * dt
            if self.position.x > (MAIN_DISPLAY.get_width() - self.w_size):
                self.position.x = MAIN_DISPLAY.get_width() - self.w_size
                self.move_direction = -1
            elif self.position.x < 0:
                self.position.x = 0
                self.move_direction = 1

    def fall(self, dt):
        if self.vertical_velocity or self.is_falling:
            self.position.y += self.vertical_velocity * dt
            self.vertical_velocity += FALL_SPEED * dt

            if self.position.y < - self.h_size * 2:
                self.position.y = -self.h_size * 2
                self.vertical_velocity = 0
            elif self.position.y > MAIN_DISPLAY.get_height() - self.h_size:
                self.position.y = MAIN_DISPLAY.get_height() - self.h_size
                self.vertical_velocity = 0

    @property
    def size(self) -> Tuple[int, int]:
        return self.w_size, self.h_size

    @property
    def is_falling(self) -> bool:
        return self.position.y < MAIN_DISPLAY.get_height() - self.h_size

    def get_dict(self) -> dict:
        data = {attr_name.value: getattr(self, attr_name.value) for attr_name in AttrsCons}
        data[AttrsCons.position.value] = tuple(data[AttrsCons.position.value])
        data[AttrsCons.body_color.value] = tuple(data[AttrsCons.body_color.value])
        data[AttrsCons.eyes_color.value] = tuple(data[AttrsCons.eyes_color.value])
        return data
