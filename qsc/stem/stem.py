from cadquery import Sketch

from qsc.stem.stem_settings import StemSettings
from qsc.stem.cherry_settings import CherrySettings
from qsc.stem.stem_type import StemType


class Stem(object):
    _settings = None

    def __init__(self, settings: StemSettings):
        self._settings = settings

    def build(self) -> Sketch:
        type = self._settings.get_type()
        if type == StemType.CHERRY:
            return self._cherry_stem(self._settings)
        else:
            return Sketch().rect(10, 10)

    @staticmethod
    def _cherry_stem(settings: CherrySettings) -> Sketch:
        cross = (1.5 + settings.get_hslop(), 4.2 + settings.get_vslop())
        return (Sketch()
                .circle(settings.get_radius())
                .rect(cross[0], cross[1], mode="s")
                .rect(cross[1], cross[0], mode="s")
                )
