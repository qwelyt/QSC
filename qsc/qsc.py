from __future__ import annotations

import copy
import math
from typing import Tuple, Iterable, TypeVar

import cadquery as cq
from OCP.StdFail import StdFail_NotDone

from qsc.types import Real
from qsc import (
    Percentage,
    Constants,
    MM,
    U,
    StemType,
    Homing,
    HomingType,
    RoundingType,
    StepType,
    StepSettings,
    CherrySettings,
    StemSettings,
    StemType,
    Stem,
    Legend,
    LegendSettings,
    Dish,
    Support,
)
from qsc.base import Base, BaseSettings

T = TypeVar("T", bound="QSC")


def _maxFillet(
        self: cq.Shape,
        edgeList: Iterable[cq.Edge],
        tolerance=0.1,
        maxIterations: int = 10,
) -> Real:
    if not self.isValid():
        raise ValueError("Invalid Shape")
    window_max = 2 * self.BoundingBox().DiagonalLength
    window_min = 0
    for i in range(maxIterations):
        window_mid = (window_min + window_max) / 2
        try:
            if not self.fillet(window_mid, edgeList).isValid():
                raise StdFail_NotDone
        except StdFail_NotDone:
            window_max = window_mid
            continue

        if window_mid - window_min <= tolerance:
            return window_mid
        else:
            window_min = window_mid

    raise RuntimeError(
        f"Failed to find the max value within {tolerance} in {maxIterations}, {window_mid}"
    )


cq.Shape.maxFillet = _maxFillet


