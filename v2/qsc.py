import cadquery as cq
import math

U_IN_MM = 19.05
UC_IN_MM = 18.2

class U(object):
    def __init__(self, val):
        self._val = val
        
    def mm(self):
        return MM(self._val*U_IN_MM)
    
    def u(self):
        return self
    
    def get(self):
        return self._val

class UC(object):
    def __init__(self, val):
        self._val = val
        
    def mm(self):
        return MM(self._val*UC_IN_MM)
    
    def get(self):
        return self._val

class MM(object):
    def __init__(self, val):
        self._val = val
    
    def __add__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return MM(self._val+other)
        if isinstance(other, MM) or isinstance(other, U):
            return MM(self._val + other.mm().get())
        
        raise Error()
        
    def __sub__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return MM(self._val-other)
        if isinstance(other, MM) or isinstance(other, U):
            return MM(self._val - other.mm().get())
        
        raise Error()
        
    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return MM(self._val*other)
        if isinstance(other, MM) or isinstance(other, U):
            return MM(self._val * other.mm().get())
        
        raise Error()
        
    
    def mm(self):
        return self
    
    def u(self):
        return U(self._val / U_IN_MM)
    
    def get(self):
        return self._val

class QSC(object):
    _dish_depth = MM(1.3)
    _bottom = (UC(1).mm(),UC(1).mm())
    _bottom_fillet = MM(1)
    _top = (MM(11),MM(11))
    _top_fillet = MM(2)
    _height = MM(8)
    _wall_thickness = MM(1.5)
    _top_thickness = MM(1.5)+_dish_depth
    _edge_fillet = MM(0.2)
    _convex = False
    _build_step = 20
    _rotated = True
    
    def _base(top, bottom, top_fillet, bottom_fillet, height):
        top = (cq.Sketch()
               .rect(top[0].mm().get(), top[1].mm().get())
               .vertices()
               .fillet(top_fillet.mm().get())
               )
        bottom = (cq.Sketch()
                  .rect(bottom[0].mm().get(), bottom[1].mm().get())
                  .vertices()
                  .fillet(bottom_fillet.mm().get())
                  )
        
        return (cq.Workplane()
                .placeSketch(
                    bottom,
                    top.moved(cq.Location(cq.Vector(0,0,height.mm().get())))
                    )
                .loft()
                )
    
    def _dish(top, bottom, height, depth, convex, angle):
        bx = bottom[0].mm().get()
        by = bottom[1].mm().get()

        tx = bx - (bottom[0].mm().get() - top[0].mm().get())
        ty = by - (bottom[1].mm().get() - top[1].mm().get())
        height = height.mm().get()
        depth = depth.mm().get()
        if convex:
            return(cq.Workplane("YZ").transformed(offset=cq.Vector(0, height-depth, bx/2), rotate=cq.Vector(0, 0, angle))
                .moveTo(-by/2+2,0)
                .threePointArc((0, min(-0.1, -depth+1.5)), (by/2-2, 0))
                .lineTo(by/2, height)
                .lineTo(-by/2, height)
                .close()
                .workplane(offset=-bx/2)
                .moveTo(-by/2-2, -0.5)
                .threePointArc((0, depth), (by/2+2, -0.5))
                .lineTo(by/2, height)
                .lineTo(-by/2, height)
                .close()
                .workplane(offset=-bx/2)
                .moveTo(-by/2+2, 0)
                .threePointArc((0, min(-0.1, -depth+1.5)), (by/2-2, 0))
                .lineTo(by/2, height)
                .lineTo(-by/2, height)
                .close()
                .loft(combine=False)
            )
        else:
            return(cq.Workplane("YZ").transformed(offset=cq.Vector(0, height, bx/2), rotate=cq.Vector(0, 0, angle))
                .moveTo(-by/2+2,0)
                .threePointArc((0, min(-0.1, -depth+1.5)), (by/2-2, 0))
                .lineTo(by/2, height)
                .lineTo(-by/2, height)
                .close()
                .workplane(offset=-bx/2)
                .moveTo(-by/2-2, -0.5)
                .threePointArc((0, -depth), (by/2+2, -0.5))
                .lineTo(by/2, height)
                .lineTo(-by/2, height)
                .close()
                .workplane(offset=-bx/2)
                .moveTo(-by/2+2, 0)
                .threePointArc((0, min(-0.1, -depth+1.5)), (by/2-2, 0))
                .lineTo(by/2, height)
                .lineTo(-by/2, height)
                .close()
                .loft(combine=False)
            )
            
            return scoop
    
    def _stem(cap):
        cross = (1.55, 4.25)
        cross_sketch = (cq.Sketch()
                        .rect(cross[0], cross[1])
                        .rect(cross[1], cross[0])
                        .clean()
                        )
        core = (cap.faces("<Z")
                .workplane()
                .sketch()
                .circle(5.6/2)
                .finalize()
                .extrude(until="next")
                ) - cap
        
        height = core.findSolid().BoundingBox().zlen
        stem = (core.faces("<Z")
                .workplane()
                .placeSketch(cross_sketch)
                .extrude(-height, combine="cut")
                ).faces("<Z").chamfer(0.2)
        
        
        return stem
        
    
    def _stem_support(cap):
        delta = 0.15
        stem_radius = 5.6/2
        pillar = (cap.faces("<Z")
                  .workplane()
                  .sketch()
                  .push([(0, stem_radius + delta/2)])
                  .rect(0.5,0.1)
                  .finalize()
                  .extrude(until="next")
                  ) - cap
        
        face = pillar.faces("<Y").workplane(centerOption="CenterOfMass")
        r = face.findSolid().BoundingBox()
        support = (cq.Workplane()
                   .add(cap)
                   .copyWorkplane(face)
                   .sketch()
                   .rect(r.xlen, r.zlen - delta)
                   .finalize()
                   .extrude(until="next")
                   ) - cap
        
        return support
    
    
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
    
    def build(self):
        #print(self._top_thickness)
        base = 0
        cap = 0
        if self._build_step > 0:
            base = (QSC._base(self._top, self._bottom, self._top_fillet, self._bottom_fillet, self._height))
            cap = base
        if self._build_step > 1:
            dish = QSC._dish(self._top, self._bottom, self._height, self._dish_depth, self._convex, 0)
            #debug(dish)
            cap = (base - dish).edges().fillet(self._edge_fillet.mm().get())
        if self._build_step > 2:
            cut = (QSC._base(
                tuple(map(lambda v: v-self._wall_thickness*2, self._top)), 
                tuple(map(lambda v: v-self._wall_thickness*2, self._bottom)), 
                self._top_fillet, 
                self._bottom_fillet, 
                self._height
                ).faces(">Z")
                .rect(self._bottom[0].mm().get(), self._bottom[1].mm().get())
                .extrude(-self._top_thickness.mm().get(), combine="cut")
                )
            #cut = (base.faces(">Z")
            #       .rect(self._bottom[0].mm().get(), self._bottom[1].mm().get())
            #       .extrude(-self._top_thickness.mm().get(), "cut")
            #       )
            #debug(cut)
            cap = (cap-cut)
        if self._build_step > 3:
            stem = QSC._stem(cap)
            
            #debug(stem)
            cap = cap+stem
        
        if self._build_step > 4:
            stem_support = QSC._stem_support(cap)
            #debug(stem_support)
            cap = cap + stem_support
            
        if self._rotated:
            return self._rotate(cap, base, 180)
        else:
            return cap
    
    
    

