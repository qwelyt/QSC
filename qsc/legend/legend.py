import cadquery as cq
from qsc.legend.legend_settings import LegendSettings


class Legend(object):
    _settings: LegendSettings = None

    def __init__(self, settings: LegendSettings):
        self._settings = settings

    def apply_legend(self, cap, base):
        if self._settings is None or self._settings.get_legend() is None:
            return cap, None
        placement = (base.faces(self._settings.get_side())
                     .workplane(offset=-self._settings.get_distance(), centerOption="CenterOfMass")
                     .center(self._settings.get_x_pos(), self._settings.get_y_pos())
                     )
        nc = cq.Workplane().add(cap).copyWorkplane(placement)
        nw = cq.Workplane().add(cap).copyWorkplane(nc)
        c = nc.text(txt=self._settings.get_legend(),
                    fontsize=self._settings.get_font_size(),
                    distance=self._settings.get_distance(),
                    font=self._settings.get_font(),
                    halign=self._settings.get_h_align(),
                    valign=self._settings.get_v_align(),
                    combine="cut"
                    )
        t = nw.text(txt=self._settings.get_legend(),
                    fontsize=self._settings.get_font_size(),
                    distance=self._settings.get_distance(),
                    font=self._settings.get_font_or_path(),
                    halign=self._settings.get_h_align(),
                    valign=self._settings.get_v_align(),
                    combine='a',
                    cut=False
                    )
        return c, t
