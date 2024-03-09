from game_components.events.base import BaseEvent
from game_components.character.zombie import Zombie


class ZombieEvent(BaseEvent):
    name = 'zombies_event'
    is_blocking = True

    def update(self, dt: float, time: float) -> None:
        done = True
        for char in self.characters:
            if isinstance(char, Zombie):
                done = False
                break

        self.is_done = done

    def draw(self) -> None:
        pass