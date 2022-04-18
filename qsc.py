import cadquery as cq


class QSC:
    _wallThickness = 3  # mm
    _topThickness = 2.4  # mm
    _width = 1  # u
    _length = 1  # u
    _height = 8  # mm
    _bottomWidth = 1  # u
    _topDiff = -7  # mm
    _dishThickness = 1.2  # mm
    _stemType = "cherry"
    _stemCherryDiameter = 5.6  # mm
    _stemSupport = True
    _stemVSlop = 0.0  # mm
    _stemHSlop = 0.0  # mm
    _inverted = False
    _row = 3

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
        return u * 19

    def _stem(self):
        stemHeight = self._height - self._topThickness
        if self._stemType == "cherry":
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

    def _buildStemSupport(self):
        if self._stemType == "cherry":
            w = (self._toMM(self._length) - self._wallThickness)/2 - self._stemCherryDiameter/2
            h = self._height - self._topThickness - 0.2
            d = self._topDiff + (self._height - h)+1

            a = self._srect(0.5, w, op="none")
            b = self._srect(0.5, w + d, op="none")

            return (cq.Workplane("XY")
                    .placeSketch(a, b.moved(cq.Location(cq.Vector(0, d/2, h))))
                    .loft()
                    )

    def _base(self):
        w = self._toMM(self._width)
        l = self._toMM(self._length)
        return self._box(w, l, self._height, self._topDiff, 0, 0, "fillet")

    def _hollow(self):
        ih = self._height - self._topThickness
        iw = self._toMM(self._width) - self._wallThickness
        il = self._toMM(self._length) - self._wallThickness
        return self._box(iw, il, ih, self._topDiff , 0, 0, "none")

    def _dish(self):
        w = self._toMM(self._width) - self._topDiff*-1 / 1.2
        l = self._toMM(self._length) - self._topDiff*-1 / 1.2
        dd = pow((pow(w, 2) + pow(l, 2)), 0.5)
        s_x, s_y, s_z = dd / 2 / self._dishThickness, dd / 2 / self._dishThickness, 1.0
        scale_matrix = cq.Matrix(
            [
                [s_x, 0.0, 0.0, 0.0],
                [0.0, s_y, 0.0, 0.0],
                [0.0, 0.0, s_z, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        return (cq.Solid
                .makeSphere(self._dishThickness, angleDegrees1=-90)
                .transformGeometry(scale_matrix)
                )

    def wallThickness(self, thickness):
        self._wallThickness = thickness
        return self

    def topThickness(self, thickness):
        self._topThickness = thickness
        return self

    def width(self, width):
        self._width = width
        return self

    def length(self, length):
        self._length = length
        return self

    def height(self, height):
        self._height = height
        return self

    def bottomWidth(self, width):
        self._bottomWidth = width
        return self

    def topDiff(self, diff):
        self._topDiff = diff
        return self

    def stemType(self, type):
        self._stemType = type
        return self

    def stemCherryDiameter(self, d):
        self._stemCherryDiameter = d
        return self

    def stemVSlop(self, slop):
        self._stemVSlop = slop
        return self

    def stemHSlop(self, slop):
        self._stemHSlop = slop
        return self

    def stemSupport(self, support):
        self._stemSupport = support
        return self

    def inverted(self, inverted):
        self._inverted = inverted
        return self

    def row(self, row):
        self._row = row
        return self

    def build(self):
        w = self._toMM(self._width)
        l = self._toMM(self._length)
        dish = self._dish()
        cap = self._base()
        h = cap.findSolid().BoundingBox().zmax

        if self._inverted:
            i = cap.intersect(dish.translate((0, 0, h - self._dishThickness)))
            cap = cap.faces(">Z").sketch().rect(w, l).finalize().extrude(-self._dishThickness, "cut")
            cap = cap.union(i)
        else:
            cap = cap.cut(dish.translate((0, 0, h)))

        cap = cap.fillet(0.685)

        cap = cap.cut(self._hollow())

        cap = cap.union(self._stem())
        il = l - self._wallThickness
        sl = -il / 4 - self._stemCherryDiameter/2 + 1 if self._stemType == "cherry" else -il / 4
        cap = cap.union(self._buildStemSupport().translate((0, -sl, 0)))

        return cap.translate((0, 0, -self._height / 2))


cap = QSC().row(3).width(2).length(1)
r3 = cap.build()
r3i = cap.inverted(True).build()
show_object(r3, options={"alpha": 0, "color": (255, 10, 50)})
show_object(r3i.translate((19.05, 19.05, 0)), options={"alpha": 0, "color": (255, 10, 50)})
# cq.exporters.export(r3, "qsc_row3.step", cq.exporters.ExportTypes.STEP)
# cq.exporters.export(r3i.rotate((0,0,0),(1,0,0),90), "qsc_r3_6_25u_i_.stl")
