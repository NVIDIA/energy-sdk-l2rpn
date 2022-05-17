import ipywidgets as ipw
import ipyvuetify as v
import time
import traitlets as tr
import numpy as np

from .common import load_template, rho2color, AllTopoActions

import heapq


def list_els_from_action(a):
    topo = a.impact_on_objects()["topology"]["bus_switch"]
    subs = set()
    gens = set()
    loads = set()
    lines = set()
    for ev in topo:
        subs.add(ev["substation"])
        if "gener" in ev["object_type"]:
            gens.add(ev["object_id"])
        if "load" in ev["object_type"]:
            loads.add(ev["object_id"])
        if "line" in ev["object_type"]:
            lines.add(ev["object_id"])

    return subs, gens, loads, lines


class ActionRecommender(v.VuetifyTemplate):
    template = tr.Unicode(load_template("vue-templates/action-recommender.vue")).tag(
        sync=True
    )
    nactions = tr.Int(0).tag(sync=True)
    act_search_status = tr.Unicode("").tag(sync=True)
    recommended_acts = tr.List(
        [
            {"aid": 1, "rho": "54.2%", "color": "green", "info": "lots of text here"},
            {"aid": 10, "rho": "154.2%", "color": "red", "info": "lots more text here"},
        ]
    ).tag(sync=True)
    randomize = tr.Bool(False).tag(sync=True)
    hot_subs = tr.List([]).tag(sync=True)

    def __init__(self, gridcontrol, *ag, app=None, **kargs):
        super().__init__(*ag, **kargs)

        self.gc = gridcontrol
        self.gm = gridcontrol.gm
        self.app = app

    def reset(self):
        self.nactions = 0
        self.alltopoactions = None
        self.recommended_acts = []

    def update(self):
        obs = self.gm.env.get_obs()

        self.hot_subs = [
            (subid, cdt)
            for subid, cdt in enumerate(obs.time_before_cooldown_sub)
            if cdt > 0
        ]

    def vue_unhighlight_elements(self, data):
        self.gm.unhighlight_elements()

    def vue_highlight_elements(self, aid):
        with self.app.output:
            action = self.alltopoactions.get_action(aid)
            subs, gens, loads, lines = list_els_from_action(action)

            self.gm.highlight_elements(
                {"subs": subs, "lines": lines, "gens": gens, "loads": loads}
            )

    def vue_take_action(self, aid):
        with self.app.output:
            print("taking action")
        action = self.alltopoactions.get_action(aid)
        self.gc.take_action(action)

    def vue_search_actions(self, perc):
        with self.app.output:
            if self.alltopoactions is None:
                self.act_search_status = "Calculating all possible actions..."
                env = self.gm.env
                self.alltopoactions = AllTopoActions(env)
                # self.actions = env.action_space.get_all_unitary_topologies_change(
                #     env.action_space
                # )
                self.nactions = self.alltopoactions.nactions
                self.act_search_status = (
                    f"Calculating all possible actions... {self.nactions:,}"
                )

            perc = int(perc)
            env = self.gm.env
            obs = self.gm.env.get_obs()
            # allacts = [(aid, a) for aid, a in enumerate(self.actions)]
            allacts = self.alltopoactions.get_actions()
            if self.randomize:
                np.random.shuffle(allacts)
            acts = allacts[: int(self.nactions * (perc / 100))]
            print("nacts all", len(allacts))
            nacts = len(acts)
            prefix = f"Searching among {nacts} actions... "
            self.act_search_status = prefix

            current_rho = obs.rho.max()
            selected_acts = []
            self.recommended_acts = []
            t0 = time.time()
            for ai, (actid, act) in enumerate(acts):
                if not env._game_rules(act, env):
                    continue
                sobs, reward, done, info = obs.simulate(act)
                rho = sobs.rho.max()

                if not done and rho < current_rho:
                    item = (rho, actid, act)
                    heapq.heappush(selected_acts, item)
                    selected_acts = heapq.nsmallest(3, selected_acts)

                    l = []
                    for mrho, aid, action in selected_acts:
                        l += [
                            {
                                "aid": aid,
                                "rho": f"{mrho*100:.1f}%",
                                "color": rho2color(mrho),
                                "info": str(action),
                            }
                        ]
                    self.recommended_acts = l
                if ai % 50 == 0:
                    itspersec = (ai + 1) / (time.time() - t0)
                    self.act_search_status = (
                        prefix + f"{ai+1} of {nacts} [{itspersec:,.1f} acts/s]"
                    )
            self.act_search_status = (
                prefix + f"{ai+1} of {nacts} [{itspersec:,.1f} acts/s]"
            )
