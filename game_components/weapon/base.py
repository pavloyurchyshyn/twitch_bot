from abc import abstractmethod


class BaseWeapon:
    def __init__(self, cooldown: float = 0.5, cooldown_time: float = 0):
        self.cooldown: float = cooldown
        self.cooldown_time: float = cooldown_time

    def update(self, dt: float):
        if not self.ready_to_use:
            self.cooldown_time -= dt

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
