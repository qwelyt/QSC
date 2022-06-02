from __future__ import annotations

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
    _debug = False
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
    _specialStabPlacement = None
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

    def _srect(self, width: Real, depth: Real, delta: Real = 9.0, op: str = "chamfer"):
        rect = (cq.Sketch().rect(width, depth))

        if delta == 0:
            return rect
        elif op == "chamfer":
            return rect.vertices().chamfer(delta)
        elif op == "fillet":
            return rect.vertices().fillet(delta)
        else:
            return rect

    def _stem(self):
        stemHeight = self._height - self._topThickness

        stem = Stem(self._stemSettings).build()
        return (cq.Workplane("XY")
                .placeSketch(stem)
                .extrude(stemHeight)
                .faces("<Z")
                .chamfer(0.24)
                )

        # if self._stemType == StemType.CHERRY:
        #     cherryCross = (1.5 + self._stemHSlop, 4.2 + self._stemVSlop)
        #     return (cq.Workplane("XY")
        #             .sketch()
        #             .circle(self._stemCherryDiameter / 2)
        #             .rect(cherryCross[0], cherryCross[1], mode="s")
        #             .rect(cherryCross[1], cherryCross[0], mode="s")
        #             .finalize()
        #             .extrude(stemHeight)
        #             .faces("<Z")
        #             .chamfer(0.24)
        #             )
        # else:
        #     return cq.Workplane().box(2, 2, stemHeight)

    def _build_wedge(self, cap, extra):
        def _worl(bb, rotation, extra):
            l = bb.ylen if rotation == 0 or rotation == 180 else bb.xlen
            l = l + extra
            l = l - U(0.25).mm().get() if self._isoEnter else l
            return l

        def _len(bb, rotation, extra1, extra2):
            l = _worl(bb, rotation, extra1)
            l = (l - self._wallThickness) / 2 + extra2
            return l

        capBB = cap.findSolid().BoundingBox()
        h = self._height - self._topThickness - 0.3
        bottomBB = cap.faces("<Z").findSolid().BoundingBox()
        topBB = cap.faces("<Z").section(h).findSolid().BoundingBox()
        rotation = self._stemSettings.get_rotation()
        bottom_fillet = -(self._bottomFillet * 2)
        bottom = _len(bottomBB, rotation, bottom_fillet, extra)
        top = _len(topBB, rotation, 0, extra)

        diff = bottom - top
        closing = 0.5

        a = self._srect(0.5, bottom + closing, op="none")
        b = self._srect(0.5, top + closing, op="none")
        offset = (_worl(bottomBB, rotation, bottom_fillet) - self._wallThickness) / 4 - extra - 1
        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0, diff / 2, h))))
                .loft()
                .translate((0, -offset, 0))
                )

    def _buildStemSupport(self, cap):
        if self._stemSettings.get_type() == StemType.CHERRY:
            return self._build_wedge(cap, -self._stemSettings.get_radius())
        else:
            return cq.Workplane("XY").box(2, 2, 2)

    def _stemAndSupport(self, cap):
        rotation = self._stemSettings.get_rotation()
        offset = self._stemSettings.get_offset()
        support = self._stemSettings.get_support()
        wORl = self._width if rotation == 0 or rotation == 180 else self._length
        wORl = wORl.u().get()
        w = cq.Workplane("XY")
        s = self._stem().union(self._buildStemSupport(cap)) if support else self._stem()
        w.add(s.translate(offset))
        if self._stabs:
            ##old_edges = cap.edges().objects
            # added = (cap.faces("<Z")
            #         .sketch()
            #         #.push([(12,0)])
            #         .circle(self._stemCherryDiameter/2)
            #         .rect(1.5, 4.2, mode="s")
            #         .rect(4.2,1.5,  mode="s")
            #         .finalize()
            #         .extrude(until="next")
            #         )
            # p = (cq.Workplane()
            #     .box(20, 20, 20)
            #     .faces(">Z")
            #     .shell(2)
            #     .faces(">Z")
            #     .sketch()
            #     .circle(5)
            #     .rect(5,3, mode="s")
            #     .finalize()
            #     .extrude(until="next")
            #     )
            ##show_object(added.edges(cq.selectors.BoxSelector((-self._stemCherryDiameter,-self._stemCherryDiameter,-1),(self._stemCherryDiameter,self._stemCherryDiameter,1))))
            # added = (added.edges(cq.selectors.BoxSelector((-self._stemCherryDiameter,-self._stemCherryDiameter,-1),(self._stemCherryDiameter,self._stemCherryDiameter,1)))
            #         .chamfer(0.24)
            #         )
            # show_object(added)
            # show_object(p.faces("<Z").workplane().faces(cq.selectors.RadiusNthSelector(1)))
            # new_edges = added.edges().objects
            # added = added.newObject(list(set(new_edges)-set(old_edges)))
            # show_object(added.edges("<Z").chamfer(0.24))
            # show_object(cap.faces("<Z").sketch().push([(12,0)]).circle(self._stemCherryDiameter/2).finalize().extrude(until="next").last().faces("<Z"))
            # show_object(w)

            if self._specialStabPlacement is not None:
                m = s.translate(self._specialStabPlacement[0])
                n = s.translate(self._specialStabPlacement[1])
                mn = m.union(n)
                w.add(mn)
            elif wORl >= 6:
                w.add(s.translate((-50, 0, 0)))
                w.add(s.translate((50, 0, 0)))
            elif wORl >= 2:
                w.add(s.translate((-12, 0, 0)))
                w.add(s.translate((12, 0, 0)))

        return cap.union(w.combine().rotate((0, 0, 0), (0, 0, 1), rotation))

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
        return Base((BaseSettings()
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
                    ).build()

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

    def _homing(self, cap):
        return Homing(self._homingType).add(cap)

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

    def special_stab_placement(self, placement: Tuple[Tuple[Real, Real, Real], Tuple[Real, Real, Real]]) -> T:
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
        return self.stem_settings(self._stemSettings.rotation(90).offset((0, 0, 0)))

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
        return (QSC()
                .bottom_fillet(self._bottomFillet)
                .bottom_rect_fillet(self._bottomRectFillet)
                .disable_stabs(not self._stabs)
                .dish_thickness(self._dishThickness)
                .height(self._height)
                .homing(self._homingType, False)
                .inverted(self._inverted)
                .iso_enter(self._isoEnter)
                .legend(self._legend, self._fontSize, self._firstLayerHeight, self._font)
                .length(self._length)
                .row(self._row, False)
                .stem_settings(self._stemSettings)
                .step(self._step)
                .stepped(self._stepType, self._raisedWidth, self._stepHeight)
                .top_diff(self._topDiff)
                .top_fillet(self._topFillet)
                .top_rect_fillet(self._topRectFillet)
                .top_thickness(self._topThickness)
                .wall_thickness(self._wallThickness)
                .width(self._width)
                )

    def _edges(self, e):
        es = []
        for edge in e:
            es.append((edge.Length(), edge))
        es.sort(key=lambda tup: tup[0])
        return es

    def _debug_edges(self, shape):
        edges = self._edges(shape.edges().vals())
        print(edges[0])
        if self._show_object_exists():
            show_object(edges[0][1], options={"color": (255, 0, 250)})
        return edges

    def debug(self):
        self._debug = True
        return self.build()

    def isValid(self):
        self._pre_checks()
        base = self._base().tag("base")
        cap = self._dish(base)
        plane_faces = cap.faces("%Plane")
        non_plane_faces = cap.faces("not %Plane")
        if self._show_object_exists():
            show_object(plane_faces, options={"color": (255, 0, 0)})
            # show_object(non_plane_faces, options={"color":(0,0,255), "alpha":0.99})
            # show_object(cap.plane_faces("not %Plane"), options={"alpha":0.99, "color":(0,0,255)})
        plane_face_count = len(plane_faces.edges().vals())
        non_plane_face_count = len(non_plane_faces.edges().vals())
        valid = plane_face_count == 4 and non_plane_face_count == 14
        if not valid:
            self._printSettings()
            print(plane_face_count, non_plane_face_count)
        return (valid, cap)

    def maxPossibleFillet(self):
        self._pre_checks()
        base = self._base()
        cap = self._dish(base)
        shape = cap.findSolid()

        iterfillet = shape.maxFillet(shape.Edges(), 0.001, 1000)
        return iterfillet

    def _apply_fillet(self, cap, fillet: Real, var: str):
        try:
            cap = cap.faces(">Z").fillet(fillet)
        except StdFail_NotDone:
            self._printSettings()
            raise ValueError(var + " too big",
                             "Your " + var + "+setting [" + str(fillet) + "] is too big for the current shape (r" + str(self._row)
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
        if self._stepType:
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

        if self._topFillet < 0:
            self._find_max_fillet(cap, ">Z", "top")
        if self._topFillet > 0:
            # print("Top:",maxTop, "Step:",maxStep)
            cap = self._apply_fillet(cap.faces(">Z"), self._topFillet, "Top fillet")

        if self._bottomFillet < 0:
            self._find_max_fillet(cap, "<Z", "bottom")
        if self._bottomFillet > 0:
            cap = self._apply_fillet(cap.faces("<Z"), self._bottomFillet, "Bottom fillet")

        return cap

    def _pre_checks(self):
        if self._homingType == HomingType.SCOOPED:
            self._topThickness += 1

    def build(self):
        self._pre_checks()
        base = self._base().tag("base")
        dished = self._dish(base) if self._step > 1 else base
        cap = self._fillet(dished) if self._step > 2 else dished
        cap = self._homing(cap) if self._step > 3 else cap
        cap = cap.cut(self._hollow()) if self._step > 4 else cap
        cap = self._stemAndSupport(cap) if self._step > 5 else cap
        cap, legend = self._add_legend(cap, dished) if self._step > 6 else (cap, None)

        if legend is not None:
            return (
                cap.translate((0, 0, -self._height / 2)),
                legend.translate((0, 0, -self._height / 2)) if legend is not None else None
            )
        return (
            cap,  # .translate((0, 0, -self._height / 2)),
            None
        )

    def name(self):
        name = "qsc_row" + str(self._row)
        name = name + "_isoEnter" if self._isoEnter else name + "_" + str(self._width.u().get()) + "x" + str(self._length.u().get())
        name = name + "_i" if self._inverted else name
        name = name + "_stepped" if self._stepType else name
        name = name + "_" + self._legend if self._legend is not None else name
        return name

    def _show_object_exists(self):
        try:
            show_object(cq.Workplane())
            return True
        except:
            return False

    def show(self, rotate=False):
        if self._show_object_exists():
            c = self.build()
            if rotate:
                show_object(self._rotate(c[0]), options={"color": (200, 20, 100)})
                if self._legend is not None:
                    show_object(self._rotate(c[1]), options={"color": (90, 200, 40)})
            else:
                show_object(c[0], options={"color": (200, 20, 100)})
                if self._legend is not None:
                    show_object(c[1], options={"color": (90, 200, 40)})
        return self

    def exportSTL(self, tolerance=0.05, angularTolerance=0.05):
        c = self.build()
        cq.exporters.export(self._rotate(c[0]), self.name() + ".stl", tolerance=tolerance, angularTolerance=angularTolerance)
        print("Cap exported")
        if self._legend is not None:
            cq.exporters.export(self._rotate(c[1]), self.name() + "_LEGEND" + ".stl", tolerance=tolerance, angularTolerance=angularTolerance)
            print("Legend exported")
        return self

    def _rotate(self, w):
        return (w.rotate((0, 0, 0), (0, 0, 1), -self._stemSettings.get_rotation())
                .rotate((0, 0, 0), (1, 0, 0), 105)
                )

    def _printSettings(self):
        print(self.__dict__)
