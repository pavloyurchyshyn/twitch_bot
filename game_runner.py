class RedeemsNames:
    spawn = "з'явитись"
    jump = "стрибок"
    recolor_body = "перефарбувати тіло"
    recolor_eyes = "перефарбувати очі"
    set_direction = "змінити напрям"
    every_body_jump = "всім іншим підстрибнути"
    start_storm = "запустити шторм"
    walk_around = "блукати"
    kiss_person = "поцілювати"
    kick_person = "штовхнути"
    start_duel = "почати дуель"
    commands_to_ignore = [
        "замовити музику",

    ]


def get_game_obj() -> 'GameRunner':
    from os import environ
    import re

    environ['VisualPygameOn'] = 'on'
    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

    from time import time
    from typing import Dict, Callable
    from pygame import init, mixer

    init()
    import pygame
    mixer.init()
    from pygame import display, event as EVENT
    from pygame.time import Clock
    from pygame import quit as close_program_pygame

    display.set_caption('twitch_entities')

    from redeems import RewardRedeemedObj
    from game_components.screen import MAIN_DISPLAY
    from game_components.game import Game
    from game_components.utils import DEFAULT_FONT, normalize_color
    from game_components.character.user_character import Character, JUMP_VELOCITY, AttrsCons
    from game_components.AI import base
    from game_components.AI.go_and_kiss import GoAndKiss
    from game_components.AI.go_and_kick import GoAndKick
    from game_components.errors import RedeemError, ProhibitedColor
    from logger import LOGGER

    ONLINE_TEXT = DEFAULT_FONT.render('Бот працює', 1, [255, 255, 255], [100, 100, 100])
    ONLINE_TEXT_POS = list(MAIN_DISPLAY.get_rect().midbottom)
    ONLINE_TEXT_POS[1] -= ONLINE_TEXT.get_height() - 2

    class GameRunner:
        FPS = 60

        def __init__(self):
            self.is_running: int = 1
            self.game: Game = Game()
            self.redeem_processors: Dict[str, Callable] = {
                RedeemsNames.spawn: self.process_spawn_redeem,
                RedeemsNames.jump: self.process_jump_redeem,
                RedeemsNames.recolor_body: self.process_body_recolor_redeem,
                RedeemsNames.recolor_eyes: self.process_eyes_recolor_redeem,
                RedeemsNames.set_direction: self.set_direction,
                RedeemsNames.every_body_jump: self.process_everybody_jump,
                RedeemsNames.start_storm: self.process_start_storm,
                RedeemsNames.walk_around: self.process_walk_around,
                RedeemsNames.kiss_person: self.process_kiss_person,
                RedeemsNames.kick_person: self.process_kick_person,
                RedeemsNames.start_duel: self.process_start_duel,
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
                self.draw_bot_online()

                display.update()

        @staticmethod
        def draw_bot_online():
            MAIN_DISPLAY.blit(ONLINE_TEXT, ONLINE_TEXT_POS)

        @staticmethod
        def draw_fps(fps):
            fps_text = DEFAULT_FONT.render(str(int(fps)), True, [255, 255, 255], [0, 0, 0])
            MAIN_DISPLAY.blit(fps_text, (0, 0))

        def process_redeem(self, redeem: RewardRedeemedObj):
            LOGGER.info(f'{redeem.user_name} застосував "{redeem.name}" з аргументом {redeem.input}')

            process_func = self.redeem_processors.get(redeem.name)
            if redeem.name in RedeemsNames.commands_to_ignore:
                return
            elif process_func is None:
                raise NotImplementedError(f'{redeem.name} поки ще не зроблено.')
            else:
                process_func(redeem=redeem)

        def process_spawn_redeem(self, redeem: RewardRedeemedObj):
            user_name = self.normalize_nickname(redeem.user_name)
            if user_name not in self.game.characters:
                self.game.add_character(user_name)

        def process_eyes_recolor_redeem(self, redeem: RewardRedeemedObj):
            self.process_recolor_redeem(redeem, AttrsCons.eyes_color.value)

        def process_body_recolor_redeem(self, redeem: RewardRedeemedObj):
            self.process_recolor_redeem(redeem, AttrsCons.body_color.value)

        def process_recolor_redeem(self, redeem: RewardRedeemedObj, attr: str):
            try:
                color = redeem.input
                re_res = re.search(r'(\d{1,3}),? ?(\d{1,3}),? ?(\d{1,3})', color)
                if re_res:
                    color = normalize_color(tuple(map(int, re_res.groups())))

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
            if self.game.check_if_any_event_is_blocking():
                return
            direction = redeem.input.strip()
            try:
                if int(direction) not in (-1, 0, 1):
                    raise RedeemError(f'значення може бути тільки -1(ліво), 0(стоп), 1(право), не "{direction}"')

                # TODO make cancel?
                if int(direction) == 0:
                    ai = self.game.characters_AI.get(redeem.user_name)
                    if ai:
                        ai.clear()
                character = self.game.get_character(redeem.user_name)
                character.move_direction = int(direction)
            except Exception:
                pass

        def process_start_storm(self, *_, **__):
            if not self.game.check_if_any_event_is_blocking():
                self.game.make_storm()
            else:
                raise RedeemError('триває інший івент')

        def process_walk_around(self, redeem: RewardRedeemedObj):
            ai = self.game.characters_AI.get(redeem.user_name)
            if ai is None:
                self.game.add_ai_for(redeem.user_name)
            if ai.current_task is None:
                ai.run_idle_walking()
            elif isinstance(ai.current_task, base.IdleWalk):
                pass
            else:
                raise RedeemError(f'Покищо персонаж робить {ai.current_task.name}')

        def process_kiss_person(self, redeem: RewardRedeemedObj):
            target_name: str = self.normalize_nickname(str(redeem.input))
            self.validate_interaction_with_other_character(user_name=redeem.user_name, target_name=target_name)

            ai = self.game.get_character_ai(redeem.user_name)
            self.validate_current_task_not_blocking(ai)

            if ai.current_task and ai.current_task.endless and ai.current_task.skippable:
                ai.finish_current_task()
            target_character: Character = self.game.get_character(target_name)
            ai.add_task(GoAndKiss(target=target_character))

        def process_kick_person(self, redeem: RewardRedeemedObj):
            target_name: str = self.normalize_nickname(str(redeem.input))
            user_name = self.normalize_nickname(str(redeem.user_name))
            self.validate_interaction_with_other_character(user_name=user_name, target_name=target_name)

            ai = self.game.get_character_ai(redeem.user_name)
            self.validate_current_task_not_blocking(ai)

            if ai.current_task and ai.current_task.endless and ai.current_task.skippable:
                ai.finish_current_task()
            target_character: Character = self.game.get_character(target_name)
            ai.add_task(GoAndKick(target=target_character))

        def process_start_duel(self, redeem: RewardRedeemedObj):
            target_name: str = self.normalize_nickname(str(redeem.input))
            user_name: str = self.normalize_nickname(str(redeem.user_name))
            if target_name == user_name:
                raise RedeemError('не можна бити себе! iamvol3U')
            self.validate_interaction_with_other_character(user_name=user_name, target_name=target_name)

            ai = self.game.get_character_ai(user_name)
            self.validate_current_task_not_blocking(ai)

            target_ai = self.game.get_character_ai(target_name)
            self.validate_current_task_not_blocking(target_ai)

            if self.game.check_if_any_event_is_blocking() or \
                    self.game.check_if_redeem_is_blocked_by_events(redeem.name):
                raise RedeemError('триває інший івент')

            if ai.current_task and not ai.current_task.skippable:
                raise RedeemError('виконується задача яку не можна пропустити')
            elif target_ai.current_task and not target_ai.current_task.skippable:
                raise RedeemError(f'опонент виконує задачу яку не можна пропустити')

            self.game.start_duel(duelist_1=self.game.get_character(user_name),
                                 duelist_2=self.game.get_character(target_name))

        def validate_interaction_with_other_character(self, user_name: str, target_name: str):
            self.validate_user_character_exists(user_name)
            self.validate_target_person_exists(target_name)

        @staticmethod
        def validate_current_task_not_blocking(ai):
            if ai.current_task and ai.current_task.is_blocking:
                raise RedeemError(f'персонаж дороблює {ai.current_task.name}')

        def validate_user_character_exists(self, name: str):
            if name not in self.game.characters:
                raise RedeemError(f'твій персонаж не існує. Потрібно спочатку створити.')

        def validate_target_person_exists(self, name: str):
            if name not in self.game.characters:
                raise RedeemError(f"персонаж з ім'ям {name} не існує")

        @staticmethod
        def normalize_nickname(name: str) -> str:
            if name.startswith('@'):
                name = name.removeprefix('@')
            return name.strip().lower()

    return GameRunner()


if __name__ == '__main__':
    g = get_game_obj()
    g.game.add_character('Dummy')
    g.run()
