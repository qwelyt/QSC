from abc import ABC, abstractmethod
from typing import TypeVar, Tuple

from ..MM import MM
from ..types import Real

from .StemType import StemType

T = TypeVar("T", bound="Settings")


class StemSettings(ABC):
    _offset = (0, 0, 0)
    _rotation = 0
    _support = True
    _vslop: MM = MM(0)
    _hslop: MM = MM(0)

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, "type")
                and hasattr(subclass, "get_type")
                )

    def __repr__(self):
        return f'.offset(offset={self._offset})' \
               f'.rotation(rotation={self._rotation})' \
               f'.disable_support(support={not self._support})' \
               f'.vslop(slop=MM({self._vslop.get()}))' \
               f'.hslop(slop=MM({self._hslop.get()}))'

    def offset(self, offset: Tuple[Real, Real, Real]) -> T:
        self._offset = offset
        return self

    def rotation(self, rotation: Real) -> T:
        self._rotation = rotation
        return self

    def disable_support(self, support: bool = True) -> T:
        self._support = not support
        return self

    def vslop(self: T, slop: MM) -> T:
        self._vslop = slop
        return self

    def hslop(self: T, slop: MM) -> T:
        self._hslop = slop
        return self

    @abstractmethod
    def get_type(self) -> StemType:
        pass

    def get_offset(self) -> Tuple[Real, Real, Real]:
        return self._offset

    def get_rotation(self) -> Real:
        return self._rotation

    def get_support(self) -> bool:
        return self._support

    def get_vslop(self) -> Real:
        return self._vslop.get()

    def get_hslop(self) -> Real:
        return self._hslop.get()
