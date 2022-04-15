import cadquery as cq

class QSC:
    def __init__(self):
        pass

    def _srect(self, width, depth, delta=9, op="chamfer"):
        rect= (cq.Sketch().rect(width,depth))

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
        b = self._srect(width+diff, depth+diff, deltaB, op)
        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0,0,height))))
                .loft()
                )

    def _taperedCylinder(self, widthA, widthB, height):
        a = cq.Sketch().circle(widthA/2)
        b = cq.Sketch().circle(widthB/2)

        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0,0,height))))
                .loft()
                )

    def stem(self, h, d=5.6, type="cherry"):
        return (cq.Workplane("XY")
                .sketch()
                .circle(d/2)
                .rect(1.5,4.2, mode="s")
                .rect(4.2,1.5, mode="s")
                .finalize()
                .extrude(h)
                .faces("<Z")
                .chamfer(0.24)
                )

    def stemSupport(self, height, width, diff, stemD):
        w = width/2-stemD/2
        d = diff/4
        a = self._srect(0.5, w, op="none")
        b = self._srect(0.5, w+d, op="none")

        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(0, -d/2, height))))
                .loft()
                )

    def _toMM(self, u):
        return u*19

    def _base(self, width=1, length=1, h=8, topThickness=2.4, wallThickness=3):
        w = self._toMM(width)
        l = self._toMM(length)

        ih = h-topThickness
        iw = w - wallThickness
        il = l - wallThickness
        diff = -7
        stemD = 5.6
        b = self._box(w,l, h, diff, 0,0, "fillet").fillet(0.7)
        hollow = self._box(iw,il, ih, diff, 0 ,0, "none")
        stem = self.stem(ih,stemD, "cherry")
        stemSupport = self.stemSupport(ih-0.2, il, diff, stemD).translate((0, -il/4-stemD/2+1, 0))

        b = b.cut(hollow)

        b = b.union(stem)

        b = b.union(stemSupport)

        return b.translate((0,0,-h/2))

    def dish(self, width=1, length=1, depth=1.2, type=1):
        dd = pow((pow(width,2) + pow(length, 2)),0.5) if type == 1 else pow(pow(width,2),0.5);
        s_x, s_y, s_z = dd/2/depth, dd/2/depth, 1.0
        scale_matrix = cq.Matrix(
            [
                [s_x, 0.0, 0.0, 0.0],
                [0.0, s_y, 0.0, 0.0],
                [0.0, 0.0, s_z, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        return (cq.Solid
                .makeSphere(depth, angleDegrees1=-90)
                .transformGeometry(scale_matrix)
                )


    def row3(self, width=1, length=1, inverted=False):
        base = self._base(width, length)
        h = base.findSolid().BoundingBox().zmax
        if inverted:
            dish = self.dish(self._toMM(width)-7, self._toMM(length)-7, 1.2).translate((0,0,h))
            inDish = base.intersect(dish)
            inDish = inDish.rotate((0,0,0),(1,0,0),180).translate((0,0,h*2))
            return base#.union(inDish)
        else:
            dish = self.dish(self._toMM(width)-7, self._toMM(length)-7, 1.2).translate((0,0,h))
            return base.cut(dish)


    def row4(self):
        h = 13
        sphereD = self._toMM(1)*1.6
        dish = cq.Workplane("XY").sphere(sphereD).translate((0,2,h/2+sphereD-4))

        return  self._base().cut(dish)


cap = QSC()
#r2 = cap.row2()
r3 = cap.row3(1,1, False)
r4 = cap.row4()
show_object(r3, options={"alpha":0, "color":(255,10,50)})
#show_object(r3[1], options={"alpha":0, "color":(25,10,50)})
#show_object(cap.dish())
#show_object(r4.translate((0,-19,0)), options={"alpha":0, "color":(25,10,250)})
#s_x, s_y, s_z = 1.0, 1.5, 2.0
#s_x, s_y, s_z = 17.31/2/1.2, 17.31/2/1.2, 1.0
#scale_matrix = cq.Matrix(
#    [
#        [s_x, 0.0, 0.0, 0.0],
#        [0.0, s_y, 0.0, 0.0],
#        [0.0, 0.0, s_z, 0.0],
#        [0.0, 0.0, 0.0, 1.0],
#    ]
#)
#sphere = cq.Solid.makeSphere(3, angleDegrees1=-90)
#show_object(sphere.transformGeometry(scale_matrix))
#show_object(cq.Workplane().ellipse(10,20).extrude(2).revolve())
#cq.exporters.export(r3, "qsc_row3.step", cq.exporters.ExportTypes.STEP)
#cq.exporters.export(r3.rotate((0,0,0),(1,0,0),90), "qsc_row3.stl")
