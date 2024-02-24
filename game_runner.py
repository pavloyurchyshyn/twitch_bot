def get_game_obj() -> 'GameRunner':
    from os import environ
    import re

    environ['VisualPygameOn'] = 'on'
    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

    from time import time
    from typing import Dict, Callable
    from pygame import init

    init()
    import pygame
    from pygame import font
    from pygame import display, event as EVENT
    from pygame.time import Clock
    from pygame import quit as close_program_pygame

    display.set_caption('twitch_entities')

    from redeems import RewardRedeemedObj
    from game_components.screen import MAIN_DISPLAY
    from game_components.game import Game
    from game_components.utils import DEFAULT_FONT
    from game_components.user_character import JUMP_VELOCITY, AttrsCons
    from game_components.errors import RedeemError, ProhibitedColor
    from logger import LOGGER

    class RedeemsNames:
        spawn = "з'явитись"
        jump = "стрибок"
        recolor_body = "перефарбувати тіло"
        recolor_eyes = "перефарбувати очі"
        set_direction = "змінити напрям"
        every_body_jump = "всім підстрибнути"
        commands_to_ignore = [
            "замовити музику",

        ]

    class GameRunner:
        FPS = 60

        def __init__(self):
            self.is_running: int = 1
            self.game: Game = Game()
            self.game.add_character('test_person')
            self.redeem_processors: Dict[str, Callable] = {
                RedeemsNames.spawn: self.process_spawn_redeem,
                RedeemsNames.jump: self.process_jump_redeem,
                RedeemsNames.recolor_body: self.process_body_recolor_redeem,
                RedeemsNames.recolor_eyes: self.process_eyes_recolor_redeem,
                RedeemsNames.set_direction: self.set_direction,
                RedeemsNames.every_body_jump: self.process_everybody_jump,
            }

        def run(self):
            pygame_clock = Clock()
            display.update()
            start = time()

            while self.is_running:
                events = EVENT.get()
                finish = time()

                pygame_clock.tick(self.FPS)

                delta_time = finish - start
                if delta_time > 0.5:
                    start = time()
                    continue
                start = finish

                MAIN_DISPLAY.fill((0, 255, 0))
                for event in events:
                    if event.type == pygame.QUIT:
                        close_program_pygame()
                        self.is_running = 0
                        break
                if not self.is_running:
                    break

                self.game.update(dt=delta_time)

                self.draw_fps(pygame_clock.get_fps())

                display.update()

        @staticmethod
        def draw_fps(fps):
            fps_text = DEFAULT_FONT.render(str(int(fps)), True, [255, 255, 255], [0, 0, 0])
            MAIN_DISPLAY.blit(fps_text, (0, 0))

        def process_redeem(self, redeem: RewardRedeemedObj):
            LOGGER.info(f'{redeem.user_name} застосував {redeem.name} з аргументом {redeem.input}')

            process_func = self.redeem_processors.get(redeem.name)
            if redeem.name in RedeemsNames.commands_to_ignore:
                return
            elif process_func is None:
                raise NotImplementedError(f'{redeem.name} поки ще не зроблено.')
            else:
                process_func(redeem=redeem)

        def process_spawn_redeem(self, redeem: RewardRedeemedObj):
            if redeem.user_name not in self.game.characters:
                self.game.add_character(redeem.user_name)

        def process_eyes_recolor_redeem(self, redeem: RewardRedeemedObj):
            self.process_recolor_redeem(redeem, AttrsCons.eyes_color.value)

        def process_body_recolor_redeem(self, redeem: RewardRedeemedObj):
            self.process_recolor_redeem(redeem, AttrsCons.body_color.value)

        def process_recolor_redeem(self, redeem: RewardRedeemedObj, attr: str):
            try:
                color = redeem.input
                re_res = re.search(r'(\d{1,3}), ?(\d{1,3}), ?(\d{1,3})', color)
                if re_res:
                    color = tuple(map(int, re_res.groups()))

                if color == pygame.Color('green'):
                    raise ProhibitedColor(color)

                color = pygame.Color(color)
            except ProhibitedColor:
                raise RedeemError(f'({redeem.input}) це заборонене значення кольору')
            except Exception:
                raise RedeemError(f'({redeem.input}) це не значення кольору')
            else:
                if character := self.game.get_character(redeem.user_name):
                    setattr(character, attr, color)
                    character.render_surface()

        def process_jump_redeem(self, redeem: RewardRedeemedObj):
            character = self.game.get_character(redeem.user_name)
            if character is not None and not character.is_falling:
                self.game.get_character(redeem.user_name).vertical_velocity -= JUMP_VELOCITY

        def process_everybody_jump(self, redeem: RewardRedeemedObj):
            for character in self.game.characters.copy().values():
                if character.name == redeem.user_name:
                    continue
                elif not character.is_falling:
                    character.vertical_velocity -= JUMP_VELOCITY

        def set_direction(self, redeem: RewardRedeemedObj):
            direction = redeem.input.strip()
            if not direction.isdigit() or int(direction) not in (-1, 0, 1):
                raise RedeemError(f'значення може бути тільки -1(ліво), 0(стоп), 1(право)')
            else:
                character = self.game.get_character(redeem.user_name)
                character.move_direction = int(direction)

    return GameRunner()


if __name__ == '__main__':
    g = get_game_obj()
    g.run()
