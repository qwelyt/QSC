import cadquery as cq
from typing import TypeVar, List
from qsc.stem.stem_settings import StemSettings
from qsc.stem.cherry_settings import CherrySettings
from qsc.stem.stem_type import StemType

T = TypeVar("T", bound="Support")


class Support(object):
    _settings: StemSettings = None
    _positions: List = [(0, 0, 0)]

    def __init__(self, settings: StemSettings):
        self._settings = settings

    def positions(self, positions: List) -> T:
        self._positions = positions
        return self

    def build(self, cap: cq.Workplane) -> cq.Workplane:
        if not self._settings.get_support():
            return cap

        match self._settings.get_type():
            case StemType.CHERRY:
                return self._cherry(cap, self._settings, self._positions)

        return cap

    def _cherry(self, cap: cq.Workplane, settings: CherrySettings, positions: List):
        def support(cap, delta, push_value, position, rotation):
            x = position[0]
            y = position[1] * -1
            v = {
                0: {
                    "mv": (x, push_value + y),
                    "rect": (1, delta),
                    "face": "<Y",
                    "bblen": lambda bb: bb.xlen,
                },
                90: {
                    "mv": (push_value + x, y),
                    "rect": (delta, 1),
                    "face": ">X",
                    "bblen": lambda bb: bb.ylen,
                },
                180: {
                    "mv": (x, -push_value + y),
                    "rect": (1, delta),
                    "face": ">Y",
                    "bblen": lambda bb: bb.xlen,
                },
                270: {
                    "mv": (-push_value + x, y),
                    "rect": (delta, 1),
                    "face": "<X",
                    "bblen": lambda bb: bb.ylen,
                },
            }.get(rotation)

            pillar = (cap.faces("<Z")
                      .workplane()
                      .sketch()
                      .push([v.get("mv")])  # Changes on rotation
                      .rect(v.get("rect")[0], v.get("rect")[1])  # Changes on rotation
                      .finalize()
                      .extrude(until="next") - cap
                      )

            face = (pillar
                    .faces(v.get("face"))  # Changes on rotation
                    .workplane(centerOption="CenterOfMass")
                    )
            pBB = face.findSolid().BoundingBox()
            return (cq.Workplane()
                    .add(cap)
                    .copyWorkplane(face)
                    .sketch()
                    .push([(0, -delta / 2)])
                    .rect(v.get("bblen")(pBB), pBB.zlen - delta)
                    .finalize()
                    .extrude(until="next")
                    )

        delta = 0.15
        push_value = settings.get_radius() + delta
        wp = cq.Workplane()
        for pos in positions:
            wp.add(support(cap, delta, push_value, pos, settings.get_rotation()))
        return cap.union(wp.combine())
