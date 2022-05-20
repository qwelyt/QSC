from __future__ import annotations
from Constants import Constants


class U(object):
    _u = 0

    def __init__(self, u):
        self._u = u

    def __str__(self):
        return str(self._u)+"u"

    def __repr__(self):
        return f'U(u={self._u})'

    def u(self) -> U:
        return self

    def mm(self) -> MM:
        from MM import MM
        return MM(self._u * Constants.U_IN_MM)

    def get(self) -> float:
        return self._u
