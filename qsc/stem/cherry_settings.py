from typing import TypeVar

from qsc.mm import MM
from qsc.types import Real
from qsc.stem.stem_settings import StemSettings
from qsc.stem.stem_type import StemType

T = TypeVar("T", bound="CherrySettings")


class CherrySettings(StemSettings):
    _radius: MM = MM(5.6 / 2)

    def __init__(self):
        pass

    def __repr__(self):
        return f'CherrySettings().radius(MM({self._radius.get()})' + super().__repr__()

    def diameter(self: T, diameter: MM) -> T:
        self._radius = MM(diameter.get() / 2)
        return self

    def radius(self: T, radius: MM) -> T:
        self._radius = radius
        return self

    def get_type(self) -> StemType:
        return StemType.CHERRY

    def get_radius(self) -> Real:
        return self._radius.get()
