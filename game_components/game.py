import pathlib
from typing import Dict, Optional, List, Callable

from logger import LOGGER
from game_components.AI.base import AI, IdleWalk
from game_components.character.user_character import Character
from game_components.character.fabric import get_character

from game_components.events.base import BaseEvent
from game_components.events.storm import StormEvent
from game_components.events.duel_event import DuelEvent
from game_components.events.character_died import CharacterGhost
from game_components.events.zombies_event import ZombieEvent
from game_components.events.title import TitleEvent
from game_components.singletone_decorator import single_tone_decorator
from game_components.save_functions import *
from game_components.save_functions import add_1_to_user_death_count
from game_components.global_data import GlobalData

GD: GlobalData = GlobalData()


@single_tone_decorator
class Game:
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.characters_AI: Dict[str, AI] = {}
        self.events: List[BaseEvent] = []
        self.send_msg: Callable = lambda *_, **__: None  # TODO make functions interfaces
        self.create_prediction: Callable = lambda *_, **__: None
        self.end_prediction: Callable = lambda *_, **__: None

    def update(self, dt: float):
        GD.update_time(dt)

        for event in self.events:
            if event.behind:
                event.draw()

        for uid, character in self.characters.copy().items():
            character_ai = self.characters_AI.get(uid)
            if character_ai:
                character_ai.update(dt=dt, time=GD.time, game_obj=self)
            try:
                character.update(dt=dt, time=GD.time)
                character.draw(dt=dt, time=GD.time)
                if character.dead:
                    self.characters.pop(uid)
                    self.characters_AI.pop(uid, None)
                    LOGGER.info(f'{character.name} died')

                    if character.make_ghost:
                        self.add_character_ghost(character)

                    if character.is_player:
                        death_reason = ''
                        if character.death_reason:
                            death_reason = character.death_reason
                        self.send_msg(f'@{character.name} пагіб iamvol3Ogo {death_reason}')
                        add_1_to_user_death_count(character_uid=uid, save_file=SAVE_FILE_NAME)
            except Exception as e:
                LOGGER.error(f'Failed to update {uid}\n{e}')

        for event in self.events.copy():
            event.update(dt, time=GD.time)
            if not event.behind:
                event.draw()
            if event.is_done:
                self.events.remove(event)
                LOGGER.debug(f'{event.name} is done')

    def get_character(self, name: str) -> Optional[Character]:
        return self.characters.get(name)

    def add_character(self, name: str, **kwargs):

        position = kwargs.pop(Character.attrs_const.position, GD.get_random_spawn_position())
        person_data = get_character_person_attrs(name)
        kwargs.update(person_data)

        self.characters[name] = get_character(name=name, position=position, **kwargs)
        self.add_ai_for(name, character=self.characters[name])

    def add_ai_for(self, name: str, character: Character = None):
        character = self.characters[name] if character is None else character
        self.characters_AI[name] = AI(character=character)

    def get_character_ai(self, name: str) -> Optional[AI]:
        if name in self.characters:
            if name not in self.characters_AI:
                self.add_ai_for(name, character=self.characters[name])
            return self.characters_AI[name]
        else:
            return None

    def save(self):
        save = get_save_template()
        try:
            for uid, char in self.characters.items():
                save[SaveConst.avatars_data][uid] = get_character_dict(char)

            save_into(data=save, save_file=SAVE_FILE_NAME)

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
        save_data = {}
        try:
            if pathlib.Path(SAVE_FILE_NAME).exists():
                save_data = load_data(SAVE_FILE_NAME)
                LOGGER.info(f'Loaded save {SAVE_FILE_NAME}')
            else:
                LOGGER.warning(f'Save file {SAVE_FILE_BACKUP_NAME} not found')
                raise FileNotFoundError
        except Exception as e:
            LOGGER.warning(e)
            if pathlib.Path(SAVE_FILE_BACKUP_NAME).exists():
                save_data = load_data(SAVE_FILE_BACKUP_NAME)
                LOGGER.info(f'Loaded save {SAVE_FILE_BACKUP_NAME}')
            else:
                LOGGER.warning(f'Save file {SAVE_FILE_BACKUP_NAME} not found')

        finally:
            for char_name, char_data in save_data.get(SaveConst.avatars_data, {}).items():
                char_name: str = char_name.strip().lower()
                character: Character = get_character(**char_data)
                self.characters[char_name] = character
                self.add_ai_for(char_name, character=character)
                if character.move_direction:
                    self.get_character_ai(char_name).add_task(IdleWalk())

    def make_storm(self):
        self.add_event(StormEvent(self.characters))

    def add_character_ghost(self, character: Character):
        try:
            self.add_event(CharacterGhost(position=tuple(character.position),
                                          ghost_surface=character.ghost_surface,
                                          name_surface=character.name_surface))
        except Exception as _:
            LOGGER.error(f'Failed to create ghost for {get_character_dict(character)}')

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
                               characters_dict=self.characters,
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

    def start_zombies_event(self):
        self.send_msg(f'УВАГА! УВАГА! Зомбі йдуть! Всім приготуватись! І зробити ставки TwitchConHYPE ')

        zombie_event = ZombieEvent(characters_dict=self.characters,
                                   characters_ai=self.characters_AI,
                                   update_prediction=self.end_prediction)
        title = TitleEvent(text='!ZOMBIES ATTACK!', event_to_follow=zombie_event)
        self.add_event(zombie_event)
        self.add_event(title)

        self.create_prediction(title='Хто переможе?',
                               outcomes=[ZombieEvent.Const.Users, ZombieEvent.Const.Zombie],
                               time_to_predict=ZombieEvent.Const.time_to_predict)
        LOGGER.info(f'Started zombie event')
