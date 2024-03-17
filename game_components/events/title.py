from typing import Optional
from pygame import Surface, Font
from game_components.events.base import BaseEvent
from game_components.utils import get_text_with_outline, DEFAULT_FONT
from game_components.screen import MAIN_DISPLAY, scaled_w
from game_components.constants import PosType


class TitleEvent(BaseEvent):
    name = 'title_event'

    def __init__(self, text: str, event_to_follow: Optional[BaseEvent] = None, timeout: float = None,
                 text_color='white', draw_time: bool = False, font: Optional[Font] = DEFAULT_FONT,
                 position: PosType = None):
        super().__init__(characters_dict={}, characters_ai={})
        self.draw_time: bool = draw_time
        self.font: Optional[Font] = font
        self.str_text: str = text
        self.text_color = text_color
        self.text: Surface = None
        self.event_to_follow: Optional[BaseEvent] = event_to_follow
        self.time: float = None if timeout is None else self.global_data.time + timeout

        self.render_text()
        self.position: PosType = self.get_new_position() if position is None else position

        if event_to_follow is None and timeout is None:
            self.finish()

    def render_text(self):
        if self.draw_time:
            text = f'{self.str_text} {int(self.time - self.global_data.time)}'
        else:
            text = self.str_text
        self.text: Surface = get_text_with_outline(text, color=self.text_color)

    def change_text(self, text: str, position: PosType = None):
        self.str_text = text
        self.render_text()
        self.position: PosType = self.get_new_position() if position is None else position

    def get_new_position(self) -> PosType:
        return scaled_w(0.5) - self.text.get_width() // 2, 0

    def update(self, dt: float, time: float) -> None:
        if self.draw_time:
            self.render_text()
        if self.event_to_follow:
            self.is_done = self.event_to_follow.is_done
        if self.time is not None:
            self.is_done = self.time < self.global_data.time

    def draw(self) -> None:
        MAIN_DISPLAY.blit(self.text, self.position)
