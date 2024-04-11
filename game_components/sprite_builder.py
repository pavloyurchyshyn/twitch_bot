from pathlib import Path
from pygame import Surface, Color

from game_components.utils import load_image, normalize_color
from game_components.constants import SizeType

BODY_IMG_NAME: str = 'sprite.png'
MASK_IMG_NAME: str = 'mask.png'
GHOST_IMG_NAME: str = 'ghost.png'


class SpritesBuilder:
    CACHE = {}

    class RecolorKeys:
        BODY_COLOR_KEY: Color = Color('blue')
        EYES_COLOR_KEY: Color = Color('green')

    @classmethod
    def get_character_body_img(cls, kind: str, state: str, size=None, smooth_scale=False) -> Surface:
        return cls.load_image_cache(path=Path(kind, state, BODY_IMG_NAME), size=size, smooth_scale=smooth_scale)

    @classmethod
    def get_character_mask(cls, kind: str, state: str,
                           mask_name: str = MASK_IMG_NAME, size=None, smooth_scale=False) -> Surface:
        return cls.load_image_cache(path=Path(kind, state, mask_name), size=size, smooth_scale=smooth_scale)

    @classmethod
    def get_character_ghost(cls, kind: str, size=None, smooth_scale=False) -> Surface:
        return cls.load_image_cache(path=Path(kind, GHOST_IMG_NAME), size=size, smooth_scale=smooth_scale)

    @classmethod
    def recolor_surface(cls, surface: Surface, color_key: Color,
                        new_color: Color, kind: str,
                        state: str, mask_name: str = MASK_IMG_NAME) -> Surface:
        new_color = normalize_color(new_color)
        surface = surface.copy()
        w, h = surface.get_size()
        mask_surface = cls.get_character_mask(kind=kind, state=state, mask_name=mask_name, size=surface.get_size())
        for x in range(w):
            for y in range(h):
                pos = [x, y]
                pixel_color = mask_surface.get_at(pos)
                if pixel_color == color_key:
                    surface.set_at(pos, new_color)

        return surface

    @classmethod
    def load_image_cache(cls, path, size=None, smooth_scale=False) -> Surface:
        key = path, size
        if key not in cls.CACHE:
            cls.CACHE[key] = load_image(path=path, size=size, smooth_scale=smooth_scale)
        return cls.CACHE[key]

    @classmethod
    def get_clothe_surface(cls, name: str, size: SizeType = None) -> Surface:
        return cls.load_image_cache(path=Path('clothes', name), size=size)
