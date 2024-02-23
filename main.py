import asyncio
import os
os.environ['VisualPygameOn'] = 'on'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import datetime
from twitchAPI.type import CustomRewardRedemptionStatus as RedeemStatus
from twitchAPI.twitch import Twitch
from twitchAPI.object.api import TwitchUser
from twitchAPI.pubsub import PubSub
from twitchAPI.oauth import UserAuthenticator, UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import webbrowser

from game_runner import get_game_obj
from game_components.errors import RedeemError
from redeems import RewardRedeemedObj
from logger import LOGGER

APP_ID = os.getenv('TWITCH_APP_ID')
APP_SECRET = os.getenv('TWITCH_APP_SECRET')
TARGET_CHANNEL = os.getenv('TWITCH_TARGET_CHANNEL')
BOT_CHANNEL = os.getenv('TWITCH_BOT_CHANNEL')
USER_SCOPE = [AuthScope.CHANNEL_READ_REDEMPTIONS,
              AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
              ]
BOT_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))


class FunBot:

    def __init__(self):
        self.game = None
        self.twitch: Twitch = None
        self.bot_twitch: Twitch = None
        self.chat: Chat = None
        self.channel_owner_user: TwitchUser = None
        self.bot_user: TwitchUser = None
        self.pubsub: PubSub = None
        self.listen_channel_points_uuid: str = None

    async def run(self):
        try:
            await self.init()
            self.game = get_game_obj()
            self.game.game.load()
            if self.game.game.get_character(TARGET_CHANNEL) is None:
                self.game.game.add_character(TARGET_CHANNEL)
            self.game.run()
        except Exception as e:
            LOGGER.warning(e)
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

            try:
                await self.twitch.close()
            finally:
                pass

    async def init(self):
        twitch = await Twitch(APP_ID, APP_SECRET)
        auth_helper = UserAuthenticationStorageHelper(twitch, USER_SCOPE)
        await auth_helper.bind()

        async for user in twitch.get_users(logins=[TARGET_CHANNEL, BOT_CHANNEL]):
            if user.login == TARGET_CHANNEL:
                self.channel_owner_user = user
            elif user.login == BOT_CHANNEL:
                self.bot_user = user
            if self.bot_user and self.channel_owner_user:
                break

        bot_twitch = await Twitch(APP_ID, APP_SECRET)
        bot_auth = UserAuthenticator(bot_twitch, BOT_SCOPE)
        bot_token, bot_refresh_token = await bot_auth.authenticate(browser_name='edge')
        await bot_twitch.set_user_authentication(bot_token, BOT_SCOPE, bot_refresh_token)
        self.twitch = twitch
        self.bot_twitch = bot_twitch

        self.pubsub = pubsub = PubSub(twitch)
        pub_uuid = await pubsub.listen_channel_points(self.channel_owner_user.id, self.redeem_event)
        self.listen_channel_points_uuid = pub_uuid
        pubsub.start()

        self.chat = chat = await Chat(bot_twitch)
        chat.register_event(ChatEvent.READY, self.ready_event)
        chat.register_command('стоп_бот', self.stop_bot_command)
        chat.start()

    @staticmethod
    async def ready_event(ready_event: EventData):
        await ready_event.chat.join_room(TARGET_CHANNEL)
        time_str = datetime.datetime.now().strftime("%H:%M")
        await ready_event.chat.send_message(TARGET_CHANNEL,
                                            text=f'Бот запрацював о {time_str} iamvol3Good')

    async def stop_bot_command(self, cmd: ChatCommand):
        if cmd.user.name == TARGET_CHANNEL:
            self.game.is_running = False
            await cmd.send(f'Бот йде ґеть! BibleThump ')
        else:
            await cmd.send(f'@{cmd.user.name}, в тебе немає влади! iamvol3U ')

    async def redeem_event(self, redeem_uuid, request_payload):
        redeem_obj = RewardRedeemedObj(request_payload)
        try:
            self.game.process_redeem(redeem_obj)
        except RedeemError as e:
            text = f'@{redeem_obj.user_name}, не вийшло застосувати "{redeem_obj.name}", бо {e}'
            LOGGER.warning(text)
            await self.chat.send_message(TARGET_CHANNEL, text)
        except Exception as e:
            LOGGER.warning(e)
        # else:
        #    TODO spend points
        finally:
            # TODO return channel points
            pass
            # if not redeem_obj.skip_queue:
            #     await self.twitch.update_redemption_status(self.broadcaster_id,
            #                                                redeem_obj.reward_id,
            #                                                redeem_obj.id,
            #                                                RedeemStatus.FULFILLED if ok else RedeemStatus.CANCELED,
            #                                                )

    @property
    def program_works(self) -> bool:
        return self.game.is_running == 1

    @property
    def broadcaster_id(self) -> str:
        return self.channel_owner_user.id


def main():
    bot = FunBot()
    asyncio.run(bot.run())
    bot.game.game.save()


if __name__ == '__main__':
    main()
