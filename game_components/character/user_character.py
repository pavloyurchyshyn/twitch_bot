from game_components.character.abc import CharacterABC
from game_components.character.visual.base import CharacterVisual


class Character(CharacterABC):
    visual_part: CharacterVisual

    def create_visual_part(self, hat: str = None, glasses: str = None):
        self.visual_part = CharacterVisual(kind=self.kind,
                                           rect=self.rect,
                                           name=self.name if self._draw_name_flag else '',
                                           state=self.state,
                                           hp_k=self.health_points / self.max_health_points,
                                           body_color=self.body_color,
                                           eyes_color=self.eyes_color,
                                           hat=hat, glasses=glasses,
                                           )

    def damage(self, damage: float, reason: str = ''):
        super().damage(damage=damage, reason=reason)
        self.visual_part.hp_k = self.health_points / self.max_health_points

    def render_visual(self):
        self.visual_part.render_surface()
        self.visual_part.render_name_surface()
        if self.visual_part.glasses_name:
            self.visual_part.render_glasses()
        if self.visual_part.hat_name:
            self.visual_part.render_hat()

    def update(self, dt: float, time: float):
        self.fall(dt)
        self.move(dt)

        if self.on_the_ground:
            self.angle = 0
            self.rotation_speed = 0
        else:
            self.angle += self.rotation_speed

        if self.weapon:
            self.weapon.update(dt=dt, position=self.hands_endpoint)

    def draw(self, *_, **__):
        self.visual_part.draw(character=self)
