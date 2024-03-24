import random
from config import Config
from game_components.singletone_decorator import single_tone_decorator
from game_components import constants as const
from game_components.screen import scaled_w


@single_tone_decorator
class GlobalData:
    def __init__(self):
        self.time: float = 0
        self.dt: float = 0
        self.config: Config = Config()

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
        return self.config.get('save_file', 'save.yaml')

    @property
    def save_backup_file(self) -> str:
        return self.config.get('save_file', 'save_backup.yaml')

    @property
    def character_size(self) -> const.SizeType:
        return self.config.get('character', {}).get('size', (const.CHAR_SIZE, const.CHAR_SIZE))

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
        return self.character_config.get('max_hp', const.DEFAULT_HP)

    @property
    def character_move_speed(self) -> float:
        return self.character_config.get('move_speed', const.MOVE_SPEED)


GD = GlobalData()
