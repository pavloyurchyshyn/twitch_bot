from pathlib import Path
from pygame import mixer
from logger import LOGGER
from game_components.constants import KICK_SOUND, KISS_SOUND
from config import Config
mixer.Channel(0).set_volume(0.3)

SOUNDS_CACHE = {}
CONFIG = Config()


def play_sound(sound_path: str):
    sound_path = Path(sound_path)
    if not str(sound_path).startswith('sounds'):
        sound_path = Path('sounds', sound_path)

    if str(sound_path) not in SOUNDS_CACHE:
        if not sound_path.exists():
            LOGGER.error(f'{sound_path} does not exists')
            return
        sound = mixer.Sound(sound_path)
        sound.set_volume(CONFIG.sounds.get('global_volume', 0.5))
        SOUNDS_CACHE[sound_path] = sound

    mixer.Sound.play(SOUNDS_CACHE[sound_path])


def play_kick_sound():
    play_sound(KICK_SOUND)


def play_kiss_sound():
    play_sound(KISS_SOUND)
