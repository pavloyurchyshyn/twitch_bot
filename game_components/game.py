import yaml
import pathlib
import random
from typing import Dict, Tuple, Optional

from logger import LOGGER
from game_components.user_character import Character, CHAR_SIZE
from game_components.screen import MAIN_DISPLAY

SAVE_FILE_NAME = 'save.yaml'
SAVE_FILE_BACKUP_NAME = 'save_backup.yaml'


class Game:
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.time: float = 0

    def update(self, dt: float):
        self.time += dt
        for character in self.characters.values():
            character.update(dt, time=self.time)

    def get_character(self, name: str) -> Optional[Character]:
        return self.characters.get(name)

    def add_character(self, name: str):
        self.characters[name] = Character(name=name,
                                          position=self.get_random_spawn_position()
                                          )

    def save(self):
        try:
            save = {'avatars_data': {}}
            for char in self.characters.values():
                save['avatars_data'][char.name] = char.get_dict()

            with open(SAVE_FILE_NAME, 'w') as f:
                yaml.safe_dump(save, f, sort_keys=False)

            LOGGER.info(f'Updated save {SAVE_FILE_NAME}')
        except Exception as e:
            LOGGER.error(f'Failed to save {save}, {e}')
        else:
            try:
                with open(SAVE_FILE_NAME) as f:
                    data = f.read()
                with open(SAVE_FILE_BACKUP_NAME, 'w') as f:
                    f.write(data)
            except Exception as e:
                LOGGER.warning(f'Failed to rewrite {SAVE_FILE_BACKUP_NAME} from {SAVE_FILE_NAME} {e}')
            else:
                LOGGER.info(f'Rewrote {SAVE_FILE_BACKUP_NAME}')

    def load(self):
        if pathlib.Path(SAVE_FILE_NAME).exists():
            with open(SAVE_FILE_NAME) as f:
                save_data = yaml.safe_load(f)

            for char_name, char_data in save_data['avatars_data'].items():
                self.characters[char_name] = Character(**char_data)

            LOGGER.info(f'Loaded save {SAVE_FILE_NAME}')

    @staticmethod
    def get_random_spawn_position() -> Tuple[int, int]:
        x_pos = random.randint(0, MAIN_DISPLAY.get_width() - CHAR_SIZE)
        y_pos = random.randint(CHAR_SIZE, MAIN_DISPLAY.get_height() - CHAR_SIZE)
        return x_pos, y_pos
