from pygame import display, Surface, SRCALPHA, DOUBLEBUF, HWACCEL, FULLSCREEN, SCALED, OPENGL, HWSURFACE, RESIZABLE
from pygame import Rect
import ctypes

user32 = ctypes.windll.user32
SCREEN_W, SCREEN_H = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
SCREEN_H = SCREEN_H // 4


def scaled_w(k) -> int:
    return int(SCREEN_W * k)


def scaled_h(k) -> int:
    return int(SCREEN_H * k)


flags = 0  # FULLSCREEN | DOUBLEBUF # | HWSURFACE
MAIN_SCREEN_DEF_COLOR = [0, 255, 0]

MAIN_DISPLAY = display.set_mode([SCREEN_W, SCREEN_H], flags)
MAIN_DISPLAY.fill(MAIN_SCREEN_DEF_COLOR)


def is_rect_out_of_screen(rect: Rect) -> bool:
    return not MAIN_DISPLAY.get_rect().colliderect(Rect(rect))
