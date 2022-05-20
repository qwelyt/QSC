from __future__ import annotations
from Constants import Constants


class MM(object):
    _mm = 0

    def __init__(self, mm: float):
        self._mm = mm

    def __str__(self):
        return str(self._mm) + "mm"

    def __repr__(self):
        return f'MM(mm={self._mm})'

    def u(self) -> U:
        from U import U
        return U(self._mm / Constants.U_IN_MM)

    def mm(self) -> MM:
        return self

    def get(self) -> float:
        return self._mm
