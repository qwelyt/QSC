class Percentage(object):
    _percentage = 0

    def __init__(self, percentage: float):
        self._percentage = percentage

    def __str__(self):
        return str(self._percentage)

    def __eq__(self, other):
        if isinstance(other, Percentage):
            return self._percentage == other.get()
        return False

    def apply(self, mm: float) -> float:
        return mm * self._percentage

    def get(self) -> float:
        return self._percentage
