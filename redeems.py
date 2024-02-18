REDEMPTION_NAME: str = 'redeem_name'
INPUT_C: str = 'input'
USERNAME_C: str = 'user_name'


class RewardRedeemedObj:
    def __init__(self, payload: dict):
        redemption = payload['data']['redemption']
        self.name: str = redemption['reward']['title'].lower()
        self.input: str = redemption.get('user_input')
        self.user_name: str = redemption['user']['display_name']
        self.id = redemption['id']
        self.reward_id = redemption['reward']['id']
        self.skip_queue: bool = redemption['reward']['should_redemptions_skip_request_queue']
