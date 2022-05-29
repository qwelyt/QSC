import cadquery as cq
from qsc.types import Real
from qsc.step_settings import StepSettings
from qsc.step_type import StepType
from qsc.mm import MM
from qsc.u import U
from qsc.percentage import Percentage
from qsc.rounding_type import RoundingType


class BaseSettings(object):
    _isoEnter = False
    _shoulderLength = Percentage(0.5)
    _stepSettings = None
    _width = 0
    _length = 0
    _height = 0
    _diff = 0
    _bottom_rounding_type = None
    _bottom_rounding = 0
    _top_rounding_type = None
    _top_rounding = 0

    def __init__(self):
        pass

    def step_settings(self, step_settings: StepSettings):
        self._stepSettings = step_settings
        return self

    def width(self, width: Real):
        self._width = width
        return self

    def length(self, length: Real):
        self._length = length
        return self

    def height(self, height: Real):
        self._height = height
        return self

    def diff(self, diff: Real):
        self._diff = diff
        return self

    def iso_enter(self, iso_enter: bool, shoulder_length: "Percentage | MM | U" = Percentage(0.5)):
        self._isoEnter = iso_enter
        self._shoulderLength = shoulder_length
        return self

    def top_rounding(self, top_rounding: Real, type: RoundingType):
        self._top_rounding = top_rounding
        self._top_rounding_type = type
        return self

    def bottom_rounding(self, bottom_rounding: Real, type: RoundingType):
        self._bottom_rounding = bottom_rounding
        self._bottom_rounding_type = type
        return self

    def get_step_settings(self) -> StepSettings:
        return self._stepSettings

    def get_iso_enter(self) -> bool:
        return self._isoEnter

    def get_shoulder_length(self) -> Percentage:
        return self._shoulderLength

    def get_width(self) -> Real:
        return self._width

    def get_length(self) -> Real:
        return self._length

    def get_height(self) -> Real:
        return self._height

    def get_diff(self) -> Real:
        return self._diff

    def get_top_rounding(self) -> Real:
        return self._top_rounding

    def get_top_rounding_type(self) -> RoundingType:
        return self._top_rounding_type

    def get_bottom_rounding(self) -> Real:
        return self._bottom_rounding

    def get_bottom_rounding_type(self) -> RoundingType:
        return self._bottom_rounding_type


