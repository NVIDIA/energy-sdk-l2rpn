import ipywidgets as ipw
import ipyvuetify as v
import time
import traitlets as tr

import ipyleaflet as ipl

from .common import load_template
from .gridmap import GridMap
from .gridcontrol import GridControl


class App(v.VuetifyTemplate):
    template = tr.Unicode(load_template("vue-templates/app.vue")).tag(sync=True)
    wsz = tr.Dict({}).tag(sync=True)
    output_dialog = tr.Bool(False).tag(sync=True)

    def __init__(self, output, *ag, **kargs):
        super().__init__(*ag, **kargs)

        self.output = output

        self.gm = ipw.HTML("GridMap")
        self.gm = GridMap(app=self)
        self.gc = GridControl(self.gm, app=self)

        self.lc_box = ipw.VBox([self.gm])
        self.rc_box = ipw.VBox([self.gc])
        self.components = {
            "left-card": self.lc_box,
            "right-card": self.rc_box,
            "app-output": self.output,
        }

    def vue_clear_output(self, key):
        self.output.clear_output()


def new(output=None):
    """Creates a new app"""

    return App(output)
