from qsc.step_type import StepType
from qsc.mm import MM
from qsc.percentage import Percentage
from qsc.u import U

ValueTypes = "MM | U | Percentage"


class StepSettings(object):
    _stepType: StepType
    _stepHeight: ValueTypes
    _raisedWidth: ValueTypes

    def __init__(self):
        self._stepHeight = Percentage(0.5)

    def step_type(self, step_type: StepType):
        self._stepType = step_type
        return self

    def step_height(self, step_height: ValueTypes):
        if step_height is not None:
            self._stepHeight = step_height
        return self

    def raised_width(self, raised_width: ValueTypes):
        self._raisedWidth = raised_width
        return self

    def get_type(self):
        return self._stepType

    def get_step_height(self):
        return self._stepHeight

    def get_raised_width(self):
        return self._raisedWidth

    def apply_step_height(self, height) -> float:
        if type(self._stepHeight) is MM:
            return self._stepHeight.mm().get()
        elif type(self._stepHeight) is U:
            return self._stepHeight.mm().get()
        elif type(self._stepHeight) is Percentage:
            return self._stepHeight.apply(height)
        else:
            return height
