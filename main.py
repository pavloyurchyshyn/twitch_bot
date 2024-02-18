import asyncio
import os
import datetime
from twitchAPI.type import CustomRewardRedemptionStatus as RedeemStatus
from twitchAPI.twitch import Twitch
from twitchAPI.object.api import TwitchUser
from twitchAPI.pubsub import PubSub
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand

from game_runner import GameRunner, RedeemError
from redeems import RewardRedeemedObj
from logger import LOGGER

APP_ID = os.getenv('TWITCH_APP_ID')
APP_SECRET = os.getenv('TWITCH_APP_SECRET')
TARGET_CHANNEL = os.getenv('TWITCH_TARGET_CHANNEL')

USER_SCOPE = [AuthScope.CHAT_READ,
              AuthScope.CHAT_EDIT,
              AuthScope.CHANNEL_READ_REDEMPTIONS,
              AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
              ]


class FunBot:

    def __init__(self):
        self.game = GameRunner()
        self.twitch: Twitch = None
        self.chat: Chat = None
        self.channel_owner_user: TwitchUser = None
        self.pubsub: PubSub = None
        self.listen_channel_points_uuid: str = None

    async def run(self):
        try:
            await self.init()
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
                    # await self.chat.send_message(TARGET_CHANNEL, "Бот вимкнувся")
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
        auth = UserAuthenticator(twitch, USER_SCOPE)
        token, refresh_token = await auth.authenticate()
        await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)
        self.twitch = twitch

        self.pubsub = pubsub = PubSub(twitch)
        async for user in twitch.get_users(logins=[TARGET_CHANNEL]):
            if user.login == TARGET_CHANNEL:
                self.channel_owner_user = user
                break

        pub_uuid = await pubsub.listen_channel_points(self.channel_owner_user.id, self.redeem_event)
        self.listen_channel_points_uuid = pub_uuid
        pubsub.start()

        self.chat = chat = await Chat(twitch)
        chat.register_event(ChatEvent.READY, self.ready_event)
        chat.register_command('стоп_бот', self.stop_bot_command)
        chat.start()

    @staticmethod
    async def ready_event(ready_event: EventData):
        await ready_event.chat.join_room(TARGET_CHANNEL)
        # time_str = datetime.datetime.now().strftime("%H:%M")
        # await ready_event.chat.send_message(TARGET_CHANNEL,
        #                                     text=f'Всім ку від бота, він запрацював! Нинька є {time_str} iamvol3Good')

    async def stop_bot_command(self, cmd: ChatCommand):
        if cmd.user.name == TARGET_CHANNEL:
            self.game.is_running = False
            await cmd.send(f'Бот йде ґеть! BibleThump ')
        else:
            await cmd.send(f'@{cmd.user.name}, в тебе немає влади! iamvol3U ')

    async def redeem_event(self, redeem_uuid, request_payload):
        redeem_obj = RewardRedeemedObj(request_payload)
        ok = True
        try:
            self.game.process_redeem(redeem_obj)
        except RedeemError as e:
            text = f'@{redeem_obj.user_name}, не вийшло застосувати "{redeem_obj.name}", бо {e}'
            LOGGER.warning(text)
            await self.chat.send_message(TARGET_CHANNEL, text)
            ok = False
        except Exception as e:
            LOGGER.warning(e)
            ok = False
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
