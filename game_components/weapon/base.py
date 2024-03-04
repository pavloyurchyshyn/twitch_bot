from abc import abstractmethod
from game_components.constants import PosType


class BaseWeapon:
    def __init__(self, position: PosType, cooldown: float = 0.5, cooldown_time: float = 0):
        self.cooldown: float = cooldown
        self.cooldown_time: float = cooldown_time
        self.position: PosType = position

    def update(self, dt: float, position: PosType):
        if not self.ready_to_use:
            self.cooldown_time -= dt
        self.position = position

    @abstractmethod
    def use(self, **kwargs):
        raise NotImplemented

    @abstractmethod
    def draw(self):
        raise NotImplemented

    def set_cooldown(self, value: float = None):
        self.cooldown_time = value if value is not None else self.cooldown

    @property
    def ready_to_use(self) -> bool:
        return self.cooldown_time <= 0
