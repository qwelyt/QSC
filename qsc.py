import cadquery as cq

class QSC:
    _wallThickness=0
    _topThickness=0

    def __init__(self, wallThickness=3, topThickness=2.4):
        self._wallThickness = wallThickness
        self._topThickness = topThickness
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
        diff = -7
        stemD = 5.6
        b = self._box(w,l, h, diff, 0,0, "fillet")#.fillet(0.7)
        #hollow = self._box(iw,il, ih, diff, 0 ,0, "none")
        #stem = self.stem(ih,stemD, "cherry")
        #stemSupport = self.stemSupport(ih-0.2, il, diff, stemD).translate((0, -il/4-stemD/2+1, 0))

        #b = b.cut(hollow)

        #b = b.union(stem)

        #b = b.union(stemSupport)

        return b
    def _hollow(self, w,l,h,diff, topThickness=None, wallThickness=None):
        topThickness = topThickness or self._topThickness
        wallThickness = wallThickness or self._wallThickness
        ih = h - topThickness
        iw = w - wallThickness
        il = l - wallThickness
        hollow = self._box(iw,il, ih, diff*-1, 0 ,0, "none")
        return hollow
        

    def dish(self, width=1, length=1, depth=1.2):
        dd = pow((pow(width,2) + pow(length, 2)),0.5) 
        s_x, s_y, s_z = dd/2/depth, dd/2/depth, 1.0
        scale_matrix = cq.Matrix(
            [
                [s_x, 0.0, 0.0, 0.0],
                [0.0, s_y, 0.0, 0.0],
                [0.0, 0.0, s_z, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        scaledSphere = (cq.Solid
                .makeSphere(depth, angleDegrees1=-90)
                .transformGeometry(scale_matrix)
                )

        return scaledSphere


    def row3(self, width=1, length=1, inverted=False):
        capHeight=8
        diff = 7
        w = self._toMM(width)
        l = self._toMM(length)
        dishThickness=1.2
        stemD = 5.6
        dish = self.dish(w-diff/1.2,l-diff/1.2, dishThickness)
            
        base = self._base(width, length, capHeight)
        h = base.findSolid().BoundingBox().zmax

        cap = base
        if inverted:
            i = base.intersect(dish.translate((0,0,h-dishThickness)))
            cap = base.faces(">Z").sketch().rect(w,l).finalize().extrude(-dishThickness, "cut")

            cap = cap.union(i)
        else:
            cap = base.cut(dish.translate((0,0,h)))

        cap = cap.fillet(0.685)

        cap = cap.cut(self._hollow(w, l, capHeight, diff))

        cap = cap.union(self.stem(capHeight-self._topThickness,stemD, "cherry"))
        il = l-self._wallThickness
        cap = cap.union(self.stemSupport(capHeight-self._topThickness-0.2, il, diff*-1, stemD).translate((0, -il/4-stemD/2+1, 0)))

        return cap.translate((0,0,-capHeight/2))



    def row4(self):
        h = 13
        sphereD = self._toMM(1)*1.6
        dish = cq.Workplane("XY").sphere(sphereD).translate((0,2,h/2+sphereD-4))

        return  self._base().cut(dish)

    def p(self):
        width=17
        length=17
        depth = 1.2
        dd = pow((pow(width,2) + pow(length, 2)),0.5) 
        #a = cq.Workplane("XY").sphere(dd).translate((0,0,-dd/5))
        #b = cq.Workplane("XY").box(width, length, depth)
        #c = a.intersect(b.translate((0,0,dd)))
        #d = c.union(b)
        a,b,c = 10,10,10

        f1 = (
          cq.Workplane('XY')
          .box(a,b,c)
          )

        f2 = (
          cq.Workplane('XY')
          .sphere(a)
          .translate((0,0,-a/5))
          )
        s_x, s_y, s_z = dd/2/depth, dd/2/depth, 1.0
        scale_matrix = cq.Matrix(
            [
                [s_x, 0.0, 0.0, 0.0],
                [0.0, s_y, 0.0, 0.0],
                [0.0, 0.0, s_z, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        f5 = cq.Workplane(cq.Solid
                    .makeSphere(depth, angleDegrees1=-90)
                    .transformGeometry(scale_matrix)
                    )

        f3 = f5.intersect(f1.translate((0,0,a)))
        f4 = f3.union(f1)
        s = f5.rect(width,length).cutThruAll()
        ff = f1.rect(20,2).cutThruAll()
        #return f2.intersect(ff.translate((0,0,8)))
        #return s.intersect(f5.translate((0,0,1)))
        return f5.cut(s)

    def d(self):
        pass


cap = QSC()
#r2 = cap.row2()
r3 = cap.row3(1,1, False)
r3i = cap.row3(1,1, True)
r4 = cap.row4()
show_object(r3, options={"alpha":0, "color":(255,10,50)})
show_object(r3i.translate((20,20,0)), options={"alpha":0, "color":(255,10,50)})
#show_object(r3[1], options={"alpha":0, "color":(25,10,50)})
#show_object(cap.dish())
#show_object(cap.p())
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
#a = 5
#
#f1 = (
#  cq.Workplane('XY')
#  .box(a*2,a*2,a)
#  )
#
#f2 = (
#  cq.Workplane('XY')
#  .sphere(a)
#  .translate((0,0,-a/5))
#  )
#
#f3 = f2.intersect(f1.translate((0,0,a)))
#f4 = f3.union(f1)
#show_object(f4) 

#aw = 18
#diff = 9
#a = (cq.Sketch().rect(18,18))
#b = (cq.Sketch().rect(11,11))
#b1 = (cq.Sketch().rect(aw-diff,aw-diff))
#c = (cq.Workplane().placeSketch(a, b.moved(cq.Location(cq.Vector(0,0,7)))).loft())
#c1 = (cq.Workplane().placeSketch(a, b1.moved(cq.Location(cq.Vector(0,0,diff)))).loft())
#
#h = c1.findSolid().BoundingBox().zmax
#dish = cap.dish(aw-diff/1.2,aw-diff/1.2).translate((0,0,h-1.2))
#
#i = c1.intersect(dish)
#c2 = c1.faces(">Z").sketch().rect(aw,aw).finalize().extrude(-1.2, "cut")

#show_object(c)
#show_object(c1, options={"alpha":0.8, "color":(255,0,0)})
#show_object(dish, options={"alpha":0.8, "color":(0,255,0)})
#show_object(i)
#show_object(c2.union(i))
