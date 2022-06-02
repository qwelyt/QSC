from cadquery import Workplane, BoundBox
from qsc.homing_type import HomingType


class Homing(object):
    _variant = None

    def __init__(self, variant: HomingType):
        self._variant = variant

    def add(self, cap: Workplane) -> Workplane:
        print("pap", self._variant)
        if self._variant is None or self._variant == HomingType.SCOOPED:
            return cap

        capBB = cap.findSolid().BoundingBox()

        length = capBB.ylen / 2 if self._variant == HomingType.BAR else 1
        print(capBB.ylen, length)
        placer = (Workplane()
                  # .sketch()
                  .rect(0.1, length)
                  # .finalize()
                  .extrude(capBB.zlen)
                  )
        intersection = cap.intersect(placer)
        intersectionBB = intersection.faces("<Y").val().BoundingBox()

        if self._variant == HomingType.BAR:
            return self._bar(cap, intersectionBB)
        elif self._variant == HomingType.DOT:
            return self._dot(cap, intersectionBB)

        return cap

    def _bar(self, cap: Workplane, bb: BoundBox) -> Workplane:
        print("poop")
        bar_size = 1
        bar = (Workplane("XY")
               .sketch()
               .rect(cap.findSolid().BoundingBox().xlen / 3, bar_size)
               .vertices()
               .fillet(bar_size / 2)
               .finalize()
               .extrude(1)
               .faces(">Z")
               .fillet(bar_size / 2)
               )
        b = bar.translate((0, bb.ymin, bb.zlen - bar_size / 1.5))
        return cap.add(b)

    def _dot(self, cap: Workplane, bb: BoundBox) -> Workplane:
        dot_size = 1
        dot = (Workplane()
               .sphere(dot_size)
               .translate((0, bb.ymin, bb.zlen - dot_size / 2))
               )
        return cap.union(dot)
