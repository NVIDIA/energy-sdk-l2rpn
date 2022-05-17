import ipywidgets as ipw
import ipyvuetify as v
import time
import traitlets as tr

import numpy as np
import grid2op

from .common import load_template, rho2color, dict2pretty_string
from .actionrecommender import ActionRecommender
from .plotscomponent import PlotsComponent


class GridControl(v.VuetifyTemplate):
    template = tr.Unicode(load_template("vue-templates/grid-control.vue")).tag(
        sync=True
    )
    date = tr.Unicode(f"{time.ctime(time.time())}").tag(sync=True)
    steps = tr.Unicode("").tag(sync=True)
    maxrho = tr.Unicode(f"{.65132*100:.1f}%").tag(sync=True)
    maxrho_color = tr.Unicode("black").tag(sync=True)

    steps2attempt = tr.Unicode("0").tag(sync=True)
    scenario = tr.Unicode("scenario").tag(sync=True)
    step_progress = tr.Int(0).tag(sync=True)
    animated_lines = tr.Bool(False).tag(sync=True)
    animation_loading = tr.Bool(False).tag(sync=True)

    nsubs = tr.Int(0).tag(sync=True)
    nlines = tr.Int(0).tag(sync=True)

    selected_gen = tr.Dict(
        {"gid": 0, "redispatchable": True, "maxup": 1, "maxdown": -1, "info": ""}
    ).tag(sync=True)

    disconnected_lines = tr.List([{"lid": 1, "cdt": 0}, {"lid": 10, "cdt": 3}]).tag(
        sync=True
    )
    selected_lines = tr.List([{"lid": 1}, {"lid": 10}]).tag(sync=True)

    logs = tr.List([]).tag(sync=True)
    show_nlogs = tr.Int(1).tag(sync=True)

    environments = tr.List(
        [{"text": e, "value": e} for e in grid2op.list_available_local_env()]
        + [
            {"text": e + " [remote]", "value": e}
            for e in grid2op.list_available_remote_env()
        ]
    ).tag(sync=True)
    env_name = tr.Unicode("").tag(sync=True)
    env_loading = tr.Bool(False).tag(sync=True)

    def select_gen(self, gid):
        obs = self.gm.env.get_obs()
        lid = gid
        self.selected_gen = {
            "gid": gid,
            "redispatchable": bool(obs.gen_redispatchable[gid]),
            "maxup": int(100 * obs.gen_max_ramp_up[gid]),
            "maxdown": int(100 * obs.gen_max_ramp_down[gid]),
            "info": f"Gen {lid} - {obs.gen_type[lid]} | P={obs.gen_p[lid]:.1f} ≤ {obs.gen_pmax[lid]:.1f}  | Q={obs.gen_q[lid]:.1f}",
        }

    def _mk_redispatch_act(self, gid, amnt):
        with self.app.output:
            env = self.gm.env
            act = env.action_space()
            act.redispatch = (int(gid), float(amnt))

            print(act)
        return act

    def vue_redispatch(self, data):
        with self.app.output:
            gid, amnt = data
            action = self._mk_redispatch_act(gid, amnt)
            self.take_action(action)

    def vue_reconnect_line(self, lid):
        self.reconnect_line(lid)

    def vue_sim_disconnect_line(self, lid):
        self.sim_disconnect_line(lid)

    def vue_disconnect_line(self, lid):
        self.disconnect_line(lid)

    def vue_unhighlight_elements(self, data):
        self.gm.unhighlight_elements()

    def vue_highlight_elements(self, els):
        with self.app.output:
            self.gm.highlight_elements(els)

    def vue_load_env(self, data):
        self.env_loading = True
        try:
            with self.app.output:
                if self.env_name not in grid2op.list_available_local_env():
                    self.app.output_dialog = True
                print(f"Loading environment [{self.env_name}] ")
                t0 = time.time()
                self.gm.load_env(self.env_name)
                self.init_game()

                self.nlines = len(self.gm.lid2locs)
                self.nsubs = len(self.gm.sub2pos)
                print(f"Loaded environment [{self.env_name}] in {time.time()-t0:.1f} s")
        finally:
            self.env_loading = False

    def vue_restart(self, data):
        self.init_game()

    def vue_attempt_nsteps(self, data):
        self.step(int(self.steps2attempt))
        self.animated_lines = False
        self.gm.animate_lines = self.animated_lines

    def vue_animate_lines(self, data):
        self.animation_loading = True
        self.animated_lines = not self.animated_lines
        self.gm.animate_lines = self.animated_lines
        self.animation_loading = False

    def vue_center_map(self, data):
        self.gm.center_map()

    def __init__(self, gridmap, *ag, app=None, **kargs):
        super().__init__(*ag, **kargs)
        self.app = app

        self.gm = gridmap
        self.pc = PlotsComponent(self, app=self.app)

        def osl(a):
            if self.gm.selected_line >= 0:
                self.selected_lines = [{"lid": self.gm.selected_line, "info": ""}]

        self.gm.observe(osl, "selected_line")

        def osg(a):
            with self.app.output:
                if self.gm.selected_gen >= 0:
                    self.select_gen(self.gm.selected_gen)

        self.gm.observe(osg, "selected_gen")

        self.ar = ActionRecommender(self, app=self.app)
        self.components = {"action-recommender": self.ar, "plots-control": self.pc}

        self.init_game()

    def _update_info(self, done=False):
        with self.app.output:
            self.logs = [dict2pretty_string(log) for log in self.rets[-10:]]
            minperstep = 5
            days = self.nsteps * minperstep / 60 / 24
            self.steps = f"{self.nsteps:,} steps [{days:.1f} days]"
            if done:
                self.steps = "Success!!! " + self.steps
            obs = self.gm.env.get_obs()
            rho = obs.rho.max()
            self.maxrho = f"{rho*100:.1f}%"
            self.maxrho_color = rho2color(rho)

            self.date = str(np.datetime64(self.gm.env.time_stamp, "m"))
            self.scenario = self.gm.env.chronics_handler.get_name()

            self.update_disconnected_lines(obs=obs)
            self.ar.update()

            self.pc.update()

    def reconnect_line(self, lid):
        with self.app.output:
            obs = self.gm.env.get_obs()
            connected = obs.line_status[lid]
            cdt = obs.time_before_cooldown_line[lid]
            if not connected and cdt == 0:
                a = self.gm.env.action_space()
                a.line_set_status = [(lid, 1)]
                self.take_action(a)

    def disconnect_line(self, lid):
        with self.app.output:
            obs = self.gm.env.get_obs()
            connected = obs.line_status[lid]
            cdt = obs.time_before_cooldown_line[lid]
            if connected and cdt == 0:
                a = self.gm.env.action_space()
                a.line_set_status = [(lid, -1)]
                self.take_action(a)

    def sim_disconnect_line(self, lid):
        with self.app.output:
            obs = self.gm.env.get_obs()
            connected = obs.line_status[lid]
            cdt = obs.time_before_cooldown_line[lid]
            if connected and cdt == 0:
                a = self.gm.env.action_space()
                a.line_set_status = [(lid, -1)]
                sobs, reward, done, info = obs.simulate(a)
                s = f"ρ={sobs.rho.max()*100:.1f}%\n" + str(info)
                maxrho = f"ρ={sobs.rho.max()*100:.1f}%"
                d = {
                    "maxrho": maxrho,
                    "step-id": self.nsteps,
                    "done": done,
                    "reward": reward,
                    "info": info,
                }
                self.selected_lines = [{"lid": lid, "info": dict2pretty_string(d)}]

    def update_disconnected_lines(self, obs=None):
        if obs is None:
            obs = self.env.get_obs()

        l = []
        for lid, connected in enumerate(obs.line_status):
            cdt = obs.time_before_cooldown_line[lid]
            if not connected:
                e = {"lid": lid, "cdt": cdt}
                l += [e]
        self.disconnected_lines = l

    def init_game(self):
        if hasattr(self.gm, "env"):
            self.nsteps = 0
            self.gm.env.reset()
            self._update_info()

            self.animated_lines = False
            self.animation_loading = False
            self.gm.animate_lines = self.animated_lines
            self.selected_lines = []

            self.gm.reset()

            self.ar.reset()
        self.rets = []
        self.steps_data = []

    def _make_step(self, action):
        ret = self.gm.env.step(action)
        self.nsteps += 1

        obs, reward, done, info = ret
        maxrho = f"ρ={obs.rho.max()*100:.1f}%"
        d = {
            "maxrho": maxrho,
            "step-id": self.nsteps,
            "done": done,
            "reward": reward,
            "info": info,
        }
        self.rets += [d]

        datum = {
            "ts": np.datetime64(self.gm.env.time_stamp),
            "rho": obs.rho.copy(),
            "gen_p": obs.gen_p,
            "load_p": obs.load_p,
        }
        self.steps_data += [datum]
        return ret

    def take_action(self, action):
        self._make_step(action)
        self._update_info()
        self.gm.reset(update_icons=False)

    def step(self, nsteps=1):
        self.step_progress = 0
        obs = self.gm.env.get_obs()
        ndisconnected = sum(obs.line_status == False)
        for stepi in range(nsteps):
            a = self.gm.env.action_space({})
            obs, reward, done, info = self._make_step(a)

            self.step_progress = int(((stepi + 1) / nsteps) * 100)

            if (
                obs.rho.max() > 1
                or done
                or ndisconnected < sum(obs.line_status == False)
            ):
                break
        self._update_info(done=done)
        self.gm.reset(update_icons=False)
