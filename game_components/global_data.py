import random
from config import Config
from game_components.singletone_decorator import single_tone_decorator
from game_components.constants import PosType
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
    def get_random_spawn_position() -> PosType:
        x_pos = random.randint(scaled_w(0.1), scaled_w(0.9))
        y_pos = 0  # random.randint(-CHAR_SIZE, MAIN_DISPLAY.get_height() - CHAR_SIZE)
        return x_pos, y_pos
