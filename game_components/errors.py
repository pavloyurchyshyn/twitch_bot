class ProhibitedColor(Exception):
    def __init__(self, color):
        self.color = color


class RedeemError(Exception):
    pass
