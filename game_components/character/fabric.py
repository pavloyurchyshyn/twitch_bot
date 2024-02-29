from game_components.character.user_character import Character
from game_components.weapon.fist import Fists


def get_character(kind: str = 'cat', **kwargs) -> Character:
    return Character(kind=kind, **kwargs, weapon=Fists())
