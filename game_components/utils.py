import os
from pygame import Surface, SRCALPHA, font
from game_components.screen import scaled_w
from pygame import image, error, transform, Color, surface
from logger import LOGGER


def get_surface(h_size, v_size=None, transparent: (bool, int) = 0, flags=0, color=None):
    v_size = v_size if v_size else h_size

    if transparent:
        flags = SRCALPHA

    surf = Surface([h_size, v_size], flags, 32)

    if color:
        surf.fill(color)

    surf.convert_alpha()
    return surf


DEFAULT_FONT = font.SysFont('Arial', scaled_w(0.01))
DEFAULT_BACK_FONT = font.SysFont('Arial', scaled_w(0.015), bold=True, italic=True)


def load_image(path: str, size: (int, int) = None, smooth_scale=False) -> surface.Surface:
    try:
        if not str(path).startswith('sprites'):
            path = os.path.join('sprites', path)

        sprite = image.load(path)

        if size and sprite.get_size() != size:
            size = (int(size[0]), int(size[1]))
            if smooth_scale:
                sprite = transform.smoothscale(sprite, size).convert_alpha()
            else:
                sprite = transform.scale(sprite, size).convert_alpha()

        LOGGER.debug(f'Loaded {path} {sprite.get_size()}')
        return sprite
    except (error, FileNotFoundError) as e:
        LOGGER.error(f'Failed to load {path}: {e}')


def __normalize_color(color) -> int:
    if color > 255:
        return 255
    elif color < 0:
        return 0
    else:
        return int(color)


def normalize_color(color) -> Color:
    return Color(list(map(__normalize_color, tuple(color))))
