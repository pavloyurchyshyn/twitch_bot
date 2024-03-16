from typing import Optional, Tuple
from pygame import Surface
from game_components.events.base import BaseEvent
from game_components.utils import get_text_with_outline
from game_components.screen import MAIN_DISPLAY, scaled_w
from game_components.constants import PosType


class TitleEvent(BaseEvent):
    name = 'title_event'

    def __init__(self, text: str, event_to_follow: Optional[BaseEvent] = None, timeout: float = None,
                 text_color = 'white',
                 position: PosType = None):
        super().__init__(characters_dict={}, characters_ai={})
        self.str_text: str = text
        self.text_color = text_color
        self.text: Surface = None
        self.render_text()
        self.event_to_follow: Optional[BaseEvent] = event_to_follow
        self.time: float = None if timeout is None else self.global_data.time + timeout

        self.position: PosType = self.get_new_position() if position is None else position

        if event_to_follow is None and timeout is None:
            self.finish()

    def render_text(self):
        self.text: Surface = get_text_with_outline(self.str_text, color=self.text_color)

    def change_text(self, text: str, position: PosType = None):
        self.str_text = text
        self.render_text()
        self.position: PosType = self.get_new_position() if position is None else position

    def get_new_position(self) -> PosType:
        return scaled_w(0.5) - self.text.get_width() // 2, 0

    def update(self, dt: float, time: float) -> None:
        if self.event_to_follow:
            self.is_done = self.event_to_follow.is_done

    def draw(self) -> None:
        MAIN_DISPLAY.blit(self.text, self.position)
