from __future__ import annotations

from qsc.percentage import Percentage
from qsc.types import Real


class RaisedPosition:
    _x: Percentage
    _y: Percentage

    def __init__(self, x: Percentage | Real, y: Percentage | Real):
        self._x = x if type(x) is Percentage else Percentage(x)
        self._y = y if type(y) is Percentage else Percentage(y)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'RaisedPosition(x={self._x}, y={self._y})'

    def __eq__(self, other):
        if isinstance(other, RaisedPosition):
            return self._x == other.x and self._y == other.y
        return False

    @property
    def x(self) -> Percentage:
        return self._x

    @property
    def y(self) -> Percentage:
        return self._y

    def apply_x(self, val: Real) -> Real:
        return self.x.apply(val)

    def apply_y(self, val: Real) -> Real:
        return self.y.apply(val)
