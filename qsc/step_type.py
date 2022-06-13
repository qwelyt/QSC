from enum import Enum

from qsc.raised_position import RaisedPosition


class StepType(Enum):
    CENTER = RaisedPosition(0, 0),
    DOWN = RaisedPosition(0, -1)
    LEFT = RaisedPosition(-1, 0),
    RIGHT = RaisedPosition(1, 0),
    UP = RaisedPosition(0, 1),
