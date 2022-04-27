from enum import Enum, auto
from typing import Tuple

import cadquery as cq
from OCP.StdFail import StdFail_NotDone


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
    _debug = False
    _wallThickness = 3  # mm
    _topThickness = 3  # mm
    _width = 1  # u
    _length = 1  # u
    _height = 8  # mm
    _legend = None
    _fontSize = _height
    _firstLayerHeight = 1.2
    _font = "Arial"
    _bottomWidth = 1  # u
    _topDiff = -7  # mm
    _dishThickness = 1.8  # mm
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
            h = self._height - self._topThickness - 0.3

            topBB = cap.faces("<Z").section(h).findSolid().BoundingBox()
            topLen = topBB.ylen if self._stemRotation == 0 or self._stemRotation == 180 else topBB.xlen
            topLen = topLen - self._toMM(0.25) if self._isoEnter else topLen
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

    def _addLegend(self, cap):
        sideSelector = {
            0: ">>Y[2]",
            90: "<<X[2]",
            180: "<<Y[2]",
            270: ">>X[2]"
        }.get(self._stemRotation)
        if self._legend is None:
            return (cap, None)
        nc = (cap.faces(sideSelector)
              .workplane(offset=-self._firstLayerHeight, centerOption="CenterOfMass")
              )
        nw = cq.Workplane().copyWorkplane(nc)
        c = nc.text(txt=self._legend, fontsize=self._fontSize, distance=self._firstLayerHeight, font=self._font)
        t = nw.text(txt=self._legend, fontsize=self._fontSize, distance=self._firstLayerHeight, font=self._font, combine='a', cut=False)
        return (c, t)

    def _base(self):
        l = self._toMM(self._length)
        if self._stepped:
            bw = self._toMM(self._width)
            w1 = bw * Constants.STEP_PERCENTAGE
            high = self._box(w1, l, self._height, self._topDiff, 0, 0, "none")
            step = self._box(bw, l, self._height / 2, self._topDiff / 2, 0, 0, "none")
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
        dd = pow((pow(w, 2) + pow(l, 2)), 0.5) + 1
        row_adjustments = {
            # (extra DD, extraDDinverted, translateY, translateZ, rotation)
            1: (2.0, 2.0, 0.0, -1.0, 15.0),
            2: (1.9, 1.9, -1.2, -0.03, 7.0),
            3: (0.0, 0.0, 0.0, 0.0, 0.0),
            4: (1.5, 1.55, 0.0, -0.23, -10.0),
            5: (0.0, 0.0, 0.0, 0.0, 0.0),
        }.get(self._row)
        dd = dd + row_adjustments[0]
        dd = dd + row_adjustments[1] if self._inverted else dd
        s_x, s_y, s_z = dd / 2 / self._dishThickness, dd / 2 / self._dishThickness, 1.0
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
        if self._inverted:
            return scaled_sphere

        b = cq.Solid.makeCylinder(self._dishThickness, dd).transformGeometry(scale_matrix)
        return (cq.Workplane()
                .add(scaled_sphere)
                .union(b)
                .translate((0, row_adjustments[2], row_adjustments[3]))
                .rotate((0, 0, 0), (1, 0, 0), row_adjustments[4])
                )

    def _dish(self, cap):
        dish = self._createDish()
        capBB = cap.findSolid().BoundingBox()
        h = capBB.zmax
        if self._inverted:
            i = cap.intersect(dish.translate((0, 0, h - self._dishThickness)))
            if self._debug:
                #show_object(i, options={"color": (0, 0, 0)})
                #show_object(dish.translate((0, 0, h - self._dishThickness)), options={"color": (255, 255, 255), "alpha": 0.7})
                show_object(cap.faces(">Z").sketch().rect(capBB.xlen, capBB.ylen).finalize().extrude(self._dishThickness*2))
                show_object(cap.faces(">Z").sketch().rect(capBB.xlen, capBB.ylen).finalize().extrude(-self._dishThickness))
            cap = cap.faces(">Z").sketch().rect(capBB.xlen, capBB.ylen).finalize().extrude(self._dishThickness*2, "cut")
            cap = cap.faces(">Z").sketch().rect(capBB.xlen, capBB.ylen).finalize().extrude(-self._dishThickness, "cut")
            if self._debug:
                pass
                #show_object(cap.translate((0,30,0)))
                #show_object(i.translate((0,50,0)))
            cap = cap.union(i)
        else:
            cap = cap.cut(dish.translate((0, 0, h)))
            if self._debug:
                show_object(dish.translate((0, 0, h)), options={"color": (255, 255, 255), "alpha": 0.7})


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

    def legend(self, legend: str, fontSize: float = -1, firstLayerHeight: float = 1.2, font: str = "Arial"):
        self._legend = legend
        self._fontSize = self._height if fontSize == -1 else fontSize
        self._firstLayerHeight = firstLayerHeight
        self._font = font
        return self

    def bottomWidth(self, width: float):
        self._bottomWidth = width
        return self

    def topDiff(self, diff: float):
        self._topDiff = diff
        return self

    def dishThickness(self, thickness: float):
        self._dishThickness = thickness
        return self

    def stemType(self, type: StemType):
        self._stemType = type
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
        self.stemRotation(90)
        self.fillet(0.3)
        return self

    def fillet(self, value: float):
        self._fillet = value
        return self

    def row(self, row: int):
        self._row = row
        row_adjustments = {
            1: (4, 2),
            2: (1, 0.5),
            3: (0, 0),
            4: (1, 0.5),
            5: (2, 0),
        }.get(self._row)
        self.height(self._height + row_adjustments[0])
        self.topThickness(self._topThickness + row_adjustments[1])
        return self

    def clone(self):
        return (QSC()
                .wallThickness(self._wallThickness)
                .topThickness(self._topThickness)
                .width(self._width)
                .length(self._length)
                .height(self._height)
                .legend(self._legend, self._fontSize, self._firstLayerHeight, self._font)
                .bottomWidth(self._bottomWidth)
                .topDiff(self._topDiff)
                .dishThickness(self._dishThickness)
                .stemType(self._stemType)
                .stemCherryDiameter(self._stemCherryDiameter)
                .stemVSlop(self._stemVSlop)
                .stemHSlop(self._stemHSlop)
                .disableStemSupport(not self._stemSupport)
                .inverted(self._inverted)
                .row(self._row)
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
        self.build()

    def isValid(self):
        base = self._base().tag("base")
        cap = self._dish(base)
        faces = cap.faces("%Plane")
        if self._show_object_exists():
            show_object(faces, options={"color":(255,0,0)})
            #show_object(cap.faces("not %Plane"), options={"alpha":0.99, "color":(0,0,255)})
        face_count = len(faces.edges().vals())
        valid = face_count == 4
        if not valid:
            self._printSettings()
            print(face_count)
        return valid


    def build(self):
        base = self._base().tag("base")
        cap = self._dish(base)

        if self._debug:
            show_object(base, options={"color": (0, 245, 0), "alpha": 0.4})
            show_object(cap, options={"color": (0, 0, 200), "alpha": 0.4})
            edges = self._edges(cap.edges().vals())
            show_object(edges[0][1], options={"color": (255, 0, 0)})
            print(edges[0][0])
            #show_object(cap.translate((0, cap.findSolid().BoundingBox().ylen + 4, 0)))

        # self._debug_edges(cap)
        if self._fillet > 0:
            try:
                cap = cap.fillet(self._fillet)
            except StdFail_NotDone:
                self._printSettings()
                raise ValueError("Fillet too big",
                                 "Your fillet setting [" + str(self._fillet) + "] is too big for the current shape (r" + str(self._row) + ", " + str(self._width) + "x" + str(
                                     self._length) + "). Try reducing it or change dish depth. Smallest edge is" + str(self._debug_edges(cap)[0]))
        cap = self._homing(cap)
        cap = cap.cut(self._hollow())
        cap = cap.union(self._stemAndSupport(cap))
        capNlegend = self._addLegend(cap)

        if self._legend is not None:
            return (
                capNlegend[0].translate((0, 0, -self._height / 2)),
                capNlegend[1].translate((0, 0, -self._height / 2))
            )
        return (capNlegend[0].translate((0, 0, -self._height / 2)), None)

    def name(self):
        name = "qsc_row" + str(self._row)
        name = name + "_isoEnter" if self._isoEnter else name + "_" + str(self._width) + "x" + str(self._length)
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
    if "show_object" in locals():
        show_object(showcase)
    showcase.save(showcase.name + ".step", "STEP")
    cq.exporters.export(showcase.toCompound(), showcase.name + ".stl")


# showcase()
# Build your own cap here
# for i in [1,2,3,4]:
#    c = QSC().row(i).legend(str(i), fontSize=6)
#    h = c._height
#    show_object(c.build()[0].translate((0, -i * 19, h / 2)))
# QSC().row(4).stepped().show()#.width(1).fillet(0).build()#.show()
#cap = QSC().row(3).width(1).length(1).inverted().dishThickness(1.82)#.fillet(0)
#valid = cap.isValid()
#valid = QSC().row(4).width(2).isValid()
#print(valid)
#cap.show()