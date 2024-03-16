from typing import Callable
from twitchAPI.type import PredictionStatus


class EventPredictionMixin:
    def __init__(self, update_method: Callable):
        self.update_prediction: Callable = update_method

    def end_prediction(self, winner: str, reason: str = ""):
        self.update_prediction(status=PredictionStatus.RESOLVED, winner=winner, reason=reason)

    def lock_prediction(self):
        self.update_prediction(status=PredictionStatus.LOCKED)

    def cancel_prediction(self, reason: str = ""):
        self.update_prediction(status=PredictionStatus.CANCELED, reason=reason)
