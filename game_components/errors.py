class ProhibitedColor(Exception):
    def __init__(self, color):
        self.color = color


class RedeemError(Exception):
    def __init__(self, msg: str = '', send_msg: bool = True):
        self.msg: str = msg
        self.send_msg: bool = send_msg

    def __str__(self):
        return self.msg
