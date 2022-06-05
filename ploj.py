import cadquery as cq


# b = cq.Workplane().myVersionThing()
def p():
    box = (cq.Workplane("XY")
           .box(10, 10, 10)
           .faces(">Z")
           .shell(1)
           )
    box_with_sketch = (box.faces(">Z")
                       .sketch()
                       .circle(5)
                       .rect(1, 10, mode="s")
                       .rect(4, 1, mode="s")
                       .finalize()
                       )
    extrude_value = box_with_sketch.extrude(-10)
    extrude_next = box_with_sketch.extrude(until="next")
    show_object(extrude_value)
    show_object(extrude_next.translate((13, 0, 0)))


def a():
    box = (cq.Workplane("XY")
           .box(10, 10, 10)
           .faces(">Z")
           .shell(1)
           )
    circle = (box.faces(">Z")
              .sketch()
              .circle(5)
              .finalize())
    cross = (cq.Sketch()
             .rect(1, 4)
             .rect(4, 1)
             )

    extrude1 = circle.extrude(until="next")
    # show_object(extrude1)

    extrude2 = (extrude1.faces(">Z")
                .placeSketch(cross)
                .extrude(until="last", combine="cut")
                )
    show_object(extrude2)  # .translate((13, 0, 0)))


def b():
    box = (cq.Workplane("XY")
           .box(10, 10, 10)
           .faces(">Z")
           .shell(1)
           )

    h = (box.faces(">Z")
         .sketch()
         .circle(5)
         .rect(1, 4, mode="s")
         .rect(4, 1, mode="s")
         .push([(5, 0)])
         .rect(10, 10, mode="s")
         .finalize()
         )

    g = (box.faces(">Z")
         .sketch()
         .circle(5)
         .rect(1, 4, mode="s")
         .rect(4, 1, mode="s")
         .push([(-5, 0)])
         .rect(10, 10, mode="s")
         .finalize()
         )
    ex = h.extrude(until="next")
    trude = g.extrude(until="next")

    p = ex.union(trude)
    show_object(p)


def c():
    box = (cq.Workplane("XY")
           .box(10, 10, 10)
           .faces(">Z")
           .shell(1)
           )

    h = (box.faces(">Z")
         .sketch()
         .circle(5)
         .rect(1, 10, mode="s")
         .rect(4, 1, mode="s")
         .finalize()
         )

    g = (box.faces(">Z")
         .sketch()
         .circle(5)
         .rect(1, 4, mode="s")
         .rect(10, 1, mode="s")
         .finalize()
         )
    ex = h.extrude(until="next")
    trude = g.extrude(until="next")

    p = ex.union(trude)
    show_object(p)


c()
