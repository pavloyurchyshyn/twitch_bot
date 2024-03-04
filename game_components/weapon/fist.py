import random

from game_components.weapon.base import BaseWeapon
from game_components.character.user_character import Character
from game_components.constants import HOOK_VELOCITY, KICK_VELOCITY, FIST_HIT_DAMAGE, PosType
from game_components.sounds import play_kick_sound


class Fists(BaseWeapon):
    def __init__(self, position: PosType,
                 damage: float = FIST_HIT_DAMAGE,
                 hook_power: float = HOOK_VELOCITY,
                 push_power: float = KICK_VELOCITY // 2):
        self.min_damage: float = damage
        self.max_damage: float = damage * 2
        self.hook_power: float = hook_power
        self.push_power: float = push_power
        super().__init__(position=position)

    def use(self, character: Character, target: Character, **kwargs):
        if self.ready_to_use:
            # TODO make a better logic
            hit_num = random.randint(0, 10)
            if hit_num < 2:
                self.hook_hit(character=character, target=target)
            elif hit_num < 6:
                self.simple_hit(character=character, target=target)
            else:
                self.throw_hit(character=character, target=target)

            play_kick_sound()
            self.set_cooldown()

    def simple_hit(self, target: Character, character: Character):
        target.damage(self.damage)

    def hook_hit(self, target: Character, character: Character):
        target.damage(self.damage)
        target.push(vertical_velocity=self.hook_power)

    def throw_hit(self, target: Character, character: Character):
        target.damage(self.damage)
        d_horizontal = -1 if character.position[0] > target.position[0] else 1
        target.push(horizontal_velocity=self.push_power * d_horizontal,
                    vertical_velocity=self.hook_power,
                    )

    @property
    def damage(self) -> float:
        return random.uniform(self.min_damage, self.max_damage)

    def draw(self):
        from pygame import draw
        from game_components.screen import MAIN_DISPLAY
        draw.circle(MAIN_DISPLAY, (255, 0, 0), self.position, 5)
