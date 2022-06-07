from typing import TypeVar
from qsc.types import Real

T = TypeVar("T", bound="Legend")


class LegendSettings(object):
    _font = "Arial"
    _fontSize = 6
    _fontPath = None
    _xPos = 0
    _yPos = 0
    _legend = None
    _side = None
    _distance = None
    _vAlign = "center"
    _hAlign = "center"

    def __init__(self):
        pass

    def font(self, font: str) -> T:
        self._font = font
        return self

    def font_size(self, size: int) -> T:
        self._fontSize = size
        return self

    def font_path(self, path: str) -> T:
        self._fontPath = path
        return self

    def x_pos(self, x: Real) -> T:
        self._xPos = x
        return self

    def y_pos(self, y: Real) -> T:
        self._yPos = y
        return self

    def legend(self, legend: str) -> T:
        self._legend = legend
        return self

    def side(self, side: str) -> T:
        self._side = side
        return self

    def distance(self, distance: Real) -> T:
        self._distance = distance
        return self

    def v_align(self, v: str) -> T:
        self._vAlign = v
        return self

    def h_align(self, h: str) -> T:
        self._hAlign = h
        return self

    def get_font(self) -> str:
        return self._font

    def get_font_size(self) -> int:
        return self._fontSize

    def get_font_path(self) -> str:
        return self._fontPath

    def get_x_pos(self) -> Real:
        return self._xPos

    def get_y_pos(self) -> Real:
        return self._yPos

    def get_legend(self) -> str:
        return self._legend

    def get_side(self) -> str:
        return self._side

    def get_distance(self) -> Real:
        return self._distance

    def get_v_align(self) -> str:
        return self._vAlign

    def get_h_align(self) -> str:
        return self._hAlign

    def get_font_or_path(self) -> str:
        if self._fontPath is None:
            return self._font
        else:
            return self._fontPath