class QSC(object):
    _bottomFillet = 0.5
    _bottomRectFillet = 1
    _dishThickness = MM(1.8).get()
    _firstLayerHeight = MM(1.2).get()
    _height = MM(8).get()
    _homingType = None  # None, Bar, Scooped, Dot
    _inverted = False
    _isoEnter = False
    _legend = None
    _legendFaceSelection = None
    _length = U(1)
    _row = 3
    _rowAngle = {
        1: 15,
        2: 5,
        3: 0,
        4: -10
    }
    _raisedWidth = 0
    _specialStabPlacement: Iterable[Tuple[Real, Real, Real]] = None
    _stabs = True
    _stemSettings = CherrySettings()
    _step = 10
    _stepFillet = 0.6
    _stepHeight = None
    _stepType = None
    _topDiff = MM(-7).get()
    _topFillet = 0.5
    _topRectFillet = 2
    _topThickness = MM(4).get()
    _wallThickness = MM(2).get()
    _width = U(1)

    _font = "Arial"
    _fontSize = _height

    def __init__(self):
        pass

    def _stem(self):
        stemHeight = self._height - self._topThickness

        stem = Stem(self._stemSettings).build()
        return (cq.Workplane("XY")
                .placeSketch(stem)
                .extrude(stemHeight)
                .faces("<Z")
                .chamfer(0.24)
                .rotate((0, 0, 0), (0, 0, 1), self._stemSettings.get_rotation())
                )

    def _stems(self, cap):
        stem = self._stem()
        positions = [self._stemSettings.get_offset()]

        if self._specialStabPlacement is not None:
            positions = [*positions, *self._specialStabPlacement]
        elif self._stabs:
            if self._width.u().get() >= 6:
                positions.append((-50, 0, 0))
                positions.append((50, 0, 0))
            elif self._width.u().get() >= 2:
                positions.append((-12, 0, 0))
                positions.append((12, 0, 0))

            if self._length.u().get() >= 6:
                positions.append((0, -50, 0))
                positions.append((0, 50, 0))
            elif self._length.u().get() >= 2:
                positions.append((0, -12, 0))
                positions.append((0, 12, 0))

        wp = cq.Workplane("XY")
        for pos in positions:
            wp.add(stem.translate(pos))

        cap = cap.union(wp.combine())
        cap = Support(self._stemSettings).positions(positions).build(cap)
        return cap

    def _add_legend(self, cap, dished):
        side = {
            0: "<Y",
            90: ">X",
            180: ">Y",
            270: "<X"
        }.get(self._stemSettings.get_rotation()) if self._legendFaceSelection is None else self._legendFaceSelection
        settings = (LegendSettings()
                    .distance(self._firstLayerHeight)
                    .font(self._font)
                    .font_size(self._fontSize)
                    .legend(self._legend)
                    .side(side)
                    .y_pos(self._bottomFillet)
                    )
        return Legend(settings).apply_legend(cap, dished)

    def _base(self):
        base_settings = (BaseSettings()
                         .width(self._width.mm().get())
                         .length(self._length.mm().get())
                         .height(MM(self._height).mm().get())
                         .diff(self._topDiff)
                         .top_rounding(self._topRectFillet, RoundingType.FILLET)
                         .bottom_rounding(self._bottomRectFillet, RoundingType.FILLET)
                         .iso_enter(self._isoEnter)
                         .step_settings((StepSettings()
                                         .step_type(self._stepType)
                                         .raised_width(self._raisedWidth)
                                         .step_height(self._stepHeight)
                                         )
                                        )
                         )
        return Base(base_settings).build()

    def _hollow(self):
        ih = (MM(self._height).mm().get() - self._topThickness)
        diff = Percentage(ih / self._height).apply(self._topDiff)
        step_height = self._stepHeight
        if type(step_height) == MM:
            step_height = MM(step_height.get() - self._topThickness)

        return Base((BaseSettings()
                     .width(self._width.mm().get() - self._wallThickness * 2)
                     .length(self._length.mm().get() - self._wallThickness * 2)
                     .height(ih)
                     .diff(diff)
                     .iso_enter(self._isoEnter, Percentage((U(1).mm().get() - self._wallThickness) / U(2).mm().get()))
                     .step_settings((StepSettings()
                                     .step_type(self._stepType)
                                     .raised_width(self._raisedWidth - self._wallThickness * 2)
                                     .step_height(step_height)
                                     )
                                    )
                     )
                    ).build()

    def _dish(self, cap):
        return (Dish()
                .dish_thickness(self._dishThickness)
                .extra_thick(self._homingType == HomingType.SCOOPED)
                .cap_height(self._height)
                .inverted(self._inverted)
                .row(self._row)
                .row_angle(self._rowAngle)
                ).dish(cap)

    def _apply_fillet(self, cap, fillet: Real, var: str):
        try:
            cap = cap.fillet(fillet)
        except StdFail_NotDone:
            self._printSettings()
            raise ValueError(var + " too big",
                             "Your " + var + " setting [" + str(fillet) + "] is too big for the current shape (r" + str(self._row)
                             + ", " + str(self._width.u().get()) + "x" + str(self._length.u().get())
                             + "). Try reducing it.")
        except Exception:
            self._printSettings()
            raise
        return cap

    def _find_max_fillet(self, cap, face, who):
        print("Max " + who + " fillet:", cap.findSolid().maxFillet(cap.faces(face).findFace().Edges(), 0.001, 100))

    def _fillet(self, cap):
        # maxTop = cap.findSolid().maxFillet(cap.faces(">Z").findFace().Edges(), 0.001, 100)
        # print("hoho", maxTop)
        # maxStep = 0
        # debug(cap.edges())

        if self._topFillet < 0:
            self._find_max_fillet(cap, ">Z", "top")
        if self._topFillet > 0:
            # print("Top:",maxTop, "Step:",maxStep)
            cap = self._apply_fillet(cap.faces(">Z"), self._topFillet, "Top fillet")

        if self._bottomFillet < 0:
            self._find_max_fillet(cap, "<Z", "bottom")
        if self._bottomFillet > 0:
            cap = self._apply_fillet(cap.faces("<Z"), self._bottomFillet, "Bottom fillet")

        if self._stepType is not None:
            selector = {
                1: ">Z[1]",
                2: ">Z[1]",
                3: ">Z[1]",
                4: ">Z[1]",
            }.get(self._row)
            if self._stepFillet < 0:
                self._find_max_fillet(cap, selector, "step")
            if self._stepFillet > 0:
                # maxStep = cap.findSolid().maxFillet(cap.faces(">Z[1]").findFace().Edges(), 0.01, 100)
                cap = self._apply_fillet(cap.faces(selector), self._stepFillet, "Step fillet")
        return cap

    def wall_thickness(self, thickness: Real) -> T:
        self._wallThickness = thickness
        return self

    def top_thickness(self, thickness: Real) -> T:
        self._topThickness = thickness
        return self

    def width(self, width: U | MM) -> T:
        self._width = width
        return self

    def length(self, length: U | MM) -> T:
        self._length = length
        return self

    def height(self, height: Real) -> T:
        self._height = height
        return self

    def legend(self, legend: str, font_size: Real = -1, first_layer_height: Real = 1.2, font: str = "Arial", face_selection: str = None) -> T:
        self._legend = legend
        self._fontSize = self._height if font_size == -1 else font_size
        self._firstLayerHeight = first_layer_height
        self._font = font
        self._legendFaceSelection = face_selection
        return self

    def top_diff(self, diff: Real) -> T:
        self._topDiff = diff
        return self

    def dish_thickness(self, thickness: Real) -> T:
        self._dishThickness = thickness
        return self

    def stem_settings(self, stem_settings: StemSettings) -> T:
        self._stemSettings = stem_settings
        return self

    def disable_stabs(self, disable: bool = True) -> T:
        self._stabs = not disable
        return self

    def special_stab_placement(self, placement: Iterable[Tuple[Real, Real, Real]]) -> T:
        self._specialStabPlacement = placement
        return self

    def homing(self, type: HomingType = HomingType.SCOOPED, adjustHeight=True):
        self._homingType = type
        if type == HomingType.SCOOPED:
            height_adjustment = {
                1: 0.6035380213915218,
                2: 0.3804040372053077,
                3: 0.2755496042382024,
                4: 0.0490026944352374
            }.get(self._row)
            if adjustHeight:
                self._height += height_adjustment
        return self

    def inverted(self, inverted: bool = True) -> T:
        self._inverted = inverted
        return self

    def stepped(self, step_type: StepType = StepType.LEFT, raised_width: Percentage | U | MM = None, step_height: MM | Percentage = None) -> T:
        self._stepType = step_type
        self._stepHeight = step_height
        if self._isoEnter:
            return self
        else:
            if raised_width is None:
                raised_width = {
                    StepType.LEFT: Constants.RAISED_PERCENTAGE,
                    StepType.CENTER: U(1),
                    StepType.RIGHT: Constants.RAISED_PERCENTAGE,
                }.get(step_type)

            raised = 0
            if type(raised_width) is Percentage:
                raised = raised_width.apply(self._width.mm().get())
            elif type(raised_width) is U or type(raised_width) is MM:
                raised = raised_width.mm().get()
            self._raisedWidth = raised
            if step_type == StepType.CENTER:
                return self
            offset = (self._width.mm().get() - raised) / 2.0
            offset = offset * -1 if step_type == StepType.LEFT else offset
            return self.stem_settings(self._stemSettings.offset((offset, 0.0, 0.0)))

    def iso_enter(self, iso: bool = True) -> T:
        self._isoEnter = iso
        self.width(U(1.5))
        self.length(U(2))
        self.step_fillet(0.221)
        return self

    def top_rect_fillet(self, value: Real) -> T:
        self._topRectFillet = value
        return self

    def bottom_rect_fillet(self, value: Real) -> T:
        self._bottomRectFillet = value
        return self

    def top_fillet(self, value: Real) -> T:
        self._topFillet = value
        return self

    def step_fillet(self, value: Real) -> T:
        self._stepFillet = value
        return self

    def bottom_fillet(self, value: Real) -> T:
        self._bottomFillet = value
        return self

    def row(self, row: int, adjust_row=True) -> T:
        self._row = row
        if adjust_row:
            row_adjustments = {
                1: (5, 3),
                2: (1.5, 0.5),
                3: (0, 0),
                4: (2, 1),
            }.get(self._row)
            self.height(self._height + row_adjustments[0])
            self.top_thickness(self._topThickness + row_adjustments[1])
        return self

    def step(self, steps) -> T:
        self._step = steps
        return self

    def clone(self) -> QSC:
        return copy.deepcopy(self)

    def _edges(self, e):
        es = []
        for edge in e:
            es.append((edge.Length(), edge))
        es.sort(key=lambda tup: tup[0])
        return es

    def _debug_edges(self, shape):
        edges = self._edges(shape.edges().vals())
        print(edges[0])
        return edges

    def isValid(self):
        self._step = 2
        cap, _ = self.build()
        plane_faces = cap.faces("%Plane")
        non_plane_faces = cap.faces("not %Plane")
        plane_face_count = len(plane_faces.edges().vals())
        non_plane_face_count = len(non_plane_faces.edges().vals())
        valid = plane_face_count == 4 and non_plane_face_count == 14
        if not valid:
            self._printSettings()
            print(plane_face_count, non_plane_face_count)
        return valid, cap

    def build(self, center=True):
        base = self._base().tag("base")
        dished = self._dish(base) if self._step > 1 else base
        cap = self._fillet(dished) if self._step > 2 else dished
        cap = Homing(self._homingType).add(cap) if self._step > 3 else cap
        cap = cap.cut(self._hollow()) if self._step > 4 else cap
        cap = self._stems(cap) if self._step > 5 else cap
        cap, legend = self._add_legend(cap, dished) if self._step > 6 else (cap, None)

        if center:
            if legend is not None:
                return (
                    cap.translate((0, 0, -self._height / 2)),
                    legend.translate((0, 0, -self._height / 2)),
                )
            return (
                cap.translate((0, 0, -self._height / 2)),
                None
            )
        else:
            if legend is not None:
                return (
                    cap,
                    legend if legend is not None else None
                )
            return (
                cap,
                None
            )

    def rotated(self):
        c = self.build(False)
        b = self._base()
        if c[1] is not None:
            return (
                self._rotate(c[0], b, self._stemSettings.get_rotation()),
                self._rotate(c[1], b, self._stemSettings.get_rotation()),
            )
        return (
            self._rotate(c[0], b, self._stemSettings.get_rotation()),
            None
        )

    def name(self):
        name = "qsc_row" + str(self._row)
        name = name + "_isoEnter" if self._isoEnter else name + "_" + str(self._width.u().get()) + "x" + str(self._length.u().get())
        name = name + "_i" if self._inverted else name
        name = name + "_stepped" if self._stepType else name
        name = name + "_" + self._legend if self._legend is not None else name
        return name

    def exportSTL(self, tolerance=0.02, angularTolerance=0.02):
        base = self._base()
        c = self.build()
        cq.exporters.export(self._rotate(c[0], base, self._stemSettings.get_rotation()), self.name() + ".stl", tolerance=tolerance, angularTolerance=angularTolerance)
        print("Cap exported")
        if self._legend is not None:
            cq.exporters.export(self._rotate(c[1], base, self._stemSettings.get_rotation()), self.name() + "_LEGEND" + ".stl", tolerance=tolerance,
                                angularTolerance=angularTolerance)
            print("Legend exported")
        return self

    def _rotate(self, cap: cq.Workplane, base: cq.Workplane, stem_rotation: int):
        face = {
            0: ("<Y", (1, 0, 0)),
            90: (">X", (0, 1, 0)),
            180: (">Y", (1, 0, 0)),
            270: ("<X", (0, 1, 0)),
        }.get(stem_rotation)

        angle = (base.faces(face[0])
                 .workplane()
                 .plane
                 .zDir
                 .getSignedAngle(cq.Vector(0, 0, 1, ))
                 )

        rotation = 180 - math.degrees(angle)

        return cap.rotate((0, 0, 0), face[1], rotation)

    def _printSettings(self):
        print(self.__dict__)
