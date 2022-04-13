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
        w = width/3
        d = diff/4
        a = self._srect(w, 0.5, op="none")
        b = self._srect(w+d, 0.5, op="none")

        return (cq.Workplane("XY")
                .placeSketch(a, b.moved(cq.Location(cq.Vector(-d/2,0,height))))
                .loft()
                )


    def row3(self):
        h = 8
        ih = h-2.4
        wd = 19
        iwd = wd-3
        diff = -7
        stemD = 5.6
        sphereD = wd*1.6

        b = self._box(wd,wd, h, diff, 1,2, "fillet").fillet(0.7)
        hollow = self._box(iwd,iwd, ih, diff, 0 ,0, "none")
        dish = self._taperedCylinder(wd*1.5,0.0001,-2.2).translate((0,0,h+1))
        dish2 = cq.Workplane("XY").sphere(sphereD).translate((0,0,h+sphereD-1))
        stem = self.stem(ih,stemD, "cherry")
        stemSupport = self.stemSupport(ih-0.2, iwd, diff, stemD).translate((-stemD+0.0,0,0))

        b = b.cut(dish2).cut(hollow)

        b = b.union(stem)

        b = b.union(stemSupport)

        return b.translate((0,0,-h/2))


cap = QSC()
c = cap.row3()
show_object(c, options={"alpha":0, "color":(255,10,50)})
#cq.exporters.export(c, "qsc_row3.step", cq.exporters.ExportTypes.STEP)
#cq.exporters.export(c.rotate((0,0,0),(0,1,0),-90), "qsc_row3.stl")
