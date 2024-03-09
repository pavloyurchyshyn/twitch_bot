import os
import random
from pygame import Surface, transform
from game_components.events.base import BaseEvent
from game_components.utils import load_image
from game_components.screen import MAIN_DISPLAY
from game_components.constants import PosType


class HitVisualEffect(BaseEvent):
    name = 'hit_visual_effect'
    behind = False
    HITS_IMAGES = [load_image(f'hits/{img}', size=(40, 40)) for img in os.listdir('sprites/hits')]

    def __init__(self, position: PosType, direction: int = 1):
        super().__init__({}, {})
        if not self.HITS_IMAGES:
            self.finish()
            return
        self.image: Surface = random.choice(self.HITS_IMAGES)
        self.direction: int = direction
        if direction < 1:
            self.image = transform.flip(self.image, True, False)
        self.position: PosType = position
        self.alive_time = 0.3
        from game_components.game import Game

        Game().add_event(self)

    def update(self, dt: float, time: float) -> None:
        self.alive_time -= dt
        if self.alive_time < 0.:
            self.finish()

    def draw(self) -> None:
        MAIN_DISPLAY.blit(self.image, self.position)
