import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


import ipywidgets as ipw
import ipyvuetify as v
import traitlets as tr

from .common import load_template

import matplotlib

# matplotlib.use("WebAgg")


class PlotsComponent(v.VuetifyTemplate):
    template = tr.Unicode(load_template("vue-templates/plots-component.vue")).tag(
        sync=True
    )
    gby = tr.Unicode("").tag(sync=True)
    showfig = tr.Bool(True).tag(sync=True)

    def __init__(self, gridcontrol, *ag, app=None, **kargs):
        super().__init__(*ag, **kargs)
        self.app = app

        self.gc = gridcontrol

        self.outputwidget = ipw.Output()
        with self.outputwidget:
            plt.close("all")
            f = plt.figure(figsize=(5, 3))
            self.figure = f
            self.ax = plt.gca()

        self.components = {"plt-figure": self.outputwidget}
        self.gby = "all"

    def vue_set_plot_gby(self, gby):
        with self.app.output:
            self.gby = gby
            self.update()

    def vue_update_plot(self, data):
        self.update()

    def update(self):
        with self.app.output:
            self.gc.steps_data
            ts = [e["ts"] for e in self.gc.steps_data]
            maxrhos = [e["rho"].max() * 100 for e in self.gc.steps_data]

            env = self.gc.gm.env
            gent = {gt: [] for gt in env.gen_type}
            for e in self.gc.steps_data:
                d = {}
                for gt, gv in zip(env.gen_type, e["gen_p"]):
                    if gt not in d:
                        d[gt] = 0
                    d[gt] += gv
                for gt, gv in d.items():
                    gent[gt] += [gv]

            gen_p = [e["gen_p"].sum() for e in self.gc.steps_data]
            load_p = [e["load_p"].sum() for e in self.gc.steps_data]

            plt.clf()
            plt.subplot(2, 1, 1)
            df = pd.DataFrame({"max(ρ)": maxrhos}, index=ts)
            df.plot(ax=plt.gca(), style=".-")
            plt.ylabel("max(ρ) (%)")
            legend = plt.legend("off")
            legend.remove()

            plt.axhline(100, lw=1, color="red")
            plt.axhline(0, lw=1, color="black")

            plt.subplot(2, 1, 2)

            gby = self.gby
            if gby == "all":
                df = pd.DataFrame({"gen_p": gen_p, "load_p": load_p}, index=ts)
                df.plot(ax=plt.gca())
                plt.ylabel("P MW")
            if gby == "gen type":
                dfg = pd.DataFrame(gent, index=ts)
                ax = plt.gca()
                dfg.plot.area(ax=ax, stacked=True)
                plt.ylabel("P MW")
                plt.legend(
                    ncol=5,
                    loc="lower center",
                    fontsize="small",
                    bbox_to_anchor=(0.5, 1),
                )
                plt.title(" ")
            if gby == "gen type (100%)":
                dfg = pd.DataFrame(gent, index=ts)
                ax = plt.gca()
                dfg.apply(lambda x: x * 100 / sum(x), axis=1).plot.area(
                    ax=ax, stacked=True
                )
                plt.ylabel("%")
                plt.legend(
                    ncol=5,
                    loc="lower center",
                    fontsize="small",
                    bbox_to_anchor=(0.5, 1.0),
                )
                plt.title(" ")

            plt.tight_layout()
