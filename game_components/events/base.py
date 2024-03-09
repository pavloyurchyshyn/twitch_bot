from abc import abstractmethod
from typing import List, Optional, Dict
import random

from game_components.character.user_character import Character
from game_components.AI.base import AI


class BaseEvent:
    is_blocking: bool = False
    behind: bool = True
    blocked_redeems: tuple = ()
    name: str

    def __init__(self, characters_dict: Dict[str, Character], characters_ai: Dict[str, AI]):
        self.characters_dict: Dict[str, Character] = characters_dict
        self.characters_ai: Dict[str, AI] = characters_ai
        self.is_done: bool = False

    @property
    def characters(self) -> List[Character]:
        return list(self.characters_dict.values())

    def get_random_character(self) -> Optional[Character]:
        if self.characters:
            return random.choice(self.characters)
        else:
            return None

    @abstractmethod
    def update(self, dt: float, time: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(self) -> None:
        raise NotImplementedError

    def finish(self):
        self.is_done = True
