from game_components.character.user_character import Character


def get_character(kind: str = 'cat', **kwargs) -> Character:
    return Character(kind=kind, **kwargs)
