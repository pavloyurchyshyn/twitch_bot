import math
from pygame import Surface, transform
from typing import Optional
from pathlib import Path

from game_components.constants import SizeType, PosType
from game_components.sprite_builder import SpritesBuilder
from game_components.character.abc import CharacterABC
from game_components.screen import MAIN_DISPLAY


class Clothes:
    type: str

    def __init__(self, img_name: str, position: PosType, size: Optional[SizeType] = None):
        self.name: str = img_name if Path(img_name).suffix == '.png' else f'{img_name}.png'
        self.size: SizeType = size
        self.position: PosType = position
        self.surface: Surface = SpritesBuilder.get_clothe_surface(name=img_name, size=size)

    def draw(self, character: CharacterABC, body_surface_pos: PosType, body_surface_size: SizeType):
        x_k = self.x_k
        y_k = self.y_k
        surface = self.surface

        sur_x, sur_y = body_surface_pos
        sur_w_size, sur_h_size = body_surface_size

        if character.look_direction == 1:
            x_k = 1 - x_k

        if character.angle != 0:
            # TODO improve
            rad_angle = -math.radians(character.angle - 90)
            surface = transform.rotate(surface, character.angle)

            x = sur_x + sur_w_size / 2
            x_len = (character.w_size * (1 - x_k))
            dx = x - math.cos(rad_angle) * x_len

            y = sur_y + sur_h_size / 2
            y_len = (character.h_size * (1 - y_k)) / 2
            dy = y - math.sin(rad_angle) * y_len

        else:
            dx = sur_x + sur_w_size * x_k
            dy = sur_y + sur_h_size * y_k

        x = dx - surface.get_width() // 2
        y = dy - surface.get_height() // 2

        MAIN_DISPLAY.blit(surface, (x, y))

    @property
    def x_k(self) -> float:
        return self.position[0]

    @property
    def y_k(self) -> float:
        return self.position[1]


class Glasses(Clothes):
    type = 'glasses'

    def __init__(self, size: SizeType, position: PosType, name: str = None):
        name = 'glasses.png' if name is None else name
        super().__init__(img_name=name, size=size, position=position)


class Hat(Clothes):
    type = 'hat'

    def __init__(self, size: SizeType, position: PosType, name: str = None):
        name = 'cylinder_hat.png' if name is None else name
        super().__init__(img_name=name, size=size, position=position)


class Moustache(Clothes):
    type = 'moustache'

    def __init__(self, size: SizeType, position: PosType, name: str = None):
        name = 'moustache.png' if name is None else name
        super().__init__(img_name=name, size=size, position=position)
