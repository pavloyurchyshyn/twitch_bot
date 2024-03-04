REDEMPTION_NAME: str = 'redeem_name'
INPUT_C: str = 'input'
USERNAME_C: str = 'user_name'


class RewardRedeemedObj:
    def __init__(self, payload: dict):
        redemption = payload['data']['redemption']
        self.name: str = redemption['reward']['title'].lower()
        self.input: str = redemption.get('user_input')
        self.user_name: str = self.normalize_nickname(redemption['user']['display_name'])
        self.user_id: str = redemption['user']['id']
        self.id = redemption['id']
        self.reward_id = redemption['reward']['id']
        self.channel_id: str = redemption['reward']['channel_id']
        self.skip_queue: bool = redemption['reward']['should_redemptions_skip_request_queue']

        self.fulfill_now: bool = True

    @staticmethod
    def normalize_nickname(name: str) -> str:
        name = str(name)
        if name.startswith('@'):
            name = name.removeprefix('@')
        return name.strip().lower()
