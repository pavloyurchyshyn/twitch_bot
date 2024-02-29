import yaml
import pathlib
import random
from typing import Dict, Tuple, Optional, List, Callable

from logger import LOGGER
from game_components.AI.base import AI
from game_components.screen import MAIN_DISPLAY
from game_components.character.user_character import Character, CHAR_SIZE
from game_components.character.fabric import get_character


from game_components.events.base import BaseEvent
from game_components.events.storm import StormEvent
from game_components.events.duel_event import DuelEvent
from game_components.events.character_died import CharacterGhost

SAVE_FILE_NAME = 'save.yaml'
SAVE_FILE_BACKUP_NAME = 'save_backup.yaml'


class Game:
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.characters_AI: Dict[str, AI] = {}
        self.events: List[BaseEvent] = []
        self.send_msg: Callable = lambda *_, **__: None  # TODO make functions interfaces
        self.create_prediction: Callable = lambda *_, **__: None
        self.end_prediction: Callable = lambda *_, **__: None
        self.time: float = 0

    def update(self, dt: float):
        self.time += dt

        for event in self.events:
            if event.behind:
                event.draw()

        for name, character in self.characters.copy().items():
            character_ai = self.characters_AI.get(name)
            if character_ai:
                character_ai.update(character=character, dt=dt, time=self.time, game_obj=self)
            try:
                character.update(dt=dt, time=self.time)
                character.draw(dt=dt, time=self.time)
                if character.dead:
                    self.characters.pop(character.name)
                    self.characters_AI.pop(character.name, None)
                    LOGGER.info(f'{character.name} died')
                    self.add_character_ghost(character)
                    death_reason = ''
                    if character.death_reason:
                        death_reason = character.death_reason
                    self.send_msg(f'@{character.name} пагіб iamvol3Ogo {death_reason}')
            except Exception as e:
                LOGGER.error(f'Failed to update {name}\n{e}')

        for event in self.events.copy():
            event.update(dt, time=self.time)
            if not event.behind:
                event.draw()
            if event.is_done:
                self.events.remove(event)
                LOGGER.info(f'{event.name} is done')

    def get_character(self, name: str) -> Optional[Character]:
        return self.characters.get(name)

    def add_character(self, name: str, **kwargs):
        position = kwargs.pop(Character.attrs_const.position, self.get_random_spawn_position())
        self.characters[name] = get_character(name=name, position=position)
        self.add_ai_for(name)

    def add_ai_for(self, name: str):
        self.characters_AI[name] = AI()

    def get_character_ai(self, name: str) -> Optional[AI]:
        if name in self.characters:
            if name not in self.characters_AI:
                self.add_ai_for(name)
            return self.characters_AI[name]
        else:
            return None

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
                char_name: str = char_name.strip().lower()
                self.characters[char_name] = get_character(**char_data)
                self.add_ai_for(char_name)

            LOGGER.info(f'Loaded save {SAVE_FILE_NAME}')

    def make_storm(self):
        self.add_event(StormEvent(self.get_characters_list()))

    def add_character_ghost(self, character: Character):
        try:
            self.add_event(CharacterGhost(position=tuple(character.position),
                                          ghost_surface=character.ghost_surface,
                                          name_surface=character.name_surface))
        except Exception as _:
            LOGGER.error(f'Failed to create ghost for {character.get_dict()}')

    def add_event(self, event: BaseEvent):
        self.events.append(event)

    def check_if_any_event_is_blocking(self) -> bool:
        return any([event.is_blocking for event in self.events])

    def check_if_redeem_is_blocked_by_events(self, redeem_name: str) -> bool:
        return any([redeem_name in event.blocked_redeems for event in self.events])

    def start_duel(self, duelist_1: Character, duelist_2: Character):
        self.send_msg(f'УВАГА @{duelist_1.name} оголосив дуель @{duelist_2.name} iamvol3Eh !')
        duel_event = DuelEvent(duelist_1=duelist_1,
                               duelist_2=duelist_2,
                               characters_list=self.get_characters_list(),
                               characters_ai=self.characters_AI,
                               update_prediction=self.end_prediction,
                               )

        self.create_prediction(title='Хто переможе?',
                               outcomes=[duelist_1.name, duelist_2.name],
                               time_to_predict=duel_event.prepare_timer)

        self.add_event(duel_event)
        LOGGER.info(f'Started duel between {duelist_1.name} and {duelist_2.name}')

    def get_characters_list(self) -> List[Character]:
        return list(self.characters.values())

    @staticmethod
    def get_random_spawn_position() -> Tuple[int, int]:
        x_pos = random.randint(0, MAIN_DISPLAY.get_width() - CHAR_SIZE)
        y_pos = random.randint(CHAR_SIZE, MAIN_DISPLAY.get_height() - CHAR_SIZE)
        return x_pos, y_pos
