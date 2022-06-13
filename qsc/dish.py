import cadquery as cq
from typing import TypeVar
from qsc.types import Real
from qsc.u import U
from qsc.step_settings import StepSettings
from qsc.step_type import StepType

T = TypeVar("T", bound="Dish")


class Dish(object):
    _dishThickness = 1.8
    _extraThick = False
    _height = 8
    _inverted = False
    _row = 3
    _rowAngle = {
        1: 15,
        2: 5,
        3: 0,
        4: -10
    }
    _topDiff = -7
    _stepSettings = None

    def __init__(self):
        pass

    def dish_thickness(self, thickness: Real) -> T:
        self._dishThickness = thickness
        return self

    def extra_thick(self, extra_thick: bool) -> T:
        self._extraThick = extra_thick
        return self

    def cap_height(self, height: Real) -> T:
        self._height = height
        return self

    def inverted(self, inverted: bool) -> T:
        self._inverted = inverted
        return self

    def row(self, row: int) -> T:
        self._row = row
        return self

    def row_angle(self, row_angle: Real) -> T:
        self._rowAngle = row_angle
        return self

    def top_diff(self, top_diff: Real) -> T:
        self._topDiff = top_diff
        return self

    def step_settings(self, step_settings: StepSettings) -> T:
        self._stepSettings = step_settings
        return self

    def dish(self, cap: cq.Workplane) -> cq.Workplane:
        dish = None
        ctbb = cap.faces("<Z").findSolid().BoundingBox()
        x = ctbb.xlen
        y = ctbb.ylen
        location = cap.faces(">Z").findFace().Center()
        if self._stepSettings.get_raised_position() is None:
            dish = self._create_dish(x, y, self._inverted)
        else:
            x = self._stepSettings.get_raised_width()
            y = self._stepSettings.get_raised_length()
            dish = self._create_dish(x, y, self._inverted)
        if self._inverted:
            loc = location.toTuple()
            place_dish = self._dish_height(self._row, loc[2])
            dish = dish.translate((loc[0], loc[1], place_dish))
            intersection = cap.intersect(dish)
            bottom = cq.Workplane()
            if self._stepSettings.get_raised_position() is None:
                bottom = cap.split(keepBottom=True)
            else:
                step_height = self._stepSettings.apply_step_height(self._height)
                bottom = (cap.faces("<Z")
                          .workplane(offset=-step_height)
                          .rect(ctbb.xlen, ctbb.ylen)
                          .extrude(-ctbb.zlen, combine="cut")
                          )
            return intersection.union(bottom)  # , dish, intersection, bottom
        else:
            return cap.cut(dish.translate(location))

    def _dish_height(self, row: int, cap_height: Real) -> Real:
        match row:
            case 1:
                return cap_height + cap_height / 50
            case 2:
                return cap_height - cap_height / 16
            case 3:
                return cap_height - cap_height / 5
            case 4:
                return cap_height - cap_height / 16
        return cap_height

    def _create_dish(self, x: Real, y: Real, inverted: bool) -> cq.Workplane:
        dd_orig = pow((pow(x, 2) + pow(y, 2)), 0.5) - 1

        row_adjustments = {
            # (extra DD, extraDDinverted, translateY, translateZInverted, rotation)
            1: (2.0, 2.0, -1.0, -4.1, self._rowAngle.get(1)),
            2: (2.0, 2.0, -1.2, -3.1, self._rowAngle.get(2)),
            3: (0.0, 0.0, 0.0, -1.8, self._rowAngle.get(3)),
            4: (0.4, 1.55, 1.2, -3.1, self._rowAngle.get(4)),
        }.get(self._row)
        dd = dd_orig + row_adjustments[0]
        dd = dd + row_adjustments[1] if inverted else dd
        s_x, s_y = dd / 2 / self._dishThickness, dd / 2 / self._dishThickness
        s_z = 1.5 if self._extraThick else 1.0
        scale_matrix = cq.Matrix(
            [
                [s_x, 0.0, 0.0, 0.0],
                [0.0, s_y, 0.0, 0.0],
                [0.0, 0.0, s_z, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        scaled_sphere = (cq.Solid
                         .makeSphere(self._dishThickness, angleDegrees1=-90)
                         .transformGeometry(scale_matrix)
                         )

        if inverted:
            top = (cq.Workplane().add(scaled_sphere).split(keepTop=True))
            ylen = top.findSolid().BoundingBox().ylen
            bh = self._height - top.findSolid().BoundingBox().zlen + 0.1
            b = (cq.Solid.makeCone(dd_orig / 2 + abs(self._topDiff) / 2 + 1, ylen / 2, bh)
                 .moved(cq.Location((cq.Vector(0, 0, -bh + 0.1))))
                 )
            return (cq.Workplane("XY")
                    .add(top)
                    .union(b)
                    .translate((0, row_adjustments[2], row_adjustments[3]))
                    .rotate((0, 0, 0), (1, 0, 0), row_adjustments[4])
                    )
        else:
            bottom = (cq.Workplane().add(scaled_sphere).split(keepBottom=True))
            p = (cq.Solid.extrudeLinear(bottom.faces(">Z").val(), cq.Vector(0, 0, dd)))
            return (cq.Workplane("XY")
                    .add(bottom)
                    .union(p)
                    .translate((0, row_adjustments[2], -1))
                    .rotate((0, 0, 0), (1, 0, 0), row_adjustments[4])
                    )
