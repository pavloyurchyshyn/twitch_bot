import yaml
import pathlib
import random
from typing import Dict, Tuple, Optional, List, Callable

from logger import LOGGER
from game_components.AI.base import AI
from game_components.screen import MAIN_DISPLAY
from game_components.events.base import BaseEvent
from game_components.events.storm import StormEvent
from game_components.events.character_died import CharacterGhost
from game_components.user_character import Character, CHAR_SIZE

SAVE_FILE_NAME = 'save.yaml'
SAVE_FILE_BACKUP_NAME = 'save_backup.yaml'


class Game:
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.characters_AI: Dict[str, AI] = {}
        self.events: List[BaseEvent] = []
        self.send_msg: Callable = lambda *_, **__: None
        self.time: float = 0

    def update(self, dt: float):
        self.time += dt
        for name, character in tuple(self.characters.items()):
            character_ai = self.characters_AI.get(name)
            if character_ai:
                character_ai.update(character=character, dt=dt, time=self.time)
            try:
                character.update(dt, time=self.time)
                character.draw(dt=dt, time=self.time)
                if character.dead:
                    self.characters.pop(character.name)
                    self.characters_AI.pop(character.name, None)
                    LOGGER.info(f'{character.name} died')
                    self.add_character_ghost(character)
                    self.send_msg(f'@{character.name} пагіб iamvol3Ogo ') # TODO fix
            except Exception as e:
                LOGGER.error(f'Failed to update {name}\n{e}')

        for event in self.events.copy():
            event.update(dt, time=self.time)
            event.draw()
            if event.is_done:
                self.events.remove(event)
                LOGGER.info(f'{event.name} is done')

    def add_ghost(self, character: Character):
        # TODO
        pass

    def get_character(self, name: str) -> Optional[Character]:
        return self.characters.get(name)

    def add_character(self, name: str):
        self.characters_AI[name] = AI()
        self.characters[name] = Character(name=name,
                                          position=self.get_random_spawn_position()
                                          )

    def save(self):
        save = {'avatars_data': {}}
        try:
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

    def make_storm(self):
        self.add_event(StormEvent(list(self.characters.values())))

    def add_character_ghost(self, character: Character):
        try:
            self.add_event(CharacterGhost(position=tuple(character.position),
                                          ghost_surface=character.ghost_surface,
                                          name_surface=character.name_surface))
        except Exception as e:
            print(e)
            LOGGER.error(f'Failed to create ghost for {character.get_dict()}')

    def add_event(self, event: BaseEvent):
        self.events.append(event)

    @staticmethod
    def get_random_spawn_position() -> Tuple[int, int]:
        x_pos = random.randint(0, MAIN_DISPLAY.get_width() - CHAR_SIZE)
        y_pos = random.randint(CHAR_SIZE, MAIN_DISPLAY.get_height() - CHAR_SIZE)
        return x_pos, y_pos
