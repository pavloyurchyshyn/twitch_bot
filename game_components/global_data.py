import logging
import os
import random
from config import Config, BaseConfig
from game_components.singletone_decorator import single_tone_decorator
from game_components import constants as const
from game_components.screen import scaled_w
from logger import LOGGER


@single_tone_decorator
class GlobalData:
    debug: bool = os.getenv('DEBUG', '')
    logger: logging.Logger = LOGGER

    def __init__(self):
        self.time: float = 0
        self.dt: float = 0
        self.config: BaseConfig = Config()

    def update_time(self, dt: float):
        self.time += dt
        self.dt = dt

    @staticmethod
    def get_random_spawn_position() -> const.PosType:
        x_pos = random.randint(scaled_w(0.1), scaled_w(0.9))
        y_pos = 0  # random.randint(-CHAR_SIZE, MAIN_DISPLAY.get_height() - CHAR_SIZE)
        return x_pos, y_pos

    @property
    def save_file(self) -> str:
        if self.debug:
            return 'debug_save.yaml'
        else:
            return self.config.get('save_file', 'save.yaml')

    @property
    def save_backup_file(self) -> str:
        if self.debug:
            return 'debug_save.yaml'
        else:
            return self.config.get('save_file', 'save_backup.yaml')

    @property
    def character_size(self) -> const.SizeType:
        return self.character_config.get(const.AttrsCons.size, (const.CHAR_SIZE, const.CHAR_SIZE))

    @property
    def character_width(self) -> int:
        return self.character_size[0]

    @property
    def character_height(self) -> int:
        return self.character_size[1]

    @property
    def character_config(self) -> dict:
        return self.config.get('character', {})

    @property
    def character_max_hp(self) -> float:
        return self.character_config.get(const.AttrsCons.max_health_points, const.DEFAULT_HP)

    @property
    def character_move_speed(self) -> float:
        return self.character_config.get('move_speed', const.MOVE_SPEED)

    @property
    def characters_config(self) -> dict:
        c = self.config.raw
        char = c.get('character', {})
        chars = char.get('characters', {})
        return chars
        # return character_config['characters']


GD = GlobalData()
