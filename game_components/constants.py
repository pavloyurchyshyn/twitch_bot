from pygame import Color
import enum

MOVE_SPEED = 100
FALL_SPEED = 100
CHAR_SIZE = 80
JUMP_VELOCITY = 200
KICK_VELOCITY = 100
FALLING_RESIST = 0.3
DEFAULT_BODY_COLOR = Color('grey')
DEFAULT_EYES_COLOR = Color('black')
DEFAULT_HP = 100

HP_BAR_W = CHAR_SIZE // 2
HP_BAR_H = 5
HP_BAR_COLOR = Color('white')
HP_BAR_BORDER_COLOR = Color(90, 90, 90)

KICK_SOUND = '8bit_kick.mp3'
KISS_SOUND = 'kiss.mp3'


class AttrsCons(enum.Enum):
    name = 'name'
    w_size = 'w_size'
    h_size = 'h_size'
    position = 'position'
    move_direction = 'move_direction'
    speed = 'speed'
    horizontal_velocity = 'horizontal_velocity'
    vertical_velocity = 'vertical_velocity'
    body_color = 'body_color'
    eyes_color = 'eyes_color'
    health_points = 'health_points'
    kind = 'kind'
    max_health_points = 'max_health_points'
