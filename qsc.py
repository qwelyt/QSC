from enum import Enum, auto
from typing import Tuple

import cadquery as cq


# TODO
# * Alps?
# * Legends

class HomingType(Enum):
    BAR = 1
    SCOOPED = 2
    DOT = 3


class StemType(Enum):
    CHERRY = auto()


class Constants():
    STEP_PERCENTAGE = 0.7142857142857143
    U_IN_MM = 19.05


class QSC:
    _wallThickness = 3  # mm
    _topThickness = 2.4  # mm
    _width = 1  # u
    _length = 1  # u
    _height = 8  # mm
    _bottomWidth = 1  # u
    _topDiff = -7  # mm
    _dishThickness = 1.2  # mm
    _stemType = StemType.CHERRY
    _stemOffset = (0, 0, 0)
    _stemRotation = 0
    _stemCherryDiameter = 5.6  # mm
    _stemSupport = True
    _specialStabPlacement = None
    _stemVSlop = 0.0  # mm
    _stemHSlop = 0.0  # mm
    _inverted = False
    _homingType = None  # None, Bar, Scooped, Dot
    _stepped = False
    _isoEnter = False
    _row = 3
    _fillet = 0.685

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

    def _toMM(self, u):
        return u * Constants.U_IN_MM

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
            return (cq.Workplane().box(2, 2, stemHeight))

    def _buildStemSupport(self, cap):
        if self._stemType == StemType.CHERRY:
            capBB = cap.findSolid().BoundingBox()
            wORl = capBB.ylen if self._stemRotation == 0 or self._stemRotation == 180 else capBB.xlen
            wORl = wORl - self._toMM(0.25) if self._isoEnter else wORl
            w = (wORl - self._wallThickness) / 2 - self._stemCherryDiameter / 2
            h = self._height - self._topThickness - 0.2
            d = self._topDiff + (self._height - h) + 1

            a = self._srect(0.5, w, op="none")
            b = self._srect(0.5, w + d, op="none")

            supportOffset = -(-(wORl - self._wallThickness) / 4 - self._stemCherryDiameter / 2 + 1)
            return (cq.Workplane("XY")
                    .placeSketch(a, b.moved(cq.Location(cq.Vector(0, d / 2, h))))
                    .loft()
                    .translate((0, supportOffset, 0))
                    )
        else:
            return (cq.Workplane("XY").box(2, 2, 2))

    def _stemAndSupport(self, cap):
        wORl = self._width if self._stemRotation == 0 or self._stemRotation == 180 else self._length
        w = cq.Workplane("XY")
        s = self._stem().union(self._buildStemSupport(cap)) if self._stemSupport else self._stem()
        w.add(s.translate(self._stemOffset))

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

        return w.combine().rotate((0, 0, 0), (0, 0, 1), self._stemRotation)

    def _base(self):
        l = self._toMM(self._length)
        if self._stepped:
            bw = self._toMM(self._width)
            w1 = bw * Constants.STEP_PERCENTAGE
            high = self._box(w1, l, self._height, self._topDiff, 0, 0, "none")
            step = self._box(bw, l, self._height / 2, self._topDiff + (self._height / 2) - 0.5, 0, 0, "none")
            return high.translate((-w1 / 4.6, 0, 0)).add(step.translate((0, 0, 0))).combine()
        elif self._isoEnter:
            w = self._toMM(self._width)
            w6 = w / 6
            lower = self._box(w - w6, l, self._height, self._topDiff, 0, 0, "none")
            upper = self._box(w, l / 2, self._height, self._topDiff, 0, 0, "none")
            return lower.add(upper.translate((-w6 / 2, l / 4, 0))).combine()
        else:
            w = self._toMM(self._width)
            return self._box(w, l, self._height, self._topDiff, 0, 0, "none")

    def _hollow(self):
        il = self._toMM(self._length) - self._wallThickness
        iw = self._toMM(self._width) - self._wallThickness
        if self._stepped:
            bw = self._toMM(self._width)
            w1 = bw * Constants.STEP_PERCENTAGE
            ihHigh = self._height - self._topThickness
            ihStep = self._height / 2 - self._topThickness
            high = self._box(w1 - self._wallThickness, il, ihHigh, self._topDiff, 0, 0, "none")
            step = self._box(iw, il, ihStep, self._topDiff + (self._height / 2) - 0.5, 0, 0, "none")
            return high.translate((-w1 / 4.6, 0, 0)).add(step.translate((0, 0, 0))).combine()
        elif self._isoEnter:
            ih = self._height - self._topThickness
            il2 = self._toMM(1) - self._wallThickness
            w = self._toMM(self._width)
            w6 = w / 6
            iw2 = iw - w6
            lower = self._box(iw2, il, ih, self._topDiff, 0, 0, "none")
            upper = self._box(iw, il2, ih, self._topDiff, 0, 0, "none")
            return lower.add(upper.translate((-w6 / 2, il2 / 1.65, 0))).combine()
        else:
            ih = self._height - self._topThickness
            return self._box(iw, il, ih, self._topDiff, 0, 0, "none")

    def _createDish(self):
        if self._homingType == HomingType.SCOOPED:
            self._dishThickness = self._dishThickness * 1.1 if self._inverted else self._dishThickness * 1.5
        isoOrNot = self._toMM(2) if self._isoEnter else self._toMM(self._width)
        w = isoOrNot - self._topDiff * -1 / 1.2
        l = self._toMM(self._length) - self._topDiff * -1 / 1.2
        dd = pow((pow(w, 2) + pow(l, 2)), 0.5)
        row_adjustments = {
            1: (2, 0.5),
            2: (1, 0.2),
            3: (0, 0),
            4: (-1, 0.2),
            5: (0, 0)
        }.get(self._row)
        dishT = self._dishThickness - row_adjustments[1]
        s_x, s_y, s_z = dd / 2 / dishT, dd / 2 / dishT, 1.0
        scale_matrix = cq.Matrix(
            [
                [s_x, 0.0, 0.0, 0.0],
                [0.0, s_y, 0.0, 0.0],
                [0.0, row_adjustments[0], s_z, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        scaled_sphere = (cq.Solid
                         .makeSphere(self._dishThickness, angleDegrees1=-90)
                         .transformGeometry(scale_matrix)
                         )
        return scaled_sphere

    def _dish(self, cap):
        dish = self._createDish()
        capBB = cap.findSolid().BoundingBox()
        h = capBB.zmax
        if self._inverted:
            i = cap.intersect(dish.translate((0, 0, h - self._dishThickness)))
            cap = cap.faces(">Z").sketch().rect(capBB.xlen, capBB.ylen).finalize().extrude(-self._dishThickness, "cut")
            cap = cap.union(i)
        else:
            cap = cap.cut(dish.translate((0, 0, h)))

        return cap

    def _homing(self, cap):
        capBB = cap.findSolid().BoundingBox()
        if self._homingType == HomingType.SCOOPED:
            return cap  # Handled in dish creation
        elif self._homingType == HomingType.BAR:
            barSize = 1
            return cap.add(cq.Workplane()
                           .sketch()
                           .rect(capBB.xlen / 3, barSize)
                           .finalize()
                           .extrude(1)
                           .fillet(barSize / 2.5)
                           .translate((0, capBB.ylen / 2 + self._topDiff / 1.5, capBB.zlen - self._dishThickness))
                           )
        elif self._homingType == HomingType.DOT:
            dotSize = 2
            return cap.add(cq.Workplane()
                           .sphere(dotSize)
                           .translate((0, 0, capBB.zlen - dotSize))
                           )
        else:
            return cap

    def wallThickness(self, thickness: float):
        self._wallThickness = thickness
        return self

    def topThickness(self, thickness: float):
        self._topThickness = thickness
        return self

    def width(self, width: float):
        self._width = width
        return self

    def length(self, length: float):
        self._length = length
        return self

    def height(self, height: float):
        self._height = height
        return self

    def bottomWidth(self, width: float):
        self._bottomWidth = width
        return self

    def topDiff(self, diff: float):
        self._topDiff = diff
        return self

    def stemType(self, type: StemType):
        self._stemType = type
        return self

    def stemOffset(self, offset: Tuple[float, float, float]):
        self._stemOffset = offset
        return self

    def stemRotation(self, rotation: float):
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

    def homing(self, type: HomingType = HomingType.SCOOPED):
        self._homingType = type
        return self

    def inverted(self, inverted: bool = True):
        self._inverted = inverted
        return self

    def stepped(self, steppedKey: bool = True):
        self._stepped = steppedKey
        lowerWidth = self._width * Constants.STEP_PERCENTAGE
        offset = (Constants.U_IN_MM * (self._width - lowerWidth) / 2.0)
        return self.stemOffset((-offset, 0.0, 0.0))

    def isoEnter(self, iso: bool = True):
        self._isoEnter = iso
        self.width(1.5)
        self.length(2)
        self.stemRotation(270)
        self.fillet(0.3)
        return self

    def fillet(self, value: float):
        self._filetValue = value
        return value

    def row(self, row: int):
        self._row = row
        height_adjustments = {
            1: 4,
            2: 1,
            3: 0,
            4: 1,
            5: 2,
        }.get(self._row)
        self.height(self._height + height_adjustments)
        return self

    def filleting(self, value: float):
        self._fillet = value
        return self

    def clone(self):
        return (QSC()
                .wallThickness(self._wallThickness)
                .topThickness(self._topThickness)
                .width(self._width)
                .length(self._length)
                .height(self._height)
                .bottomWidth(self._bottomWidth)
                .topDiff(self._topDiff)
                .stemType(self._stemType)
                .stemCherryDiameter(self._stemCherryDiameter)
                .stemVSlop(self._stemVSlop)
                .stemHSlop(self._stemHSlop)
                .disableStemSupport(not self._stemSupport)
                .inverted(self._inverted)
                .row(self._row)
                )

    def build(self):
        cap = self._base()
        cap = self._dish(cap)
        cap = cap.fillet(self._fillet)
        cap = self._homing(cap)
        cap = cap.cut(self._hollow())
        cap = cap.union(self._stemAndSupport(cap))

        return cap.translate((0, 0, -self._height / 2))

    def name(self):
        name = "qsc_row" + str(self._row)
        name = name + "_isoEnter" if self._isoEnter else name + "_" + str(self._width) + "x" + str(self._length)
        name = name + "_i" if self._inverted else name
        name = name + "_stepped" if self._stepped else name
        return name


def showcase():
    c = QSC()
    showcase = (cq.Assembly(name="QSC_showcase"))
    for i in [(1, 4), (2, 1), (3, 0), (4, 1)]:
        showcase.add(c.clone().row(i[0]).build().translate((0, -20 * i[0], i[1] / 2)))
    for homingType in HomingType:
        showcase.add(c.clone().row(3).homing(homingType).build().translate((20 * homingType.value, -20 * 3, 0)))
    showcase.add(c.clone().row(3).inverted().build().translate((0, -20 * 5, 0)))
    showcase.add(c.clone().isoEnter().build().translate((30, 0, 0)))
    showcase.add(c.clone().width(1.75).length(1).stepped().build().translate((-30, 0, 0)))
    showcase.add(c.clone().width(1.75).length(1).build().translate((-30, -20, 0)))
    showcase.add(c.clone().width(6.25).inverted().build().translate((0, 30, 0)))
    showcase.add(c.clone().width(2.75).build().translate((0, 30 + 20, 0)))
    show_object(showcase)
    showcase.save(showcase.name + ".step", "STEP")
    cq.exporters.export(showcase.toCompound(), showcase.name + ".stl")

showcase() # Comment out this line when doing your own thing
# Build your own cap here
# cap = QSC().build()
# cq.exporters.export(cap.rotate((0,0,0),(1,0,0),-90), cap.name+".stl")
