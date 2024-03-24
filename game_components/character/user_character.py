import random
from math import sin
from typing import List, Optional, Union
from pygame import Surface, transform, Color, Rect, draw

from game_components.constants import *
from game_components.screen import MAIN_DISPLAY
from game_components.weapon.base import BaseWeapon
from game_components.utils import DEFAULT_BACK_FONT
from game_components.utils import add_outline_to_image
from game_components.sprite_builder import SpritesBuilder


# TODO make character ABC
class Character:
    attrs_const = AttrsCons
    states_const = StatesConst

    def __init__(self, position: PosType,
                 kind: str,
                 name: str = '',
                 draw_name: bool = True,
                 w_size: int = CHAR_SIZE, h_size: int = CHAR_SIZE,
                 speed: float = MOVE_SPEED, move_direction: int = 1,
                 body_color: Optional[Color] = DEFAULT_BODY_COLOR,
                 eyes_color: Optional[Color] = DEFAULT_EYES_COLOR,
                 health_points: float = None,
                 max_health_points: float = DEFAULT_HP,
                 horizontal_velocity: float = 0,
                 vertical_velocity: float = 0,
                 make_ghost: bool = True,
                 weapon: Optional[BaseWeapon] = None,
                 is_player: bool = True,
                 state: str = StatesConst.Idle,
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

        self.body_color: Color = Color(body_color) if body_color else body_color
        self.eyes_color: Color = Color(eyes_color) if eyes_color else eyes_color

        self.surface: Surface = None
        self.name_surface: Surface = None
        self.render_surface()
        if self.name:
            self.render_name_surface()

        self.make_ghost: bool = make_ghost

        self.alive: bool = True

        self.draw_over: List[Surface] = []
        self.death_reason: str = ''
        self.movement_time: float = 0

    def render_surface(self):
        self.surface = SpritesBuilder.get_character_body_img(kind=self.kind, size=self.size, state=self.state)
        if self.body_color:
            self.surface = SpritesBuilder.recolor_surface(surface=self.surface,
                                                          kind=self.kind,
                                                          state=self.state,
                                                          color_key=SpritesBuilder.RecolorKeys.BODY_COLOR_KEY,
                                                          new_color=self.body_color)
        if self.eyes_color:
            self.surface = SpritesBuilder.recolor_surface(surface=self.surface,
                                                          kind=self.kind,
                                                          state=self.state,
                                                          color_key=SpritesBuilder.RecolorKeys.EYES_COLOR_KEY,
                                                          new_color=self.eyes_color)

    def render_name_surface(self):
        name_surface = DEFAULT_BACK_FONT.render(self.name, True, 'white')
        name_surface = add_outline_to_image(name_surface)
        size = name_surface.get_size()
        self.name_surface: Surface = transform.smoothscale(name_surface, [size[0] * 0.75, size[1]])

    def update(self, dt: float, time: float):
        self.fall(dt)
        self.move(dt)

        if self.on_the_ground:
            self.angle = 0
            self.rotation_speed = 0
        else:
            self.angle += self.rotation_speed

        if self.weapon:
            self.weapon.update(dt=dt, position=self.hands_endpoint)

    def draw(self, *_, **__):
        if self.angle:
            surface = transform.rotate(self.surface, self.angle)
        else:
            surface = self.surface

        position = list(self.center)
        if self.horizontal_velocity != 0 and not self.is_falling:
            # dy = sin(self.movement_time * 8 + self.move_anim_deviation) * self.h_size * 0.05
            dy = sin(self.movement_time * 8) * self.h_size * 0.05
            position[1] += dy
        else:
            dy = 0
        dx = -surface.get_width() // 2

        position[0] += dx
        position[1] += dy - surface.get_height() // 2

        if self.look_direction > 0:
            surface = transform.flip(surface, True, False)

        MAIN_DISPLAY.blit(surface, position)

        if self._draw_name_flag:
            self.draw_name(dy)
        self.draw_hp_bar(dy)
        if self.weapon:
            self.weapon.draw()

    def draw_name(self, dy: int):
        name_pos = self.get_name_position(dy=dy)
        MAIN_DISPLAY.blit(self.name_surface, name_pos)

    def get_name_position(self, dy: float = 0) -> Tuple[float, float]:
        x_0, y_0 = self.rect.midtop
        x = x_0 - self.name_surface.get_width() // 2
        y = y_0 - self.name_surface.get_height() + dy
        return x, y

    def draw_hp_bar(self, dy: int):
        x, y = self.rect.midtop
        y += dy - HP_BAR_H + 2
        x -= HP_BAR_W // 2

        draw.rect(MAIN_DISPLAY, HP_BAR_BORDER_COLOR, [[x, y], [HP_BAR_W, HP_BAR_H]], 0, 2)
        hp_w = (HP_BAR_W - 2) * self.health_points / self.max_health_points
        draw.rect(MAIN_DISPLAY, HP_BAR_COLOR, [[x + 1, y + 1], [hp_w, HP_BAR_H - 2]], 0, 2)

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
