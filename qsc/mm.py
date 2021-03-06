from __future__ import annotations

from qsc.types import Real
from qsc.constants import Constants


class MM(object):
    _mm: Real = 0

    def __init__(self, mm: Real):
        self._mm = mm

    def __str__(self):
        return str(self._mm) + "mm"

    def __repr__(self):
        return f'MM(mm={self._mm})'

    def u(self) -> U:
        from u import U
        return U(self._mm / Constants.U_IN_MM)

    def mm(self) -> MM:
        return self

    def get(self) -> Real:
        return self._mm
