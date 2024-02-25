from pathlib import Path
from pygame import mixer

SOUNDS_CASH = {}


def play_sound(sound_path: str):
    sound_path = Path(sound_path)
    if not str(sound_path).startswith('sounds'):
        sound_path = Path('sounds', sound_path)

    if str(sound_path) not in SOUNDS_CASH:
        sound = mixer.Sound(sound_path)
        SOUNDS_CASH[sound_path] = sound

    mixer.Sound.play(SOUNDS_CASH[sound_path])
