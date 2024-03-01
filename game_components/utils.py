import os
from pygame import Surface, SRCALPHA, font, mask as py_mask
from pygame import image, error, transform, Color, surface
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


def textHollow(font, message, fontcolor):
    notcolor = [c ^ 0xFF for c in fontcolor]
    base = font.render(message, 0, fontcolor, notcolor)
    size = base.get_width() + 2, base.get_height() + 2
    img = Surface(size, 16)
    img.fill(notcolor)
    base.set_colorkey(0)
    img.blit(base, (0, 0))
    img.blit(base, (2, 0))
    img.blit(base, (0, 2))
    img.blit(base, (2, 2))
    base.set_colorkey(0)
    base.set_palette_at(1, notcolor)
    img.blit(base, (1, 1))
    img.set_colorkey(notcolor)
    return img


def textOutline(font, message, fontcolor, outlinecolor):
    base = font.render(message, 0, tuple(Color(fontcolor)))
    outline = textHollow(font, message, tuple(Color(outlinecolor)))
    img = Surface(outline.get_size(), 16)
    img.blit(base, (1, 1))
    img.blit(outline, (0, 0))
    img.set_colorkey(0)
    return img


def add_outline_to_image(image: Surface, border_color: tuple = (0, 0, 0)) -> Surface:
    mask = py_mask.from_surface(image)
    result_surface = get_surface(image.get_width() + 4, image.get_height() + 4, transparent=1)
    loc = [2, 2]
    mask_surf = mask.to_surface(unsetcolor=(0,0,0,0), setcolor=border_color)
    result_surface.blit(mask_surf, (loc[0] - 1, loc[1]))
    result_surface.blit(mask_surf, (loc[0] + 1, loc[1]))
    result_surface.blit(mask_surf, (loc[0], loc[1] - 1))
    result_surface.blit(mask_surf, (loc[0], loc[1] + 1))

    result_surface.blit(image, loc)

    return result_surface
