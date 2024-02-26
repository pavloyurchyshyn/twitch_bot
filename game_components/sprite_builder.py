from pygame import Surface, Color
from game_components.utils import load_image, normalize_color

BODY_IMG_NAME: str = 'sprite.png'
MASK_IMG_NAME: str = 'mask.png'
GHOST_IMG_NAME: str = 'ghost.png'


def get_character_body_img(kind: str, size=None, smooth_scale=False) -> Surface:
    return load_image(path=f'{kind}/{BODY_IMG_NAME}', size=size, smooth_scale=smooth_scale)


def get_character_mask(kind: str, size=None, smooth_scale=False) -> Surface:
    return load_image(path=f'{kind}/{MASK_IMG_NAME}', size=size, smooth_scale=smooth_scale)


def get_character_ghost(kind: str, size=None, smooth_scale=False) -> Surface:
    return load_image(path=f'{kind}/{GHOST_IMG_NAME}', size=size, smooth_scale=smooth_scale)


class RecolorKeys:
    BODY_COLOR_KEY: Color = Color('blue')
    EYES_COLOR_KEY: Color = Color('green')


def recolor_surface(surface: Surface, color_key: Color,
                    new_color: Color, mask_surface: str = MASK_IMG_NAME) -> Surface:
    new_color = normalize_color(new_color)
    surface = surface.copy()
    w, h = surface.get_size()
    mask_surface = load_image(f'cat/{mask_surface}', surface.get_size())
    for x in range(w):
        for y in range(h):
            pos = [x, y]
            pixel_color = mask_surface.get_at(pos)
            if pixel_color == color_key:
                surface.set_at(pos, new_color)

    return surface
