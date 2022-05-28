

class Percentage(object):
    _percentage = 0

    def __init__(self, percentage: float):
        self._percentage = percentage

    def __str__(self):
        return str(self._percentage)

    def apply(self, mm: float) -> float:
        return mm * self._percentage

    def get(self) -> float:
        return self._percentage
