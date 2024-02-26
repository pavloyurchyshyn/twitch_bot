from abc import abstractmethod
from typing import List, Optional
import random

from game_components.character.user_character import Character


class BaseEvent:
    blocking: bool = False
    behind: bool = True
    blocked_redeems: tuple = ()
    name: str

    def __init__(self, characters_list: List[Character]):
        self.characters: List[Character] = characters_list
        self.is_done: bool = False

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

    def cancel(self):
        self.is_done = True