class Base(object):
    _settings = None

    def __init__(self, settings: BaseSettings):
        self._settings = settings

    def build(self):
        if self._settings.get_iso_enter() and self._settings.get_step_settings().get_type() is not None:
            return self._stepped_iso()
        elif self._settings.get_iso_enter():
            return self._iso_enter()
        elif self._settings.get_step_settings().get_type() is not None:
            return self._stepped()
        else:
            return self._basic()

    @staticmethod
    def _rect(width: Real, depth: Real, delta: Real = 0.0, op: RoundingType = None):
        rect = (cq.Sketch().rect(width, depth))

        if delta == 0 or op is None:
            return rect
        elif op == RoundingType.CHAMFER:
            return rect.vertices().chamfer(delta)
        elif op == RoundingType.FILLET:
            return rect.vertices().fillet(delta)
        else:
            return rect

    def _box(self, width: Real, depth: Real, height: Real, diff: Real, bottom_rounding: Real, bottom_rounding_type: RoundingType, top_rounding: Real,
             top_rounding_type: RoundingType):
        a = self._rect(width, depth, bottom_rounding, bottom_rounding_type)
        b = self._rect(width + diff, depth + diff, top_rounding, top_rounding_type)
        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0, 0, height))))
                .loft()
                )

    def _iso_form(self, delta):
        dx_p = Percentage(1.25 / 1.5)
        dy_p = self._settings.get_shoulder_length()
        base_width = dx_p.apply(self._settings.get_width())
        shoulder_length = dy_p.apply(self._settings.get_length())
        base_length = self._settings.get_length()

        x = (self._settings.get_width() - base_width) / 2
        y = (base_length - shoulder_length) / 2
        return (cq.Sketch()
                .rect(base_width + delta, self._settings.get_length() + delta)
                .push([(-x, y)])
                .rect(self._settings.get_width() + delta, shoulder_length + delta)
                .reset()
                .clean()
                )

    def _stepped_iso(self):
        step_height = self._settings.get_step_settings().apply_step_height(self._settings.get_height())
        base_width = Percentage(1.25 / 1.5).apply(self._settings.get_width())
        a = self._iso_form(0)
        if self._settings.get_bottom_rounding_type() == RoundingType.FILLET:
            a = a.vertices().fillet(self._settings.get_bottom_rounding())
        elif self._settings.get_bottom_rounding_type() == RoundingType.CHAMFER:
            a = a.vertices().chamfer(self._settings.get_bottom_rounding())

        p = Percentage(step_height / self._settings.get_height())
        d = p.apply(self._settings.get_diff())

        b = self._iso_form(d)
        if self._settings.get_top_rounding_type() == RoundingType.FILLET:
            b = b.vertices().fillet(self._settings.get_top_rounding())
        elif self._settings.get_top_rounding_type() == RoundingType.CHAMFER:
            b = b.vertices().chamfer(self._settings.get_top_rounding())

        raised = self._box(
            base_width,
            self._settings.get_length(),
            self._settings.get_height(),
            self._settings.get_diff(),
            self._settings.get_bottom_rounding(),
            self._settings.get_bottom_rounding_type(),
            self._settings.get_top_rounding(),
            self._settings.get_top_rounding_type(),
        )

        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0, 0, step_height))))
                .loft()
                .union(raised)
                )

    def _iso_enter(self):
        a = self._iso_form(0)
        if self._settings.get_bottom_rounding_type() == RoundingType.FILLET:
            a = a.vertices().fillet(self._settings.get_bottom_rounding())
        elif self._settings.get_bottom_rounding_type() == RoundingType.CHAMFER:
            a = a.vertices().chamfer(self._settings.get_bottom_rounding())

        b = self._iso_form(self._settings.get_diff())
        if self._settings.get_top_rounding_type() == RoundingType.FILLET:
            b = b.vertices().fillet(self._settings.get_top_rounding())
        elif self._settings.get_top_rounding_type() == RoundingType.CHAMFER:
            b = b.vertices().chamfer(self._settings.get_top_rounding())

        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0, 0, self._settings.get_height()))))
                .loft()
                )

    def _stepped(self):
        step_settings = self._settings.get_step_settings()
        l = self._settings.get_length()
        w = self._settings.get_width()
        h = self._settings.get_height()
        step_height = step_settings.apply_step_height(h)
        step_width = w - step_settings.get_raised_width()
        raised = self._box(
            step_settings.get_raised_width(),
            l,
            h,
            self._settings.get_diff(),
            self._settings.get_bottom_rounding(),
            self._settings.get_bottom_rounding_type(),
            self._settings.get_top_rounding(),
            self._settings.get_top_rounding_type(),
        )
        step = self._box(
            w,
            l,
            h,
            self._settings.get_diff(),
            self._settings.get_bottom_rounding(),
            self._settings.get_bottom_rounding_type(),
            self._settings.get_top_rounding(),
            self._settings.get_top_rounding_type(),
        )
        step = (step.faces(">Z")
                .sketch()
                .rect(w, l)
                .finalize()
                .extrude(-(h - step_height), combine="cut")
                )
        if step_settings.get_type() == StepType.LEFT:
            return (raised.translate((-step_width / 2, 0, 0))
                    .add(step)
                    .combine()
                    )
        elif step_settings.get_type() == StepType.RIGHT:
            return (raised.translate((step_width / 2, 0, 0))
                    .add(step)
                    .combine()
                    )
        else:  # self._stepType == StepType.CENTER:
            return step.add(raised).combine()

    def _basic(self):
        return self._box(
            self._settings.get_width(),
            self._settings.get_length(),
            self._settings.get_height(),
            self._settings.get_diff(),
            self._settings.get_bottom_rounding(),
            self._settings.get_bottom_rounding_type(),
            self._settings.get_top_rounding(),
            self._settings.get_top_rounding_type(),
        )
