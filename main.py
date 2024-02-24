import asyncio
import os
from typing import Dict, List

os.environ['VisualPygameOn'] = 'on'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import datetime
from twitchAPI.type import CustomRewardRedemptionStatus as RedeemStatus
from twitchAPI.twitch import Twitch
from twitchAPI.object.api import TwitchUser, CustomReward
from twitchAPI.pubsub import PubSub
from twitchAPI.oauth import UserAuthenticator, UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import webbrowser

from game_runner import get_game_obj
from game_components.errors import RedeemError
from global_data import Config
from redeems import RewardRedeemedObj
from logger import LOGGER

CONFIG = Config()
CONFIG.load_config()

APP_ID = os.getenv('TWITCH_APP_ID', CONFIG.creds.app_id)
APP_SECRET = os.getenv('TWITCH_APP_SECRET', CONFIG.creds.app_secret)
TARGET_CHANNEL = os.getenv('TWITCH_TARGET_CHANNEL', CONFIG.creds.target_channel)
BOT_CHANNEL = os.getenv('TWITCH_BOT_CHANNEL', CONFIG.creds.bot_channel)
# TODO add message
USER_SCOPE = [AuthScope.CHANNEL_READ_REDEMPTIONS,
              AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
              ]
BOT_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

BOT_BROWSER_PATH = CONFIG.get('bot_browser_path')
if BOT_BROWSER_PATH is None:
    BOT_BROWSER_PATH = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
BOT_BROWSER_NAME = 'twitch_bot_browser'

webbrowser.register(BOT_BROWSER_NAME, None, webbrowser.BackgroundBrowser(BOT_BROWSER_PATH))


