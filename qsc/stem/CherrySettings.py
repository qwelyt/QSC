from typing import TypeVar

from .StemSettings import StemSettings
from .StemType import StemType
from ..MM import MM
from ..types import Real

T = TypeVar("T", bound="CherrySettings")


class CherrySettings(StemSettings):
    _type = StemType.CHERRY
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

    def get_type(self):
        return self._type

    def get_radius(self) -> Real:
        return self._radius.get()
