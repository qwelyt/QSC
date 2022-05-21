from qsc import (
    Constants,
    HomingType,
    MM,
    Percentage,
    QSC,
    StemType,
    StepType,
    U,
)


def show(cap: QSC, rotate=False):
    c = cap.build()
    if rotate:
        show_object(cap._rotate(c[0]), options={"color": (200, 20, 100)})
        if cap._legend is not None:
            show_object(cap._rotate(c[1]), options={"color": (90, 200, 40)})
    else:
        show_object(c[0], options={"color": (200, 20, 100)})
        if cap._legend is not None:
            show_object(c[1], options={"color": (90, 200, 40)})


cap = (QSC()
       .row(3)
       .width(U(3))
       .legend("Hi", fontSize=6)
       .inverted()
       .homing(HomingType.BAR)
       )

show(cap)