class FunBot:

    def __init__(self):
        self.game_runner = None
        self.channel_twitch: Twitch = None
        self.bot_twitch: Twitch = None
        self.chat: Chat = None
        self.channel_owner_user: TwitchUser = None
        self.bot_user: TwitchUser = None
        self.pubsub: PubSub = None
        self.listen_channel_points_uuid: str = None

    async def run(self):
        try:
            await self.init()
            self.game_runner = get_game_obj()
            self.game_runner.game.load()
            await self.set_up_rewards()

            if self.game_runner.game.get_character(TARGET_CHANNEL) is None:
                self.game_runner.game.add_character(TARGET_CHANNEL)
            self.game_runner.run()
        except Exception as e:
            LOGGER.warning(e)
            print(e)
            await self.chat.send_message(TARGET_CHANNEL, 'Бот впав BibleThump')
        finally:
            if self.chat:
                try:
                    await self.chat.send_message(TARGET_CHANNEL, "Бот вимкнувся")
                    self.chat.stop()
                finally:
                    pass
            if self.pubsub:
                try:
                    self.pubsub.stop()
                finally:
                    pass

            if self.channel_twitch:
                try:
                    await self.channel_twitch.close()
                finally:
                    pass

            if self.bot_twitch:
                try:
                    await self.bot_twitch.close()
                finally:
                    pass

    async def init(self):
        # INIT USER
        twitch = await Twitch(APP_ID, APP_SECRET)
        auth_helper = UserAuthenticationStorageHelper(twitch, USER_SCOPE)
        await auth_helper.bind()
        self.channel_twitch = twitch

        # collect required users objects
        async for user in twitch.get_users(logins=[TARGET_CHANNEL, BOT_CHANNEL]):
            if user.login == TARGET_CHANNEL:
                self.channel_owner_user = user
            elif user.login == BOT_CHANNEL:
                self.bot_user = user
            if self.bot_user and self.channel_owner_user:
                break

        # INIT BOT
        bot_twitch = await Twitch(APP_ID, APP_SECRET)
        bot_auth = UserAuthenticator(bot_twitch, BOT_SCOPE)
        bot_token, bot_refresh_token = await bot_auth.authenticate(browser_name=BOT_BROWSER_NAME)
        await bot_twitch.set_user_authentication(bot_token, BOT_SCOPE, bot_refresh_token)
        self.bot_twitch = bot_twitch

        await self.subscribe_to_redemptions()
        await self.connect_co_chat()

    async def set_up_rewards(self):
        title_key = 'title'
        base_settings = {
            'title': 'стрибок',
            'prompt': None,
            'cost': 1,

            'is_enabled': True,
            'background_color': None,
            'is_user_input_required': False,
            'is_max_per_stream_enabled': False,
            'max_per_stream': None,
            'is_max_per_user_per_stream_enabled': False,
            'max_per_user_per_stream': None,
            'is_global_cooldown_enabled': False,

            'global_cooldown_seconds': None,
            'should_redemptions_skip_request_queue': False,
        }

        twitch = self.channel_twitch
        manageable_existing_rewards: List[CustomReward] = await twitch.get_custom_reward(self.broadcaster_id,
                                                                                         only_manageable_rewards=True)
        manageable_existing_rewards: Dict[str, CustomReward] = {r.title: r for r in manageable_existing_rewards}

        all_rewards: List[CustomReward] = await twitch.get_custom_reward(self.broadcaster_id)
        all_rewards: List[str] = [r.title for r in all_rewards if r.title not in manageable_existing_rewards]
        rewards_config = {r.title: r for r in CONFIG.redeems if r.title is not None}

        for redeem_name in self.game_runner.redeem_processors.keys():
            if redeem_name in manageable_existing_rewards:  # recreate
                await self.delete_reward(reward_id=manageable_existing_rewards.pop(redeem_name).id)

            if redeem_name not in manageable_existing_rewards and redeem_name not in all_rewards:
                data = base_settings.copy()
                data[title_key] = redeem_name
                data.update(rewards_config.get(redeem_name, {}))
                await self.create_reward(**data)
            else:
                # TODO make comparison
                pass

    async def create_reward(self, **kwargs):
        await self.channel_twitch.create_custom_reward(broadcaster_id=self.broadcaster_id, **kwargs)

    async def delete_reward(self, reward_id: str):
        await self.channel_twitch.delete_custom_reward(broadcaster_id=self.broadcaster_id, reward_id=reward_id)

    async def subscribe_to_redemptions(self):
        # LISTEN TO EVENTS
        self.pubsub = pubsub = PubSub(self.channel_twitch)
        pub_uuid = await pubsub.listen_channel_points(self.channel_owner_user.id, self.process_redeem_event)
        self.listen_channel_points_uuid = pub_uuid
        pubsub.start()

    async def connect_co_chat(self):
        # READ CHAT
        self.chat = chat = await Chat(self.bot_twitch)
        chat.register_event(ChatEvent.READY, self.ready_event)
        chat.register_command('стоп_бот', self.stop_bot_command)
        chat.start()

    @staticmethod
    async def ready_event(ready_event: EventData):
        await ready_event.chat.join_room(TARGET_CHANNEL)
        # time_str = datetime.datetime.now().strftime("%H:%M")
        # await ready_event.chat.send_message(TARGET_CHANNEL, text=f'Бот запрацював о {time_str} iamvol3Good')

    async def stop_bot_command(self, cmd: ChatCommand):
        if cmd.user.name == TARGET_CHANNEL:
            self.game_runner.is_running = False
            await cmd.send(f'Бот йде ґеть! BibleThump ')
        else:
            await cmd.send(f'@{cmd.user.name}, в тебе немає влади! iamvol3U ')

    async def process_redeem_event(self, _, request_payload):
        redeem_obj = RewardRedeemedObj(request_payload)
        fulfilled = False
        try:
            self.game_runner.process_redeem(redeem_obj)
        except RedeemError as e:
            text = f'@{redeem_obj.user_name}, не вийшло застосувати "{redeem_obj.name}", бо {e}'
            LOGGER.warning(text)
            await self.chat.send_message(TARGET_CHANNEL, text)
        except Exception as e:
            LOGGER.warning(e)
        else:
            fulfilled = True

        # TODO return channel points
        if not redeem_obj.skip_queue:
            status = RedeemStatus.FULFILLED if fulfilled else RedeemStatus.CANCELED

            try:
                await self.channel_twitch.update_redemption_status(broadcaster_id=self.broadcaster_id,
                                                                   reward_id=redeem_obj.reward_id,
                                                                   redemption_ids=redeem_obj.id,
                                                                   status=status,
                                                                   )
                LOGGER.info(f'Redemption {redeem_obj.id} status is {status}')
            except Exception as e:
                LOGGER.error(str(e))

    @property
    def program_works(self) -> bool:
        return self.game_runner.is_running == 1

    @property
    def broadcaster_id(self) -> str:
        return self.channel_owner_user.id


def main():
    bot = FunBot()
    asyncio.run(bot.run())
    bot.game_runner.game.save()


if __name__ == '__main__':
    main()
