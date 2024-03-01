from pathlib import Path
from pygame import mixer
from logger import LOGGER
from game_components.constants import KICK_SOUND, KISS_SOUND

SOUNDS_CASH = {}


def play_sound(sound_path: str):
    sound_path = Path(sound_path)
    if not str(sound_path).startswith('sounds'):
        sound_path = Path('sounds', sound_path)

    if str(sound_path) not in SOUNDS_CASH:
        if not sound_path.exists():
            LOGGER.error(f'{sound_path} does not exists')
            return
        sound = mixer.Sound(sound_path)
        SOUNDS_CASH[sound_path] = sound

    mixer.Sound.play(SOUNDS_CASH[sound_path])


def play_kick_sound():
    play_sound(KICK_SOUND)


def play_kiss_sound():
    play_sound(KISS_SOUND)
