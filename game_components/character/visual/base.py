from math import sin
from pygame import Color, Surface, transform, draw, Rect
from typing import Optional, Type

from game_components import constants as const
from game_components.character.abc import CharacterABC
from game_components.character.visual.clothes import Glasses, Hat, Moustache, Clothes
from game_components.sprite_builder import SpritesBuilder
from game_components.global_data import GD
from game_components.screen import MAIN_DISPLAY
from game_components.utils import DEFAULT_BACK_FONT, add_outline_to_image


class CharVisualError(Exception):
    pass


class CharacterVisual:
    def __init__(self, kind: str, rect: Rect,
                 name: str = '',
                 state: str = const.StatesConst.Idle,
                 hp_k: float = 1,
                 body_color: Optional[Color] = const.DEFAULT_BODY_COLOR,
                 eyes_color: Optional[Color] = const.DEFAULT_EYES_COLOR,
                 hat: str = None, glasses: str = None,
                 ):
        self.kind: str = kind
        self.rect: Rect = rect
        self.state: str = state
        self.hp_k: float = hp_k

        self.name: str = name
        self.name_surface: Surface = None

        self.body_color: Color = Color(body_color) if body_color else body_color
        self.eyes_color: Color = Color(eyes_color) if eyes_color else eyes_color

        self.surface: Surface = None
        self.mirrored_surface: Surface = None

        self.glasses_name: str = glasses
        self.glasses: Clothes = None
        self.hat_name: str = hat
        self.hat: Clothes = None

    def render_glasses(self):
        self.render_clothes_part(class_=Glasses, name=self.glasses_name)

    def render_hat(self):
        self.render_clothes_part(class_=Hat, name=self.hat_name)

    def render_moustache(self):
        self.render_clothes_part(class_=Moustache)

    def render_clothes_part(self, class_: Type[Clothes], name: str = None):
        config = GD.characters_config

        kind_config = config.get(self.kind)
        if kind_config is None:
            GD.logger.error(f'Config do not contain data for kind {self.kind}')
            raise CharVisualError

        state_config = kind_config.get(self.state)
        if state_config is None:
            GD.logger.error(f'Config do not contain data for state {self.kind}/{self.state}')
            raise CharVisualError

        size_k = state_config.get(const.ClothesConst.size_template.format(class_.type))
        size = self.rect.width * size_k[0], self.rect.height * size_k[1]

        position_k = state_config.get(const.ClothesConst.position_template.format(class_.type))

        setattr(self, class_.type, class_(size=size, position=position_k))

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

        self.mirrored_surface = transform.flip(self.surface, flip_x=True, flip_y=False)

    def render_name_surface(self):
        if self.name:
            name_surface = DEFAULT_BACK_FONT.render(self.name, True, 'white')
            name_surface = add_outline_to_image(name_surface)
            size = name_surface.get_size()
            self.name_surface: Surface = transform.smoothscale(name_surface, [size[0] * 0.75, size[1]])

    def draw(self, character: CharacterABC):
        position = list(self.rect.center)

        if character.horizontal_velocity != 0 and not character.is_falling:
            dy = sin(character.movement_time * 8) * character.h_size * 0.05
            position[1] += dy
        else:
            dy = 0

        surface = self.surface if character.move_direction < 0 else self.mirrored_surface
        if character.angle:
            surface = transform.rotate(surface, character.angle)

        position[0] -= surface.get_width() // 2
        position[1] += dy - surface.get_height() // 2

        MAIN_DISPLAY.blit(surface, position)

        if self.glasses:
            self.glasses.draw(character=character,
                              body_surface_pos=position,
                              body_surface_size=surface.get_size())

        if self.hat:
            self.hat.draw(character=character,
                          body_surface_pos=position,
                          body_surface_size=surface.get_size())

        self.draw_name(dy=dy)

        self.draw_hp_bar(dy=dy)

        if character.weapon:
            character.weapon.draw()

    def draw_name(self, dy: int):
        if self.name_surface:
            name_pos = self.get_name_position(dy=dy)
            MAIN_DISPLAY.blit(self.name_surface, name_pos)

    def get_name_position(self, dy: float = 0.) -> const.PosType:
        x_0, y_0 = self.rect.midtop
        x = x_0 - self.name_surface.get_width() // 2
        y = y_0 - self.name_surface.get_height() + dy
        return x, y

    def draw_hp_bar(self, dy: int):
        # TODO probably better to render once
        x, y = self.rect.midtop
        y += dy - const.HP_BAR_H + 2
        x -= const.HP_BAR_W // 2

        draw.rect(MAIN_DISPLAY, const.HP_BAR_BORDER_COLOR, [[x, y], [const.HP_BAR_W, const.HP_BAR_H]], 0, 2)
        hp_w = (const.HP_BAR_W - 2) * self.hp_k
        draw.rect(MAIN_DISPLAY, const.HP_BAR_COLOR, [[x + 1, y + 1], [hp_w, const.HP_BAR_H - 2]], 0, 2)

    @property
    def size(self) -> const.SizeType:
        return self.rect.size
