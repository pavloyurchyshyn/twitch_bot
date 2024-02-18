import os
from pygame import Surface, Color

from game_components.utils import load_image, normalize_color

CAT_IMG_NAME = 'cat_1.png'
DEFAULT_SPRITE = load_image(CAT_IMG_NAME)
CAT_MASK_NAME = 'cat_1_mask.png'
DEFAULT_SPRITE_MASK = load_image(CAT_MASK_NAME)


def get_cat_sprite(path: os.PathLike = None, size=None, smooth_scale=False) -> Surface:
    if path is None:
        return DEFAULT_SPRITE.copy()
    else:
        return load_image(path=path, size=size, smooth_scale=smooth_scale)


class RecolorKeys:
    BODY_COLOR_KEY: Color = Color('blue')
    EYES_COLOR_KEY: Color = Color('green')


def recolor_sprite(sprite: Surface, color_key: Color, new_color: Color, mask_name: str = CAT_MASK_NAME) -> Surface:
    sprite = sprite.copy()
    w, h = sprite.get_size()
    mask_surface = load_image(mask_name, sprite.get_size())
    for x in range(w):
        for y in range(h):
            pos = [x, y]
            pixel_color = mask_surface.get_at(pos)
            if pixel_color == color_key:
                sprite.set_at(pos, new_color)

    return sprite
