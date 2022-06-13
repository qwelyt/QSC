from qsc.step_type import StepType
from qsc.mm import MM
from qsc.percentage import Percentage
from qsc.u import U
from qsc.raised_position import RaisedPosition

ValueTypes = "MM | U | Percentage"


class StepSettings(object):
    _stepHeight: ValueTypes
    _raisedWidth: ValueTypes
    _raisedLength: ValueTypes
    _raisedPosition: RaisedPosition

    def __init__(self):
        self._stepHeight = Percentage(0.5)

    def step_height(self, step_height: ValueTypes):
        if step_height is not None:
            self._stepHeight = step_height
        return self

    def raised_width(self, raised_width: ValueTypes):
        self._raisedWidth = raised_width
        return self

    def raised_length(self, raised_length: ValueTypes):
        self._raisedLength = raised_length
        return self

    def raised_position(self, raised_position: RaisedPosition):
        self._raisedPosition = raised_position
        return self

    def get_step_height(self):
        return self._stepHeight

    def get_raised_width(self):
        return self._raisedWidth

    def get_raised_length(self):
        return self._raisedLength

    def get_raised_position(self):
        return self._raisedPosition

    def apply_step_height(self, height) -> float:
        if type(self._stepHeight) is MM:
            return self._stepHeight.mm().get()
        elif type(self._stepHeight) is U:
            return self._stepHeight.mm().get()
        elif type(self._stepHeight) is Percentage:
            return self._stepHeight.apply(height)
        else:
            return height
