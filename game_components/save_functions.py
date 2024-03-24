import yaml
from game_components.constants import AttrsCons
from game_components.character.user_character import Character
from game_components.global_data import GD
from logger import LOGGER
from copy import deepcopy

__all__ = ['SaveConst', 'save_into', 'load_data',
           'get_save_template', 'get_character_dict', 'get_character_dict', 'get_character_person_dict',
           'save_character_attr', 'get_character_person_attrs']


class SaveConst:
    avatars_data = 'avatars_data'
    users_data = 'users_data'
    char_data = 'char_data'

    statistic = 'statistic'
    death_count = 'death_count'
    duels_won = 'duels_won'
    duels_count = 'duels_count'
    duels_lost = 'duels_lost'


def save_into(data, save_file=None):
    save_file = GD.save_file if save_file is None else save_file
    backup = load_data(save_file)

    prev_data = deepcopy(backup)
    prev_data.update(data)
    try:
        with open(save_file, 'w') as f:
            yaml.safe_dump(prev_data, f, sort_keys=False)
    except Exception as e:
        LOGGER.warning(f'Failed to save data into {save_file}: \n{e}')
        with open(save_file, 'w') as f:
            yaml.safe_dump(backup, f, sort_keys=False)


def load_data(save_file=None) -> dict:
    save_file = GD.save_file if save_file is None else save_file
    with open(save_file) as f:
        return yaml.safe_load(f)


def get_save_template() -> dict:
    return {SaveConst.avatars_data: {}}


def get_character_dict(character: Character) -> dict:
    attrs_const = character.attrs_const
    data = {attr_name.value: getattr(character, attr_name.value) for attr_name in attrs_const}

    data[AttrsCons.position.value] = tuple(data[AttrsCons.position.value])
    if data.get(AttrsCons.body_color.value):
        data[AttrsCons.body_color.value] = tuple(data[AttrsCons.body_color.value])
    if data.get(AttrsCons.eyes_color.value):
        data[AttrsCons.eyes_color.value] = tuple(data[AttrsCons.eyes_color.value])
    return data


def get_character_person_dict(character) -> dict:
    data = {attr_name.value: getattr(character, attr_name.value) for attr_name in character.person_attrs_const}
    if data.get(AttrsCons.body_color.value):
        data[AttrsCons.body_color.value] = tuple(data[AttrsCons.body_color.value])
    if data.get(AttrsCons.eyes_color.value):
        data[AttrsCons.eyes_color.value] = tuple(data[AttrsCons.eyes_color.value])
    return data


def save_character_attr(character_uid: str, attr: str, value, save_file=None):
    data = load_data(save_file)

    users_data = data[SaveConst.users_data] = data.get(SaveConst.users_data, {})
    user_data = users_data[character_uid] = users_data.get(character_uid, {})
    char_data = user_data[SaveConst.char_data] = user_data.get(SaveConst.char_data, {})
    char_data[attr] = value

    save_into(data, save_file=save_file)


def get_character_person_attrs(character_uid: str, save_file=None) -> dict:
    data = load_data(save_file=save_file)
    users_data = data.get(SaveConst.users_data, {})
    user_data = users_data.get(character_uid, {})
    return user_data.get(SaveConst.char_data, {})


def get_user_statistic(character_uid: str, save_file=None) -> dict:
    data = load_data(save_file=save_file)
    users_data = data.get(SaveConst.users_data, {})
    user_data = users_data.get(character_uid, {})
    return user_data.get(SaveConst.statistic, {})


def save_user_statist_attr(character_uid: str, stat_name, value, save_file=None):
    data = load_data(save_file)

    users_data = data[SaveConst.users_data] = data.get(SaveConst.users_data, {})
    user_data = users_data[character_uid] = users_data.get(character_uid, {})
    stat_data = user_data[SaveConst.statistic] = user_data.get(SaveConst.statistic, {})
    stat_data[stat_name] = value

    save_into(data, save_file=save_file)


def add_1_to_user_death_count(character_uid, save_file=None):
    death_count = get_user_statistic(character_uid, save_file=save_file).get(SaveConst.death_count, 0) + 1
    save_user_statist_attr(character_uid, stat_name=SaveConst.death_count, value=death_count, save_file=save_file)
