import asyncio
import os
import time
from typing import Dict, List, Optional

os.environ['VisualPygameOn'] = 'on'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import datetime
from twitchAPI.type import CustomRewardRedemptionStatus as RedeemStatus, PredictionStatus
from twitchAPI.twitch import Twitch
from twitchAPI.object.api import TwitchUser, CustomReward, Prediction
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

from _thread import start_new_thread

CONFIG = Config()
CONFIG.load_config()

APP_ID = os.getenv('TWITCH_APP_ID', CONFIG.creds.app_id)
APP_SECRET = os.getenv('TWITCH_APP_SECRET', CONFIG.creds.app_secret)
TARGET_CHANNEL = os.getenv('TWITCH_TARGET_CHANNEL', CONFIG.creds.target_channel)
BOT_CHANNEL = os.getenv('TWITCH_BOT_CHANNEL', CONFIG.creds.bot_channel)
# TODO add message
USER_SCOPE = [AuthScope.CHANNEL_READ_REDEMPTIONS,
              AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
              AuthScope.CHANNEL_MANAGE_PREDICTIONS,
              ]
BOT_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, ]

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
        self.messages_queue: List[str] = []
        self.current_prediction: Optional[Prediction] = None

    async def run(self):
        try:
            await self.init()
            self.game_runner = get_game_obj()
            self.game_runner.game.load()
            await self.set_up_rewards()

            if self.game_runner.game.get_character(TARGET_CHANNEL) is None:
                self.game_runner.game.add_character(TARGET_CHANNEL)

            start_new_thread(asyncio.run, (self.check_for_send_messages(),))

            self.game_runner.game.send_msg = self.send_message
            self.game_runner.game.create_prediction = self.sync_create_predict
            self.game_runner.game.end_prediction = self.sync_end_prediction
            self.game_runner.run()
        except Exception as e:
            # import traceback
            # print(traceback.format_exc())
            LOGGER.error(e)
            # await self.chat.send_message(TARGET_CHANNEL, 'Бот впав BibleThump')
        finally:
            if self.current_prediction:
                await self.end_prediction(status=PredictionStatus.CANCELED)

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
        auth_helper = UserAuthenticationStorageHelper(bot_twitch, BOT_SCOPE,
                                                      storage_path='bot_token.json',
                                                      auth_generator_func=self.bot_auth)
        await auth_helper.bind()
        self.bot_twitch = bot_twitch

        await self.subscribe_to_redemptions()
        await self.connect_co_chat()

    @staticmethod
    async def bot_auth(twitch, scopes):
        auth = UserAuthenticator(twitch, scopes=scopes)
        return await auth.authenticate(browser_name=BOT_BROWSER_NAME)

    async def set_up_rewards(self):
        title_key = 'title'

        twitch = self.channel_twitch
        manageable_rewards: List[CustomReward] = await twitch.get_custom_reward(self.broadcaster_id,
                                                                                only_manageable_rewards=True)
        manageable_rewards: Dict[str, CustomReward] = {r.title: r for r in manageable_rewards}

        all_rewards: List[CustomReward] = await twitch.get_custom_reward(self.broadcaster_id)
        all_rewards: List[str] = [r.title for r in all_rewards if r.title not in manageable_rewards]
        rewards_config = {r_data[title_key]: r_data for r_data in CONFIG.custom_rewards if r_data.get(title_key)}

        # delete rewards which are not in config
        for reward_name in tuple(manageable_rewards.keys()):
            if reward_name not in self.game_runner.redeem_processors:
                await self.delete_reward(reward_id=manageable_rewards.pop(reward_name).id)

        for reward_name in self.game_runner.redeem_processors.keys():
            try:
                if reward_name in manageable_rewards:
                    try:
                        await self.update_reward_if_required(reward=manageable_rewards[reward_name],
                                                             reward_config=rewards_config.get(reward_name, {}))
                    except Exception as e:
                        LOGGER.error(f'Failed to update {reward_name}')
                        raise e

                elif reward_name in all_rewards:
                    LOGGER.error(f'Failed to create "{reward_name}" because its already exists in unmanageable rewards')

                else:
                    try:
                        await self.create_reward(reward_name=reward_name,
                                                 rewards_config=rewards_config.get(reward_name, {}))
                    except Exception as e:
                        LOGGER.warning(f'Failed to create reward "{reward_name}"')
                        raise e
                    else:
                        LOGGER.info(f'Created reward "{reward_name}"')
            except Exception as e:
                LOGGER.error(f'Failed to process "{reward_name}" update/create\n{e}')

    async def update_reward_if_required(self, reward: CustomReward, reward_config: dict):
        update_dict = {}
        for k, v in reward_config.items():
            if hasattr(reward, k) and getattr(reward, k) != v:
                # TODO not all attrs the same, at least is_max_per_stream_enabled
                update_dict[k] = v

        if update_dict:
            await self.channel_twitch.update_custom_reward(broadcaster_id=self.broadcaster_id,
                                                           reward_id=reward.id,
                                                           **update_dict)
            LOGGER.info(f'Updated {reward.title} with {update_dict}')
        else:
            LOGGER.info(f'Nothing to update in "{reward.title}"')

    async def create_reward(self, reward_name: str, rewards_config: dict):
        data = {
            'title': reward_name,
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
        data.update(rewards_config)
        if not data['title']:
            raise Exception(f'Can`t create reward without title, {data}')

        await self.channel_twitch.create_custom_reward(broadcaster_id=self.broadcaster_id, **data)

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

    async def ready_event(self, ready_event: EventData):
        await ready_event.chat.join_room(TARGET_CHANNEL)
        # time_str = datetime.datetime.now().strftime("%H:%M")
        # self.send_message(f'Бот запрацював о {time_str} iamvol3Good')

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

        if redeem_obj.fulfill_now and not redeem_obj.skip_queue:
            try:
                await self.manage_spent_points(redeem_obj=redeem_obj, fulfilled=fulfilled)
            except Exception as e:
                LOGGER.error(str(e))

    async def manage_spent_points(self, redeem_obj: RewardRedeemedObj, fulfilled: bool = True):
        status = RedeemStatus.FULFILLED if fulfilled else RedeemStatus.CANCELED
        try:
            await self.channel_twitch.update_redemption_status(broadcaster_id=self.broadcaster_id,
                                                               reward_id=redeem_obj.reward_id,
                                                               redemption_ids=redeem_obj.id,
                                                               status=status,
                                                               )
            LOGGER.debug(f'Redemption {redeem_obj.name} from {redeem_obj.user_name} status is {status}')
        except Exception as e:
            LOGGER.error(str(e))

    def send_message(self, msg: str) -> None:
        self.messages_queue.append(msg)

    async def check_for_send_messages(self):
        try:
            while self.program_works:
                while self.messages_queue:
                    await self.chat.send_message(TARGET_CHANNEL, self.messages_queue.pop(0))
                await asyncio.sleep(1)
        except Exception as e:
            LOGGER.error(f'Messages thread is dead\n{e}')

    def sync_create_predict(self, title: str, outcomes: List[str], time_to_predict: int = 60):
        start_new_thread(asyncio.run, (self.create_prediction(title=title,
                                                              outcomes=outcomes,
                                                              time_to_predict=time_to_predict),))

    async def create_prediction(self, title: str, outcomes: List[str], time_to_predict: int = 60):
        try:
            self.current_prediction = await self.channel_twitch.create_prediction(broadcaster_id=self.broadcaster_id,
                                                                                  title=title,
                                                                                  outcomes=outcomes,
                                                                                  prediction_window=time_to_predict,
                                                                                  )
        except Exception as e:
            LOGGER.error(f'Failed to start prediction {title}({outcomes}) \n{e}')

    def sync_end_prediction(self, status: PredictionStatus, winner: Optional[str] = None, reason: str = ''):
        start_new_thread(asyncio.run, (self.end_prediction(status=status, winner=winner, reason=reason),))

    async def end_prediction(self, status: PredictionStatus, winner: Optional[str] = None, reason: str = ''):
        if self.current_prediction:
            try:
                if winner:
                    winners = [w.id for w in self.current_prediction.outcomes if w.title == winner]
                    if not winners:
                        raise Exception(f'Any winner id do not match with {winner}')
                    winner_id = winners[0]
                else:
                    winner_id = None
                # TODO if not found all ok
                await self.channel_twitch.end_prediction(broadcaster_id=self.broadcaster_id,
                                                         prediction_id=self.current_prediction.id,
                                                         status=status,
                                                         winning_outcome_id=winner_id
                                                         )
                if status == PredictionStatus.LOCKED:
                    # TODO await self.chat.send_message(TARGET_CHANNEL, f"Час ставок закінчився! {reason}")
                    pass
                elif status == PredictionStatus.CANCELED and not winner:
                    await self.chat.send_message(TARGET_CHANNEL, f"Предікшн відмінено! {reason}")
            except Exception as e:
                LOGGER.error(f'Failed to end prediction {self.current_prediction.title} status={status}, winner={winner}')
                LOGGER.error(f'Reason {e}')
                # await self.chat.send_message(TARGET_CHANNEL,
                #                              f'@{self.channel_owner_user.login} не вийшло змінити предікшн')
            else:
                LOGGER.info(f'Changed prediction status to {status} without errors')
            finally:
                if status == PredictionStatus.CANCELED:
                    self.current_prediction = None

        else:
            LOGGER.warning(f'Have not predict to end!')

    @property
    def program_works(self) -> bool:
        return self.game_runner.is_running == 1

    @property
    def broadcaster_id(self) -> str:
        return self.channel_owner_user.id

    @property
    def bot_broadcaster_id(self) -> str:
        return self.bot_user.id


def main():
    bot = FunBot()
    asyncio.run(bot.run())
    if bot.game_runner:
        bot.game_runner.game.save()


if __name__ == '__main__':
    main()