q = QSC()
p = QSC()
p._convex = True

c = q.build()
d = p.build()

show_object(c)
show_object(d.translate((U(1).mm().get(),0,0)))

def apa():
    (cq.Workplane("YZ").transformed(offset=cq.Vector(0, height, bx/2), rotate=cq.Vector(0, 0, angle))
        .moveTo(-by/2+2,0)
        .threePointArc((0, 0), (by/2-2, 0))
        .lineTo(by/2, height)
        .lineTo(-by/2, height)
        .close()
        .workplane(offset=-bx/2)
        .moveTo(-by/2-2, -0.5)
        .threePointArc((0, -depth), (by/2+2, -0.5))
        .lineTo(by/2, height)
        .lineTo(-by/2, height)
        .close()
        .workplane(offset=-bx/2)
        .moveTo(-by/2+2, 0)
        .threePointArc((0, min(-0.1, -depth+1.5)), (by/2-2, 0))
        .lineTo(by/2, height)
        .lineTo(-by/2, height)
        .close()
        .loft(combine=False)
        )
def a():
    by=18
    bx=18
    height=20
    depth=3
    return (cq.Workplane("YZ").transformed(offset=cq.Vector(0, height, bx/2), rotate=cq.Vector(0,0,0))
          .moveTo(-by/2+2,0)
          .threePointArc((0,0),(by/2-2,-0.5))
          .lineTo(by/2, height)
          .lineTo(-by/2, height)
          .close()
          .workplane(offset=-bx/2)
          .moveTo(-by/2+2,0)
          .threePointArc((0,depth),(by/2-2,-0.5))
          .lineTo(by/2, height)
          .lineTo(-by/2, height)
          .close()
          .workplane(offset=-bx/2)
          .moveTo(-by/2+2,0)
          .threePointArc((0,0),(by/2-2,-0.5))
          .lineTo(by/2, height)
          .lineTo(-by/2, height)
          .close()
          .loft()
          )
#debug(cq.Workplane().rect(20,20).extrude(8-1.7))
# b = a()
# show_object(b)
# show_object(cq.Workplane().box(1,1,1))