from __future__ import annotations

from enum import Enum, auto
from typing import Tuple, Iterable

import cadquery as cq
from OCP.StdFail import StdFail_NotDone


def _maxFillet(
        self: cq.Shape,
        edgeList: Iterable[cq.Edge],
        tolerance=0.1,
        maxIterations: int = 10,
) -> float:
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


# TODO
# * Alps?

class HomingType(Enum):
    BAR = 1
    SCOOPED = 2
    DOT = 3


class StemType(Enum):
    CHERRY = auto()


class StepType(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


class Percentage(object):
    _percentage = 0

    def __init__(self, percentage):
        self._percentage = percentage

    def __str__(self):
        return str(self._percentage)

    def apply(self, mm):
        return mm * self._percentage


class Constants:
    STEP_PERCENTAGE = Percentage(0.7142857142857143)  # 1.25/1.75
    STEP_PERCENTAGE_OF_TOTAL = Percentage(28.57142857142857)  # 0.5/1.75
    U_IN_MM = 19.05


class U(object):
    _u = 0

    def __init__(self, u):
        self._u = u
        
    def __str__(self):
        return str(self._u+"u")

    def u(self) -> U:
        return self

    def mm(self) -> MM:
        return MM(self._u * Constants.U_IN_MM)

    def get(self) -> float:
        return self._u


class MM(object):
    _mm = 0

    def __init__(self, mm):
        self._mm = mm

    def __str__(self):
        return str(self._mm + "mm")

    def u(self) -> U:
        return U(self._mm / Constants.U_IN_MM)

    def mm(self) -> MM:
        return self

    def get(self) -> float:
        return self._mm


class QSC:
    _bottomFillet = 0.6
    _bottomRectFillet = 1
    _debug = False
    _dishThickness = MM(1.8).get()
    _firstLayerHeight = MM(1.2).get()
    _height = MM(8).get()
    _homingType = None  # None, Bar, Scooped, Dot
    _inverted = False
    _isoEnter = False
    _legend = None
    _length = U(1)
    _row = 3
    _rowAngle = {
        1: 15,
        2: 5,
        3: 0,
        4: -10
    }
    _specialStabPlacement = None
    _stemCherryDiameter = MM(5.6).get()  # mm
    _stemHSlop = MM(0.0).get()  # mm
    _stemOffset = (0, 0, 0)
    _stemRotation = 0
    _stemSupport = True
    _stemType = StemType.CHERRY
    _stemVSlop = MM(0.0).get()  # mm
    _step = 10
    _stepped = False
    _topDiff = MM(-7).get()  # mm
    _topFillet = 0.6
    _topRectFillet = 2
    _topThickness = MM(3).get()  # mm
    _wallThickness = MM(1.5).get()  # mm
    _width = U(1)  #

    _font = "Arial"
    _fontSize = _height

    def __init__(self):
        pass

    def _srect(self, width, depth, delta=9, op="chamfer"):
        rect = (cq.Sketch().rect(width, depth))

        if delta == 0:
            return rect
        elif op == "chamfer":
            return (rect.vertices().chamfer(delta))
        elif op == "fillet":
            return (rect.vertices().fillet(delta))
        else:
            return rect

    def _box(self, width, depth, height, diff=0, deltaA=9, deltaB=4, op="chamfer"):
        a = self._srect(width, depth, deltaA, op)
        b = self._srect(width + diff, depth + diff, deltaB, op)
        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0, 0, height))))
                .loft()
                )

    def _stem(self):
        stemHeight = self._height - self._topThickness
        if self._stemType == StemType.CHERRY:
            cherryCross = (1.5 + self._stemHSlop, 4.2 + self._stemVSlop)
            return (cq.Workplane("XY")
                    .sketch()
                    .circle(self._stemCherryDiameter / 2)
                    .rect(cherryCross[0], cherryCross[1], mode="s")
                    .rect(cherryCross[1], cherryCross[0], mode="s")
                    .finalize()
                    .extrude(stemHeight)
                    .faces("<Z")
                    .chamfer(0.24)
                    )
        else:
            return cq.Workplane().box(2, 2, stemHeight)

    def _buildStemSupport(self, cap):
        if self._stemType == StemType.CHERRY:
            bottomBB = cap.faces("<Z").findSolid().BoundingBox()
            wORl = bottomBB.ylen if self._stemRotation == 0 or self._stemRotation == 180 else bottomBB.xlen
            wORl = wORl - self._bottomFillet * 2
            wORl = wORl - U(0.25).mm().get() if self._isoEnter else wORl
            w = (wORl - self._wallThickness) / 2 - self._stemCherryDiameter / 2
            h = self._height - self._topThickness - 0.3

            topBB = cap.faces("<Z").section(h).findSolid().BoundingBox()
            topLen = topBB.ylen if self._stemRotation == 0 or self._stemRotation == 180 else topBB.xlen
            topLen = topLen - U(0.25).mm().get() if self._isoEnter else topLen
            w2 = (topLen - self._wallThickness) / 2 - self._stemCherryDiameter / 2
            diff = w - w2

            closing = 0.5
            a = self._srect(0.5, w + closing, op="none")
            b = self._srect(0.5, w2 + closing, op="none")

            supportOffset = (wORl - self._wallThickness) / 4 + self._stemCherryDiameter / 2 - 1
            return (cq.Workplane("XY")
                    .placeSketch(a, b.moved(cq.Location(cq.Vector(0, diff / 2, h))))
                    .loft()
                    .translate((0, -supportOffset, 0))
                    )
        else:
            return (cq.Workplane("XY").box(2, 2, 2))

    def _stemAndSupport(self, cap):
        wORl = self._width if self._stemRotation == 0 or self._stemRotation == 180 else self._length
        wORl = wORl.u().get()
        w = cq.Workplane("XY")
        s = self._stem().union(self._buildStemSupport(cap)) if self._stemSupport else self._stem()
        w.add(s.translate(self._stemOffset))
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

        return cap.union(w.combine().rotate((0, 0, 0), (0, 0, 1), self._stemRotation))

    def _addLegend(self, cap):
        if self._legend is None:
            return cap, None
        sideSelector = {
            1: {
                0: ">>Y[3]",
                90: "<<X[2]",
                180: "<<Y[2]",
                270: ">>X[3]"
            },
            2: {
                0: ">>Y[3]",
                90: "<<X[2]",
                180: "<<Y[2]",
                270: ">>X[3]"
            },
            3: {
                0: ">>Y[3]",
                90: "<<X[2]",
                180: "<<Y[2]",
                270: ">>X[3]"
            },
            4: {
                0: ">>Y[3]",
                90: "<<X[2]",
                180: "<<Y[2]",
                270: ">>X[3]"
            }
        }.get(self._row).get(self._stemRotation)
        # show_object(cap.faces(sideSelector))
        nc = (cap.faces(sideSelector)
              .workplane(offset=-self._firstLayerHeight, centerOption="CenterOfMass")
              )
        nw = cq.Workplane().copyWorkplane(nc)
        c = nc.text(txt=self._legend, fontsize=self._fontSize, distance=self._firstLayerHeight, font=self._font)
        t = nw.text(txt=self._legend, fontsize=self._fontSize, distance=self._firstLayerHeight, font=self._font, combine='a', cut=False)
        return c, t

    def _base(self):
        l = self._length.mm().get()
        w = self._width.mm().get()
        if self._isoEnter and self._stepped:
            w6 = w / 6
            lower = self._box(w - w6, l, self._height, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            upper = self._box(w, l / 2, self._height / 2, self._topDiff / 2, self._bottomRectFillet, self._topRectFillet, "fillet")
            return lower.add(upper.translate((-w6 / 2, l / 4, 0))).combine()
        elif self._isoEnter:
            w6 = w / 6
            lower = self._box(w - w6, l, self._height, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            upper = self._box(w, l / 2, self._height, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            return lower.add(upper.translate((-w6 / 2, l / 4, 0))).combine()
        elif self._stepped:
            highWidth = Constants.STEP_PERCENTAGE.apply(w)
            stepWidth = w - highWidth
            heightDivider = 2 if not self._row == 1 else 2
            high = self._box(highWidth, l, self._height, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            step = self._box(w, l, self._height, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            step = (step.faces(">Z")
                    .sketch()
                    .rect(w, l)
                    .finalize()
                    .extrude(-self._height / heightDivider, "cut")
                    )
            return high.translate((-stepWidth / 2, 0, 0)).add(step).combine()
        else:
            return self._box(w, l, self._height, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")

    def _hollow(self):
        il = self._length.mm().get() - (self._wallThickness * 2)
        iw = self._width.mm().get() - (self._wallThickness * 2)
        if self._isoEnter and self._stepped:
            ih = self._height - self._topThickness
            il2 = U(1).mm().get() - (self._wallThickness * 2)
            w = self._width.mm().get()
            w6 = w / 6
            iw2 = iw - w6
            lower = self._box(iw2, il, ih, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            upper = self._box(iw, il2, ih / 2, self._topDiff / 2, self._bottomRectFillet, self._topRectFillet, "fillet")
            return lower.add(upper.translate((-w6 / 2, il2 / 1.65, 0))).combine()
        elif self._stepped:
            highWidth = Constants.STEP_PERCENTAGE.apply(iw)
            stepWidth = iw - highWidth
            heightDivider = 2 if not self._row == 1 else 3
            ihHigh = self._height - self._topThickness
            high = self._box(highWidth, il, ihHigh, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            step = self._box(iw, il, ihHigh, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            step = (step.faces(">Z")
                    .sketch()
                    .rect(iw, il)
                    .finalize()
                    .extrude(-self._height / heightDivider, "cut")
                    )
            return high.translate((-stepWidth / 2, 0, 0)).add(step).combine()
        elif self._isoEnter:
            ih = self._height - self._topThickness
            il2 = U(1).mm().get() - (self._wallThickness * 2)
            w = self._width.mm().get()
            w6 = w / 6
            iw2 = iw - w6
            lower = self._box(iw2, il, ih, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            upper = self._box(iw, il2, ih, self._topDiff, self._bottomRectFillet, self._topRectFillet, "fillet")
            return lower.add(upper.translate((-w6 / 2, il2 / 1.65, 0))).combine()
        else:
            ih = self._height - self._topThickness
            return self._box(iw, il, ih, self._topDiff, 0, 0, "none")

    def _createDish(self, inverted):
        isoOrNot = U(2).mm().get() if self._isoEnter else self._width.mm().get()
        w = isoOrNot - self._topDiff * -1 / 1.2
        l = self._length.mm().get() - self._topDiff * -1 / 1.2
        dd_orig = pow((pow(w, 2) + pow(l, 2)), 0.5) + 1
        row_adjustments = {
            # (extra DD, extraDDinverted, translateY, translateZ, rotation)
            1: (2.0, 2.0, 0.0, 0.0, self._rowAngle.get(1)),
            2: (2.0, 2.0, -1.2, 0.0, self._rowAngle.get(2)),
            3: (0.0, 0.0, 0.0, 0.0, self._rowAngle.get(3)),
            4: (0.4, 1.55, 1.2, 0.0, self._rowAngle.get(4)),
        }.get(self._row)
        dd = dd_orig + row_adjustments[0]
        dd = dd + row_adjustments[1] if inverted else dd
        s_x, s_y = dd / 2 / self._dishThickness, dd / 2 / self._dishThickness
        s_z = 1.5 if self._homingType == HomingType.SCOOPED else 1.0
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
        noCylinder = (cq.Workplane("XY").add(scaled_sphere)
                    .translate((0, row_adjustments[2], row_adjustments[3]))
                    .rotate((0, 0, 0), (1, 0, 0), row_adjustments[4])
                    )
        # show_object(scaled_sphere, options={"color":(255,0,0), "alpha":0.5})
        # show_object(scaled_sphere2, options={"color":(0,255,0), "alpha":0.5})

        upOrDown = -1 if inverted else 0

        b = (cq.Solid.makeCylinder(self._dishThickness, dd)
             .transformGeometry(scale_matrix)
             .translate((0,0,dd*upOrDown))
             )
        z = -1  # row_adjustments[3]
        return (
            (cq.Workplane()
                .add(scaled_sphere)
                .union(b)
                .translate((0, row_adjustments[2], z))
                .rotate((0, 0, 0), (1, 0, 0), row_adjustments[4])
                ),
            noCylinder
        )

    def _dish(self, cap):
        dish, just_dish = self._createDish(self._inverted)
        capBB = cap.findSolid().BoundingBox()
        h = capBB.zmax
        #debug(dish.translate((0,0,h)))
        print(self._inverted)
        if self._inverted:
            dishBB = just_dish.findSolid().BoundingBox()
            intersection = cap.intersect(dish.translate((0, 0, h - dishBB.zlen/2)))
            #debug(intersection)
            cutter = cq.Solid.extrudeLinear(intersection.faces(">Z").val(), cq.Vector(0, 0, dishBB.zlen))
            #debug(cutter)
            cap = cap.cut(cutter)
            #cap = cap.union(intersection)
        else:
            # debug(dish)
            cap = cap.cut(dish.translate((0, 0, h)))
            if self._debug:
                show_object(dish.translate((0, 0, h)), options={"color": (255, 255, 255), "alpha": 0.3})

        return cap

    def _homing(self, cap):
        if self._homingType is None or self._homingType is HomingType.SCOOPED:
            return cap
        capBB = cap.findSolid().BoundingBox()
        l = capBB.ylen / 2 if self._homingType == HomingType.BAR else 1
        placer = cq.Workplane().rect(0.1, l).extrude(capBB.zlen)
        intersection = cap.intersect(placer)
        iBB = intersection.faces("<Y").val().BoundingBox()

        if self._homingType == HomingType.BAR:
            barSize = 1
            bar = (cq.Workplane("XY")
                   .sketch()
                   .rect(capBB.xlen / 3, barSize)
                   .vertices()
                   .fillet(barSize / 2)
                   .finalize()
                   .extrude(1)
                   .faces(">Z")
                   .fillet(barSize / 2)
                   )
            b = bar.translate((0, iBB.ymin, iBB.zlen - barSize / 1.5))
            return cap.add(b)
        elif self._homingType == HomingType.DOT:
            dotSize = 1
            dot = (cq.Workplane()
                   .sphere(dotSize)
                   .translate((0, iBB.ymin, iBB.zlen - dotSize / 2))
                   )
            return cap.union(dot)
        else:
            return cap

    def wallThickness(self, thickness: float):
        self._wallThickness = thickness
        return self

    def topThickness(self, thickness: float):
        self._topThickness = thickness
        return self

    def width(self, width: U | MM):
        self._width = width
        return self

    def length(self, length: U | MM):
        self._length = length
        return self

    def height(self, height: float):
        self._height = height
        return self

    def legend(self, legend: str, fontSize: float = -1, firstLayerHeight: float = 1.2, font: str = "Arial"):
        self._legend = legend
        self._fontSize = self._height if fontSize == -1 else fontSize
        self._firstLayerHeight = firstLayerHeight
        self._font = font
        return self

    def topDiff(self, diff: float):
        self._topDiff = diff
        return self

    def dishThickness(self, thickness: float):
        self._dishThickness = thickness
        return self

    def stemType(self, stemtype: StemType):
        self._stemType = stemtype
        return self

    def stemOffset(self, offset: Tuple[float, float, float]):
        self._stemOffset = offset
        return self

    def stemRotation(self, rotation: int):
        self._stemRotation = rotation
        return self

    def stemCherryDiameter(self, d: float):
        self._stemCherryDiameter = d
        return self

    def stemVSlop(self, slop: float):
        self._stemVSlop = slop
        return self

    def stemHSlop(self, slop: float):
        self._stemHSlop = slop
        return self

    def disableStemSupport(self, disable: bool = True):
        self._stemSupport = not disable
        return self

    def specialStabPlacement(self, placement: Tuple[Tuple[float, float, float], Tuple[float, float, float]]):
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

    def inverted(self, inverted: bool = True):
        self._inverted = inverted
        return self

    # def stepped(self, stepType=StepType.LEFT: StepType, stepAmount=Constants.STEP_PERCENTAGE: float):
    # def stepped(self, stepType=StepType.LEFT: StepType, raisedAmount: Union[Percentage,U] = Contants.STEP_AMOUNT):
    def stepped(self, steppedKey: bool = True, offset: bool=True):
        self._stepped = steppedKey
        if self._isoEnter:
            return self
        else:
            lowerWidth = Constants.STEP_PERCENTAGE.apply(self._width.mm().get())
            offset = (self._width.mm().get() - lowerWidth) / 2.0
            return self.stemOffset((-offset, 0.0, 0.0))

    def isoEnter(self, iso: bool = True):
        self._isoEnter = iso
        self.width(U(1.5))
        self.length(U(2))
        self.stemRotation(90)
        return self.stemOffset((0, 0, 0))

    def topRectFillet(self, value: float):
        self._topRectFillet = value
        return self

    def bottomRectFillet(self, value: float):
        self._bottomRectFillet = value
        return self

    def topFillet(self, value: float):
        self._topFillet = value
        return self

    def bottomFillet(self, value: float):
        self._bottomFillet = value
        return self

    def row(self, row: int, adjustRow=True):
        self._row = row
        if adjustRow:
            row_adjustments = {
                1: (5, 3),
                2: (1.5, 0.5),
                3: (0, 0),
                4: (2, 1),
            }.get(self._row)
            self.height(self._height + row_adjustments[0])
            self.topThickness(self._topThickness + row_adjustments[1])
        return self

    def step(self, steps):
        self._step = steps
        return self

    def clone(self):
        return (QSC()
                .bottomFillet(self._bottomFillet)
                .bottomRectFillet(self._bottomRectFillet)
                .disableStemSupport(not self._stemSupport)
                .dishThickness(self._dishThickness)
                .height(self._height)
                .homing(self._homingType, False)
                .inverted(self._inverted)
                .isoEnter(self._isoEnter)
                .legend(self._legend, self._fontSize, self._firstLayerHeight, self._font)
                .length(self._length)
                .row(self._row, False)
                .stemCherryDiameter(self._stemCherryDiameter)
                .stemHSlop(self._stemHSlop)
                .stemType(self._stemType)
                .stemVSlop(self._stemVSlop)
                .stepped(self._stepped, False)
                .stemOffset(self._stemOffset)
                .stemRotation(self._stemRotation)
                .step(self._step)
                .topDiff(self._topDiff)
                .topFillet(self._topFillet)
                .topRectFillet(self._topRectFillet)
                .topThickness(self._topThickness)
                .wallThickness(self._wallThickness)
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
            show_object(edges[0][1], options={"color": {255, 0, 0}})
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

    def _fillet(self, cap):
        # maxTop = cap.findSolid().maxFillet(cap.faces(">Z").findFace().Edges(), 0.01, 100)
        # maxStep = 0
        if self._topFillet > 0:
            try:
                if self._stepped:
                    # maxStep = cap.findSolid().maxFillet(cap.faces(">Z[1]").findFace().Edges(), 0.01, 100)
                    selector = {
                        1: ">Z[1]",
                        2: ">Z[1]",
                        3: ">Z[1]",
                        4: ">Z[1]",
                    }.get(self._row)
                    cap = cap.faces(selector).fillet(self._topFillet)
                # print("Top:",maxTop, "Step:",maxStep)
                cap = cap.faces(">Z").fillet(self._topFillet)
            except StdFail_NotDone:
                self._printSettings()
                raise ValueError("Top fillet too big",
                                 "Your top fillet setting [" + str(self._topFillet) + "] is too big for the current shape (r" + str(self._row)
                                 + ", " + str(self._width.u().get()) + "x" + str(self._length.u().get())
                                 + "). Try reducing it.")
            except Exception:
                self._printSettings()
                raise

        if self._bottomFillet > 0:
            try:
                cap = cap.edges("<Z").fillet(self._bottomFillet)
            except StdFail_NotDone:
                self._printSettings()
                raise ValueError("Bottom fillet too big",
                                 "Your bottom fillet setting [" + str(self._bottomFillet) + "] is too big for the current shape (r" + str(self._row)
                                 + ", " + str(self._width.u().get()) + "x" + str(self._length)
                                 + "). Try reducing it.")
            except Exception:
                self._printSettings()
                raise

        return cap

    def _pre_checks(self):
        if self._homingType == HomingType.SCOOPED:
            self._topThickness += 1

    def build(self):
        self._pre_checks()
        cap = self._base().tag("base")
        cap = self._dish(cap) if self._step > 1 else cap
        cap = self._fillet(cap) if self._step > 2 else cap
        cap = self._homing(cap) if self._step > 3 else cap
        cap = cap.cut(self._hollow()) if self._step > 4 else cap
        cap = self._stemAndSupport(cap) if self._step > 5 else cap
        cap, legend = self._addLegend(cap) if self._step > 6 else (cap, None)

        if self._legend is not None:
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
        name = name + "_stepped" if self._stepped else name
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

    def exportSTL(self):
        c = self.build()
        cq.exporters.export(self._rotate(c[0]), self.name() + ".stl")
        if self._legend is not None:
            cq.exporters.export(self._rotate(c[1]), self.name() + "_LEGEND" + ".stl")
        return self

    def _rotate(self, w):
        return (w.rotate((0, 0, 0), (0, 0, 1), -self._stemRotation)
                .rotate((0, 0, 0), (1, 0, 0), 250)
                )

    def _printSettings(self):
        print(self.__dict__)


def showcase():
    print("=== Build showcase ==")
    c = QSC()
    showcase = (cq.Assembly(name="QSC_showcase"))
    for i in [(1, 4), (2, 1), (3, 0), (4, 1)]:
        showcase.add(c.clone().row(i[0]).legend(str(i[0]), fontSize=6).build()[0].translate((0, -20 * i[0], i[1] / 2)))
        print("Built r" + str(i[0]))
    for homingType in HomingType:
        showcase.add(c.clone().row(3).homing(homingType).build()[0].translate((20 * homingType.value, -20 * 3, 0)))
        print("Built homing " + homingType.name)
    showcase.add(c.clone().row(3).inverted().build()[0].translate((0, -20 * 5, 0)))
    print("Built inverted r3")
    showcase.add(c.clone().isoEnter().build()[0].translate((30, 0, 0)))
    print("Built ISO enter")
    showcase.add(c.clone().width(1.75).length(1).stepped().build()[0].translate((-30, 0, 0)))
    print("1.75 Stepped")
    showcase.add(c.clone().width(1.75).length(1).build()[0].translate((-30, -20, 0)))

    showcase.add(c.clone().width(6.25).inverted().build()[0].translate((0, 30, 0)))
    print("6.25 inverted")
    showcase.add(c.clone().width(2.75).build()[0].translate((0, 30 + 20, 0)))
    print("2.75")
    if c._show_object_exists():
        show_object(showcase)
    # showcase.save(showcase.name + ".step", "STEP")
    # cq.exporters.export(showcase.toCompound(), showcase.name + ".stl")


def all_rows():
    for i in [1, 2, 3, 4]:
        c = QSC().row(i).width(7).inverted().step(9).homing(HomingType.BAR)  # .legend(str(i), fontSize=6)
        h = 1  # c._height
        show_object(c.build()[0].translate((0, -(i - 1) * 19, h / 2)))


def all_rows_with_legends(width):
    for row in [1, 2, 3, 4]:
        for rIdx, rotation in enumerate([0, 90, 180, 270]):
            c = QSC().row(row).width(width).legend(str(row) + "." + str(rIdx), fontSize=6).stemRotation(rotation)
            h = c._height
            show_object(c.build()[0].translate((19 * width * rIdx, -(row - 1) * 19, h / 2)))


def test_fillet():
    for row in range(1, 5):
        for width in [1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 6.25, 7]:
            for type in ["normal", "inverted", "stepped"]:
                q = QSC().row(row).width(width).fillet(1)
                if type == "normal":
                    q = q
                elif type == "inverted":
                    q = q.inverted()
                elif type == "stepped":
                    q = q.stepped()

                try:
                    f = q.maxPossibleFillet()
                    print("Row", row, ", width", width, ", type", type, ":   ", f)
                except RuntimeError:
                    print("Failed to find max for row", row, "width", width, "type", type)


# all_rows_with_legends(2)
# all_rows()

# showcase()
# Build your own cap here
# cap = QSC().row(3).width(16.25).step(3).stepped()#.topFillet(0)
# c,l = cap.build()
# show_object(c)


# show_object(QSC().homing().build()[0])
# show_object(QSC().build()[0].translate((20,0,0)))
# show_object(QSC().stepped().legend("A",6).build()[0])
# all_rows_with_legends(1)
# all_rows()
def scooped_or_no():
    for i in [1, 2, 3, 4]:
        c = QSC().row(i).width(1).legend(str(i), fontSize=6).step(2)
        b = QSC().row(i).width(1).homing().legend(str(i) + "h", fontSize=6).step(2)
        h = c._height
        k = b._height
        cc = c.build()[0]
        bb = b.build()[0]
        ccz = cc.findSolid().BoundingBox().zlen
        bbz = bb.findSolid().BoundingBox().zlen
        print(
            ccz,
            bbz,
            ccz - bbz,
        )
        show_object(cc.translate((0, -(i - 1) * 19, h / 2)))
        show_object(bb.translate((20, -(i - 1) * 19, k / 2)))


def test_all_types_same_width():
    print()

    def bb(cap):
        return cap.findSolid().BoundingBox()

    for row in [3]:  # ,2,3,4]:
        for width in [2]:  # ,2,3,6.25,7]:
            qsc = QSC().row(row).width(width)
            normal, _ = qsc.build()
            stepped, _ = qsc.clone().stepped().build()
            inverted, _ = qsc.clone().inverted().build()

            nBB = bb(normal)
            sBB = bb(stepped)
            iBB = bb(inverted)

            print(nBB.xlen, sBB.xlen, "r" + str(row) + " w" + str(width) + " n vs s X", nBB.xlen == sBB.xlen)
            print(nBB.xlen, iBB.xlen, "r" + str(row) + " w" + str(width) + " n vs i X", nBB.xlen == iBB.xlen)
            print(sBB.xlen, iBB.xlen, "r" + str(row) + " w" + str(width) + " s vs i X", sBB.xlen == iBB.xlen)

            print(nBB.ylen, sBB.ylen, "r" + str(row) + " w" + str(width) + " n vs s Y", nBB.ylen == sBB.ylen)
            print(nBB.ylen, iBB.ylen, "r" + str(row) + " w" + str(width) + " n vs i Y", nBB.ylen == iBB.ylen)
            print(sBB.ylen, iBB.ylen, "r" + str(row) + " w" + str(width) + " s vs i y", sBB.ylen == iBB.ylen)
            show_object(normal)
            show_object(stepped.translate((20, 0, 0)))
            show_object(inverted.translate((-20, 0, 0)))


# qsc = QSC().row(1).width(1)
# n,_ = qsc.build()
# i,_ = qsc.inverted().build()
# s,_ = qsc.stepped().build()
#
# show_object(n)
# show_object(i.translate((20,0,0)))
# show_object(s.translate((-20,0,0)))
# test_all_types_same_width()

# build_ = QSC().row(1).homing().step(2).build()[0]
# show_object(build_)
# scooped_or_no()
# all_rows_with_legends(2)
# all_rows()
s = QSC().row(1).width(U(2.25)).inverted().step(2).build()[0]
#show_object(s)
#show_object(QSC().row(3)._createDish(True))
