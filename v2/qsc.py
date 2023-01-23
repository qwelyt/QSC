import cadquery as cq

U_IN_MM = 19.05

class U(object):
    def __init__(self, val):
        self._val = val
        
    def mm(self):
        return MM(self._val*U_IN_MM)
    
    def u(self):
        return self
    
    def get(self):
        return self._val

class MM(object):
    def __init__(self, val):
        self._val = val
    
    def mm(self):
        return self
    
    def u(self):
        return U(self._val / U_IN_MM)
    
    def get(self):
        return self._val

class QSC(object):
    _bottom = (MM(18.2),MM(18.2))
    _bottom_fillet = MM(1)
    _top = (MM(12),MM(12))
    _top_fillet = MM(2)
    _height = MM(13)
    _wall_thickness = MM(3)
    _top_thickness = MM(3+2.8)
    _edge_fillet = MM(0.2)
    _dish_depth = MM(2.8)
    _convex = True
    
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
            return (cq.Workplane("YZ").transformed(offset=cq.Vector(0, height-2.1, -bx/2), rotate=cq.Vector(0, 0, angle))
            .moveTo(-by/2, -1)
            .threePointArc((0, 2), (by/2, -1))
            .lineTo(by/2, 10)
            .lineTo(-by/2, 10)
            .close()
            .extrude(bx, combine=False)
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
    
    def build(self):
        base = (QSC._base(self._top, self._bottom, self._top_fillet, self._bottom_fillet, self._height)

                )
        dish = QSC._dish(self._top, self._bottom, self._height, self._dish_depth, self._convex, 0)
        #debug(dish)

        baseDish = (base - dish).edges().fillet(self._edge_fillet.mm().get())
        
        cut = QSC._base(
            tuple(map(lambda v: MM(v.mm().get()-self._wall_thickness.mm().get()), self._top)), 
            tuple(map(lambda v: MM(v.mm().get()-self._wall_thickness.mm().get()), self._bottom)), 
            self._top_fillet, 
            self._bottom_fillet, 
            MM(self._height.mm().get()-self._top_thickness.mm().get())
            )
        #debug(cut)
        
        
        return baseDish-cut
    

c = QSC().build()

show_object(c)