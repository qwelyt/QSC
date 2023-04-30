# Things this thing should be able to do (in order of importance):
# (legend: + == done, - == ToDo)
# + Generate 1u caps
# + Generate with cherry stem
# + Generate support for the stem for printing
# + Concave caps
# + Convex caps
# + Different sizes: 1u, 2, 3, 6.25, 7
# + Generate stems for stabs at correct places for the size
# + Homing (scooped, bar, dot)
# - ISO enter
# - Rows, set angle
# - Off-center stems
# - Stepped simple caps, with off-center stem
# - Stepped ISO enter
# - Center-stepped keys (like on Cherry G84-4400
# - Legends on side (generate both the legend and make a cut in the model, to allow printin in two colours)
# - Legends on top
import cadquery as cq
import math
from enum import Enum

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
    def uc(self):
        return U(self._val / UC_IN_MM)
    
    def get(self):
        return self._val

class Homing(Enum):
    BAR = 1
    DOT = 2
    SCOOP = 3

class QSC(object):
    _dish_depth = MM(1.3)
    _width = UC(1).mm()
    _length = UC(1).mm()
    _top_diff = ((UC(1).mm()-MM(11).mm())*-1, (UC(1).mm()-MM(11).mm())*-1)
    _bottom_fillet = MM(1)
    _top_fillet = MM(2)
    _height = MM(8)
    _wall_thickness = MM(1.5)
    _top_thickness = MM(1.5)+_dish_depth
    _edge_fillet = MM(0.2)
    _convex = False
    _build_step = 20
    _rotated = True
    _homing = None
    
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
    def _homing_bump(cap, kind, dish_depth):
        cBB = cap.findSolid().BoundingBox()
        if kind == Homing.BAR:
            size = 0.5
            length = cBB.xlen/3
            bar = (((cap.faces("<<Z[3]")
                     .workplane()
                     .sketch()
                     .circle(size)
                     .finalize()
                     .extrude(length)
                   ) -cap
                   )
                   .fillet(size)
                   .rotateAboutCenter([0,1,0], 90)
                   .translate((0,-cBB.ylen/6,-length/2-size/1.7))
                   )
            return bar
        elif kind == Homing.DOT:
            size = 1
            dot = (cq.Workplane("YZ")
                   .sphere(size)
                   .translate((0, 0, cBB.zlen-(size*1.15)))
                   )
            return dot
        else:
            raise Exception("Unknown homing type:"+kind)
    
    def _stem_positions(width):
        positions = [(0,0)] # Always center (not true for stepped)
        if width < 2:
            return positions

        # https://deskthority.net/wiki/Space_bar_dimensions
        distance = 0
        if width >= 8:
            distance = U(3.5).mm().get()
        elif width >= 7:
            distance = U(3).mm().get()
        elif width >= 6.5:
            distance = U(2.75).mm().get()
        elif width >= 6.25:
            distance = U(2.1).mm().get()
        elif width >= 6:
            distance = U(2).mm().get()
        elif width >= 5.5:
            distance = U(2.25).mm().get()
        elif width >= 4.5:
            distance = U(1.82).mm().get()
        elif width >= 4:
            distance = U(1.5).mm().get()
        elif width >= 3:
            distance = U(1).mm().get()
        elif width >= 2:
            distance = MM(12).get()
        positions.extend([(distance,0),(-distance,0)])

        return positions


    def _stem(cap, bottom):
        positions = QSC._stem_positions(bottom[0].uc().get())
        cross = (1.4, 4.1)
        cross_sketch = (cq.Sketch()
                        .rect(cross[0], cross[1])
                        .rect(cross[1], cross[0])
                        .clean()
                        )
        stems = []
        for p in positions:
            core = (cap.faces("<Z")
                    .workplane()
                    .sketch()
                    .push([(p[0],p[1])])
                    .circle(5.6/2)
                    .finalize()
                    .extrude(until="next")
                    ) - cap
            
            height = core.findSolid().BoundingBox().zlen
            stem = (core.faces("<Z")
                    .workplane()
                    .move(p[0],p[1])
                    .placeSketch(cross_sketch)
                    .extrude(-height, combine="cut")
                    ).faces("<Z").chamfer(0.2)
            stems.append(stem)
        
        ret = cq.Workplane()
        for stem in stems:
            ret.add(stem)
        
        return ret
        
    
    def _stem_support(cap, bottom):
        delta = 0.15
        stem_radius = 5.6/2
        supports = []
        positions = QSC._stem_positions(bottom[0].uc().get())

        for pos in positions:
            pillar = (cap.faces("<Z")
                      .workplane()
                      .sketch()
                      .push([(pos[0], pos[1]+stem_radius + delta/2)])
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
            supports.append(support)
        
        ret = cq.Workplane()
        for support in supports:
            ret.add(support)
        
        return ret
    
    
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
        base = 0
        cap = 0
        top = (self._width + self._top_diff[0], self._length + self._top_diff[1])
        bottom = (self._width, self._length)
        if self._build_step > 0:
            # Build basic shape
            base = (QSC._base(top, bottom, self._top_fillet, self._bottom_fillet, self._height))
            cap = base

        if self._build_step > 1:
            # Cut the dish
            depth = self._dish_depth*2 if self._homing == Homing.SCOOP else self._dish_depth
            dish = QSC._dish(top, bottom, self._height, depth, self._convex, 0)
            cap = (base - dish).edges().fillet(self._edge_fillet.mm().get())

        if self._build_step > 2:
            # Add homing (scoop handled dish creation)
            if self._homing is not None and self._homing is not Homing.SCOOP:
                homing = QSC._homing_bump(cap, self._homing, self._dish_depth.mm().get())
                cap = (cap+homing)

        if self._build_step > 3:
            # Hollow out the cap
            cut = (QSC._base(
                tuple(map(lambda v: v-self._wall_thickness*2, top)), 
                tuple(map(lambda v: v-self._wall_thickness*2, bottom)), 
                self._top_fillet, 
                self._bottom_fillet, 
                self._height
                ).faces(">Z")
                .rect(bottom[0].mm().get(), bottom[1].mm().get())
                .extrude(-self._top_thickness.mm().get(), combine="cut")
                )
            cap = (cap-cut)

        if self._build_step > 4:
            # Add stem(s)
            stem = QSC._stem(cap, bottom)
            cap = cap+stem 
        
        if self._build_step > 5:
            # Add support to the stem(s) for printing
            stem_support = QSC._stem_support(cap, bottom)
            cap = cap + stem_support 
            
        if self._rotated:
            return self._rotate(cap, base, 180)
        else:
            return cap
    
    
    


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

#f = (cq.Workplane()
#     .sketch()
#     .circle(3/2)
#     .finalize()
#     .extrude(5)
#     .faces(">Z")
#     .workplane()
#     .sketch()
#     .rect(1.4, 2.65, mode='a')
#     .rect(2.65, 1.4, mode='a')
#     .clean()
#     .finalize()
#     .extrude(3)
#     )
#show_object(f)

def normal():
    q = QSC()
    q._width = UC(10).mm()
    p = QSC()
    p._width = UC(2).mm()
    b = QSC()
    b._width = UC(3).mm()
    #p._convex = True
    #p._bottom = (U(7).mm(), U(1).mm())
    #p._top = (U(7).mm()-(U(1).mm()-MM(11).mm()), MM(11).mm())

    c = q.build()
    d = p.build()
    e = b.build()

    show_object(c)
    #show_object(d)
    show_object(d.translate((0, U(1).mm().get(),0)))
    show_object(e.translate((0, U(2).mm().get(),0)))

def show_stems():
    for i,w in enumerate([1,2,3,4,4.5,5.5,6,6.25,6.5,7,8,9,9.75,10]):
        c = QSC()
        c._width = UC(w).mm()
        b = c.build()
        show_object(b.translate((0,U(i).mm().get(),0)))
#show_stems()

def simple():
    q = QSC()
    q._width = UC(1).mm()
    q._homing = Homing.BAR
    #q._rotated = False
    #q._build_step=2
    b = q.build()
    cBB = b.findSolid().BoundingBox()
    show_object(b)
simple()
