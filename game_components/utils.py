from typing import Union
from pathlib import Path
from pygame import Surface, SRCALPHA, font, mask as py_mask
from pygame import image, error, transform, Color, surface, draw
from logger import LOGGER
from game_components.screen import scaled_w


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
FONT_25_px = font.SysFont('Arial', 25, bold=True, italic=True)
FONT_35_px = font.SysFont('Arial', 35, bold=True, italic=True)


def load_image(path: Union[str, Path], size: (int, int) = None, smooth_scale=False) -> surface.Surface:
    try:
        if not str(path).startswith('sprites'):
            path = Path('sprites', path)

        sprite = image.load(str(path))

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


def add_outline_to_image(image: Surface, border_color: tuple = (0, 0, 0)) -> Surface:
    mask = py_mask.from_surface(image)
    result_surface = get_surface(image.get_width() + 4, image.get_height() + 4, transparent=1)
    loc = [2, 2]
    mask_surf = mask.to_surface(unsetcolor=(0, 0, 0, 0), setcolor=border_color)
    result_surface.blit(mask_surf, (loc[0] - 1, loc[1]))
    result_surface.blit(mask_surf, (loc[0] + 1, loc[1]))
    result_surface.blit(mask_surf, (loc[0], loc[1] - 1))
    result_surface.blit(mask_surf, (loc[0], loc[1] + 1))

    result_surface.blit(image, loc)

    return result_surface


def get_text_with_outline(text: str, color='white', font_: font.Font = DEFAULT_FONT,
                          border_color: tuple = (0, 0, 0)) -> Surface:
    return add_outline_to_image(font_.render(text, 0, color), border_color=border_color)


def get_progress_bar(current: int, max_value: int, h_size: int, v_size: int,
                     border_color: Color, color: Color) -> Surface:
    s = get_surface(h_size=h_size, v_size=v_size, transparent=1)
    draw.rect(s, border_color, [[0, 0], [h_size, v_size]], 0, 2)
    inner_w = (h_size - 2) * max_value / current
    draw.rect(s, color, [[1, 1], [inner_w, v_size - 2]], 0, 2)

    return s
