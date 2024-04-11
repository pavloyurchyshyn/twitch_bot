from abc import abstractmethod
import random
from typing import List, Optional, Union
from pygame import Surface, Color, Rect

from game_components.global_data import GD
from game_components.constants import *
from game_components.screen import MAIN_DISPLAY
from game_components.weapon.base import BaseWeapon

__all__ = ['CharacterABC']


class CharacterABC:
    attrs_const = AttrsCons
    states_const = StatesConst

    def __init__(self, position: PosType,
                 kind: str,
                 name: str = '',
                 draw_name: bool = True,
                 w_size: int = GD.character_width, h_size: int = GD.character_height,
                 speed: float = GD.character_move_speed, move_direction: int = 1,
                 body_color: Optional[Color] = DEFAULT_BODY_COLOR,
                 eyes_color: Optional[Color] = DEFAULT_EYES_COLOR,
                 health_points: float = None,
                 max_health_points: float = GD.character_max_hp,
                 horizontal_velocity: float = 0,
                 vertical_velocity: float = 0,
                 make_ghost: bool = True,
                 weapon: Optional[BaseWeapon] = None,
                 is_player: bool = True,
                 state: str = StatesConst.Idle,
                 hat:  str = None,
                 glasses:  str = None,
                 *_,
                 **__,
                 ):
        self.name: str = name.lower()
        self._draw_name_flag: bool = draw_name
        self.kind: str = kind
        self.state: str = state
        self.is_player: bool = is_player

        self.w_size: int = w_size
        self.h_size: int = h_size
        self._position: List = list(position)
        self.rotation_speed: float = DEFAULT_ROTATION_SPEED * random.random()
        self.angle: float = 0

        self.look_direction: int = 1
        self.max_health_points: float = max_health_points
        self.health_points: float = max_health_points if health_points is None else health_points

        self.weapon: Optional[BaseWeapon] = weapon

        self.rect: Rect = Rect(position, self.size)
        if move_direction is None:
            move_direction = random.randint(-1, 1)
        self.move_direction: int = move_direction
        self.speed: float = speed

        self.horizontal_velocity: float = horizontal_velocity
        self.vertical_velocity: float = vertical_velocity + 0.1

        self._body_color: Color = Color(body_color) if body_color else body_color
        self._eyes_color: Color = Color(eyes_color) if eyes_color else eyes_color

        self.make_ghost: bool = make_ghost

        self.alive: bool = True

        self.draw_over: List[Surface] = []
        self.death_reason: str = ''
        self.movement_time: float = 0

        self.visual_part: 'CharacterVisual' = None
        self.create_visual_part(hat=hat, glasses=glasses)
        self.render_visual()

    @abstractmethod
    def render_visual(self):
        raise NotImplemented

    @abstractmethod
    def create_visual_part(self, hat: str = None, glasses: str = None):
        raise NotImplemented

    def damage(self, damage: float, reason: str = ''):
        self.health_points -= damage
        if self.health_points < 1:
            self.alive = False
            self.death_reason = reason

    def heal(self, hp: float):
        self.health_points += hp
        if self.health_points > self.max_health_points:
            self.health_points = self.max_health_points

    def move(self, dt: float):
        if self.move_direction or self.horizontal_velocity:
            if self.is_falling and self.horizontal_velocity:
                self.horizontal_velocity -= self.horizontal_velocity * FALLING_RESIST * dt
                self.horizontal_velocity = round(self.horizontal_velocity, 2)
            elif not self.is_falling:
                self.horizontal_velocity = self.move_direction * self.speed
                self.movement_time += dt

            dx = self.horizontal_velocity * dt
            self._position[0] += self.horizontal_velocity * dt
            self.set_look_direction(dx)
            self.rect.x = self._position[0]

            if self.rect.x > (MAIN_DISPLAY.get_width() - self.w_size):
                self.rect.x = MAIN_DISPLAY.get_width() - self.w_size
                self.move_direction = -1
            elif self.rect.x < 1:
                self.rect.x = 0
                self.move_direction = 1

    def fall(self, dt):
        if self.vertical_velocity or self.is_falling:
            self._position[1] += self.vertical_velocity * dt
            self.rect.y = self._position[1]
            self.vertical_velocity += FALL_SPEED * dt

            if self.rect.y < -(self.h_size * 2):
                self._position[1] = -(self.h_size * 2)
                self.rect.y = self._position[1]
                self.vertical_velocity = 0
            elif self.rect.y > MAIN_DISPLAY.get_height() - self.h_size:
                self._position[1] = MAIN_DISPLAY.get_height() - self.h_size
                self.rect.y = self._position[1]
                self.vertical_velocity = 0

    def push(self, horizontal_velocity: float = 0, vertical_velocity: float = 0, rotation_speed: float = 0):
        self.horizontal_velocity += horizontal_velocity
        self.vertical_velocity -= vertical_velocity
        self.rotation_speed += rotation_speed

    def set_look_direction(self, direction: Union[int, float]) -> None:
        if direction == 0:
            return
        self.look_direction = -1 if direction < 0 else 1

    @property
    def size(self) -> SizeType:
        return self.w_size, self.h_size

    @property
    def is_falling(self) -> bool:
        return self.rect.y < MAIN_DISPLAY.get_height() - self.h_size - 1

    @property
    def on_the_ground(self) -> bool:
        return not self.is_falling

    @property
    def hands_endpoint(self) -> PosType:
        return self.rect.midright if self.look_direction > 0 else self.rect.midleft

    def stop(self):
        self.move_direction = 0
        self.movement_time = 0

    @property
    def center(self) -> PosType:
        return self.rect.center

    @property
    def center_x(self) -> int:
        return self.center[0]

    @property
    def center_y(self) -> int:
        return self.center[1]

    def restore_hp(self):
        self.health_points = self.max_health_points

    @property
    def dead(self) -> bool:
        return not self.alive

    @property
    def position(self) -> PosType:
        return self.rect.topleft

    def on_position(self, position: PosType) -> bool:
        return self.rect.collidepoint(position)

    @position.setter
    def position(self, position: PosType):
        self._position[0] = position[0]
        self._position[1] = position[1]
        self.rect.x, self.rect.y = position

    @property
    def x(self) -> int:
        return self.position[0]

    @property
    def y(self) -> int:
        return self.position[1]

    @property
    def body_color(self) -> Color:
        return self._body_color

    @body_color.setter
    def body_color(self, color:  Color) -> None:
        self._body_color = color
        self.visual_part.body_color = color

    @property
    def eyes_color(self) -> Color:
        return self._eyes_color

    @eyes_color.setter
    def eyes_color(self, color:  Color) -> None:
        self._eyes_color = color
        self.visual_part.eyes_color = color
