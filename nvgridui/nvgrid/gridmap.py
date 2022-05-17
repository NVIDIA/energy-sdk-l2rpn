import ipywidgets as ipw
import ipyvuetify as v
import time
import traitlets as tr

import ipyleaflet as ipl
import numpy as np

from .common import load_template, rho2color

from grid2op.MakeEnv import make
from lightsim2grid import LightSimBackend as BACKEND

PATH2ICONS = "/nvgrid/assets/"


def rho2delay(rho):
    d = max((900 - 10 * 100 * np.abs(rho)), 50)
    return int(d)


class GridMap(v.VuetifyTemplate):
    template = tr.Unicode(load_template("vue-templates/grid-map.vue")).tag(sync=True)
    wsz = tr.Dict({}).tag(sync=True)
    line_weight = tr.Unicode("3").tag(sync=True)
    animate_lines = tr.Bool(False)
    selected_line = tr.Int(-1).tag(sync=True)
    selected_gen = tr.Int(-1).tag(sync=True)

    def __init__(self, *ag, app=None, **kargs):
        super().__init__(*ag, **kargs)
        self.app = app

        self.lm = ipl.Map(
            layers=[],
            crs=ipl.projections.Simple,
            scroll_wheel_zoom=True,
            zoom_control=False,
            attribution_control=False,
            zoom=2,
        )
        self._lg = ipl.LayerGroup()
        self.lm.add_layer(self._lg)

        self._lg2 = ipl.LayerGroup()
        self.lm.add_layer(self._lg2)

        # self.lm.add_control(ipl.FullScreenControl())
        self.status_html = ipw.HTML("status")
        self.lm.add_control(
            ipl.WidgetControl(widget=self.status_html, position="bottomright")
        )

        self.lm_box = ipw.VBox([self.lm])
        self.components = {"grid-map": self.lm_box}
        self.observe(lambda a: self.on_app_resize(), "wsz")

        def handle_line_anim(a):
            if self.animate_lines:
                self._make_lines_animated()
            else:
                # self._make_lines()
                self.lgs["lines-animated"].layers = []

        self.observe(handle_line_anim, "animate_lines")
        # display config
        # self.animate_lines = False  # True

        # load environment
        # self.load_env()

        # self.reset()

    def unhighlight_elements(self):
        self._lg2.layers = []

    def highlight_elements(self, els):
        features = []
        fc = {"type": "FeatureCollection", "features": features}

        for subid in els.get("subs", []):
            subn = f"sub_{subid}"
            f = self.el2feature["subs"][subn]
            f["properties"]["style"]["weight"] = 5
            features += [f]

        for etype in ["lines", "gens", "loads"]:
            for lid in els.get(etype, []):
                f = self.el2feature[etype][lid]
                f["properties"]["style"]["weight"] = 5
                features += [f]

        gj = ipl.GeoJSON(data=fc)
        self._lg2.layers = [gj]
        pass

    def center_map(self):
        self.lm.center = [0, 0]

    def on_app_resize(self):
        self.lm.layout.height = f"{int(self.wsz['y']-120)}px"
        self.lm_box.children = []
        self.lm_box.children = [self.lm]

    def vue_lc_key(self, key):
        self.lm.center = [10, -60]

    def load_env(self, dataset="l2rpn_icaps_2021_large"):
        self.env = make(dataset, backend=BACKEND())  # make("l2rpn_icaps_2021_large")
        self.obs = self.env.get_obs()

        self.subs = {subn: loc for subn, loc in self.env.grid_layout.items()}

    def reset(self, update_icons=True):
        self._make_elements(update_icons=update_icons)
        self.selected_line = -1

    def redraw(self):
        self._make_lines()

    def _update_lgs(self, key, newlayers):
        # self._lg2.layers = []
        # self._lg2.layers = newlayers
        # time.sleep(0.05)
        self.lgs[key].layers = newlayers

        self._lg2.layers = []

    def _make_elements(self, update_icons=True):
        if update_icons or not hasattr(self, "lgs"):
            self.el2feature = {}
            self.lgs = {
                lgn: ipl.LayerGroup()
                for lgn in ["subs", "lines", "lines-animated", "gens", "loads"]
            }
            self._lg.layers = list(self.lgs.values())

            self.sub2pos = {}

            self._make_subs()
        self._make_lines()
        self._make_gens(update_icons=update_icons)
        self._make_loads(update_icons=update_icons)

    def _deselect_lines(self):
        for pl, ap in self.lid2ap.values():
            pl.weight = 1

    def _select_line(self, lid):
        self._deselect_all()
        pl, ap = self.lid2ap[lid]
        pl.weight = 7

    def _deselect_subs(self):
        for sr in self.subn2rect.values():
            sr.weight = 1

    def _deselect_all(self):
        self._deselect_subs()
        self._deselect_lines()

    def _select_sub(self, subn):
        self._deselect_all()
        sr = self.subn2rect[subn]
        sr.weight = 5

    def _on_hover_sub(self, subn):
        # gen = -1
        # s = f"[{subn}] gen={gen:.1f}Mw"
        # self.status_html.value = s

        obs = self.env.get_obs()
        locs = f"{self.sub2pos[subn]}"

        subid = int(subn.split("_")[1])
        genids = np.where(obs.gen_to_subid == subid)[0]
        gen = np.sum(obs.gen_p[genids]) if len(genids) > 0 else 0

        loadids = np.where(obs.load_to_subid == subid)[0]
        load = np.sum(obs.load_p[loadids]) if len(loadids) > 0 else 0

        s = f"[{subn}] gen={gen:.1f}Mw | load={load:.1f}Mw  | gen-load={gen-load:.1f} Mw"
        self.status_html.value = s
        # self._select_sub(subn)

    def _on_hover_line(self, lid):
        obs = self.env.get_obs()
        rho = obs.rho[lid]
        p_or = obs.p_or[lid]
        q_or = obs.q_or[lid]
        s2s = f" | {obs.line_or_to_subid[lid]}->{obs.line_ex_to_subid[lid]}"
        self.status_html.value = (
            f"PL {lid}: ρ={rho*100:.1f}% | P={p_or:.1f} MW | Q={q_or:.1f} MW" + s2s
        )

        # self._select_line(lid)

    def _on_hover_load(self, lid):
        # gen = -1
        # s = f"[{subn}] gen={gen:.1f}Mw"
        obs = self.env.get_obs()
        self.status_html.value = (
            f"[Load {lid}] P={obs.load_p[lid]:.1f} | Q={obs.load_q[lid]:.1f}"
        )

    def _on_hover_gen(self, lid):
        # gen = -1
        # s = f"[{subn}] gen={gen:.1f}Mw"
        obs = self.env.get_obs()
        self.status_html.value = f"[Gen {lid} - {obs.gen_type[lid]}] P={obs.gen_p[lid]:.1f} ≤ {obs.gen_pmax[lid]:.1f} | max Δ = (-{obs.gen_max_ramp_down[lid]:.1f}, +{obs.gen_max_ramp_up[lid]:.1f}) | Q={obs.gen_q[lid]:.1f} | redispatchable={obs.gen_redispatchable[lid]}"

    def _scale(self, loc, s=0.1):
        return loc[0] * s, loc[1] * s
        # return loc[1] * s, loc[0] * s

    def _make_subs(self):
        scale = self._scale
        # scale = lambda p: self._scale([p[1], p[0]])
        scale = lambda p: (p[1], p[0])
        dx = 15
        bb = 15
        markl = []
        self.subn2rect = {}
        for sn, loc in self.subs.items():
            l1 = loc[0] - dx, loc[1]
            l2 = loc[0] + dx, loc[1]

            self.sub2pos[sn] = {
                -1: loc,
                1: l1,
                2: l2,
            }

        # self.lgs["subs"].layers = [self.make_subs_fc(self.sub2pos)]
        self._deselect_subs()
        newlayers = [self.make_subs_fc(self.sub2pos)]
        self._update_lgs("subs", newlayers)

    def make_subs_fc(self, sub2pos):

        if "subs" not in self.el2feature:
            self.el2feature["subs"] = {}

        scale = self._scale
        # scale = lambda p: (p[1], p[0])
        obs = self.env.get_obs()
        rhos = obs.rho
        features = []
        fc = {"type": "FeatureCollection", "features": features}

        for lid, pos in sub2pos.items():
            bb = 15
            l1, l2 = pos[1], pos[2]
            locs = [
                scale([l1[0] - bb, l1[1] - bb]),
                scale([l1[0] - bb, l2[1] + bb]),
                scale([l2[0] + bb, l2[1] + bb]),
                scale([l2[0] + bb, l1[1] - bb]),
                scale([l1[0] - bb, l1[1] - bb]),
            ]
            f = make_polygon_feature(locs, fid=lid)
            features += [f]
            self.el2feature["subs"][lid] = f
            for p in [pos[1], pos[2]]:
                f = {
                    "type": "Feature",
                    "properties": {
                        "ftype": "sub",
                        "fid": lid,
                        "style": {"weight": 10},
                    },
                }

                f["geometry"] = {
                    "type": "LineString",
                    "coordinates": [
                        scale(p),
                        scale(p),
                    ],
                }
                features += [f]

        hover_style = {"weight": 5}

        def oh(**a):
            props = a["feature"]["properties"]
            lid = props["fid"]
            self._on_hover_sub(lid)

        gj = ipl.GeoJSON(data=fc, hover_style=hover_style)
        gj.on_hover(oh)
        return gj

    def _is_line_disconnected(self, lid):
        obs = self.env.get_obs()
        return not obs.line_status[lid]

    def lm_bounds(self):
        arr = []
        for locs in self.lid2locs.values():
            arr += locs
        arr = np.array(arr)

        mn = np.min(arr[:, 0]), np.min(arr[:, 1])
        mx = np.max(arr[:, 0]), np.max(arr[:, 1])
        return [mn, mx]

    def center_map(self):
        lm = self.lm
        lm.center = [0, 0]
        lmb = lm.bounds
        gb = self.lm_bounds()
        # if all(np.array(lmb[0])<np.array(gb[0])) and all(np.array(lmb[1])>np.array(gb[1])):
        #     lm.zoom += 1
        gx = max(np.abs(gb[0][0]), np.abs(gb[1][0]))
        lmx = max(np.abs(lmb[0][0]), np.abs(lmb[1][0]))
        xzoom = np.round(np.log(lmx / gx) / np.log(2))

        gx = max(np.abs(gb[0][1]), np.abs(gb[1][1]))
        lmx = max(np.abs(lmb[0][1]), np.abs(lmb[1][1]))
        yzoom = np.round(np.log(lmx / gx) / np.log(2))
        lm.zoom += min(xzoom, yzoom)

    def _make_lines(self):
        obs = self.env.get_obs()
        sub2pos = self.sub2pos
        scale = self._scale  # lambda p: self._scale([p[1], p[0]])
        # scale = lambda p: (p[1], p[0])
        lid2ap = {}

        locs2ap = {}
        for lid, (sor, sex) in enumerate(
            zip(obs.line_or_to_subid, obs.line_ex_to_subid)
        ):
            exb = obs.line_ex_bus[lid]
            orb = obs.line_or_bus[lid]

            locs = (
                scale(sub2pos[f"sub_{sor}"][orb]),
                scale(sub2pos[f"sub_{sex}"][exb]),
            )

            if locs not in locs2ap:
                locs2ap[locs] = []
            locs2ap[locs] += [lid]

        # fix geometry of lines that run parallel to one another
        lid2locs = {}
        for locs, aps in locs2ap.items():
            if len(aps) == 2:
                p1, p2 = locs
                p1, p2 = np.array(p1), np.array(p2)

                tvec = p1 - p2
                nvec = np.array([tvec[1], -tvec[0]])
                nvec = nvec / np.linalg.norm(nvec)

                sign = 1
                for lid in aps:
                    sign = -sign
                    pm = p2 + tvec / 2 + sign * nvec
                    lid2locs[lid] = np.array([p1, pm, p2]).tolist()

            else:
                for lid in aps:
                    lid2locs[lid] = locs

        # finally, update the layer
        # make GeoJSON layer
        self.lid2ap = {}
        self.lid2locs = lid2locs

        # self.lgs["lines"].layers = [self.make_lines_fc(lid2locs)]
        self._update_lgs("lines", [self.make_lines_fc(lid2locs)])

    def make_lines_fc(self, lid2locs):
        if "lines" not in self.el2feature:
            self.el2feature["lines"] = {}

        obs = self.env.get_obs()
        rhos = obs.rho
        features = []
        fc = {"type": "FeatureCollection", "features": features}

        for lid, locs in lid2locs.items():
            f = {
                "type": "Feature",
                "properties": {
                    "ftype": "line",
                    "fid": lid,
                    "style": {"color": rho2color(rhos[lid]), "weight": 3},
                },
            }
            f["geometry"] = {"type": "LineString", "coordinates": locs}
            if self._is_line_disconnected(lid):
                f["properties"]["style"]["dashArray"] = "5"
                f["properties"]["style"]["color"] = "black"
            features += [f]

            self.el2feature["lines"][lid] = f

        hover_style = {"weight": 7}

        def oh(**a):
            props = a["feature"]["properties"]
            lid = props["fid"]
            self._on_hover_line(lid)

        def oc(**a):
            with self.app.output:
                if a["event"] == "click":
                    self.selected_line = a["feature"]["properties"]["fid"]

        gj = ipl.GeoJSON(data=fc, hover_style=hover_style)
        gj.on_hover(oh)
        gj.on_click(oc)
        return gj

    def _make_lines_animated(self):
        obs = self.env.get_obs()
        sub2pos = self.sub2pos
        scale = lambda p: self._scale([p[1], p[0]])

        lid2ap = {}
        self.lid2ap = lid2ap

        rhos = obs.rho

        locs2ap = {}
        for lid, (sor, sex) in enumerate(
            zip(obs.line_or_to_subid, obs.line_ex_to_subid)
        ):
            if self._is_line_disconnected(lid):
                continue
            exb = obs.line_ex_bus[lid]
            orb = obs.line_or_bus[lid]
            locs = [
                scale(sub2pos[f"sub_{sor}"][orb]),
                scale(sub2pos[f"sub_{sex}"][exb]),
            ]
            if obs.p_or[lid] < 0:
                locs = list(reversed(locs))
            with self.app.output:
                ap = ipl.AntPath(
                    locations=locs,  # if  else reversed(locs),
                    delay=rho2delay(rhos[lid]),
                    paused=(not self.animate_lines)
                    or bool(np.round(obs.p_or[lid] * 100) == 0),
                    weight=int(self.line_weight),
                    color=rho2color(obs.rho[lid]),
                )
            pl = ipl.Polyline(locations=locs, weight=1, fill=False)
            lid2ap[lid] = (pl, ap)
            locsk = str(locs)
            if locsk not in locs2ap:
                locs2ap[locsk] = []
            locs2ap[locsk] += [(pl, ap)]

            def mkomo(lid):
                def omo(**a):
                    self._on_hover_line(lid)

                return omo

            ap.on_mouseover(mkomo(lid))

        # fix geometry of lines that run parallel to one another
        for locs, aps in locs2ap.items():
            if len(aps) == 2:
                p1, p2 = eval(locs)
                p1, p2 = np.array(p1), np.array(p2)

                tvec = p1 - p2
                nvec = np.array([tvec[1], -tvec[0]])
                nvec = nvec / np.linalg.norm(nvec)

                pm = p2 + tvec / 2 + nvec
                aps[0][0].locations = np.array([p1, pm, p2]).tolist()
                aps[0][1].locations = np.array([p1, pm, p2]).tolist()
                pm = p2 + tvec / 2 - nvec
                aps[1][0].locations = np.array([p1, pm, p2]).tolist()
                aps[1][1].locations = np.array([p1, pm, p2]).tolist()

        l = [e[0] for e in lid2ap.values()] + [e[1] for e in lid2ap.values()]
        self.lgs["lines-animated"].layers = l  # list(lid2ap.values())

    def _make_gens(self, update_icons=True):
        obs = self.env.get_obs()
        sub2pos = self.sub2pos
        scale = self._scale  # lambda p: self._scale([p[1], p[0]])

        gtype2icon = {
            "nuclear": "radioactive",
            "thermal": "fire",
            "solar": "solar-panel",
            "wind": "wind-turbine",
            "hydro": "hydro-power",
        }
        gen2loc = {}
        self.gen2loc = gen2loc
        r = 50

        if update_icons:
            self.gen_icons = []
        for lid, sid in enumerate(obs.gen_to_subid):
            sloc = sub2pos[f"sub_{sid}"][obs.gen_bus[lid]]

            sl = np.array(sloc)
            a = 2 * 3.1415 / 16 * obs.gen_to_sub_pos[lid]
            x = sl[0] + r * np.cos(a)
            y = sl[1] + r * np.sin(a)
            lloc = np.array([x, y]).tolist()
            gen2loc[lid] = [
                scale(lloc),
                scale(sloc),
            ]  # {"loc": (x, y), "sub_loc": sloc}
            gicon = gtype2icon[obs.gen_type[lid]]
            # icon = ipl.Icon(
            #     icon_url=f"/files/nvgrid/assets/{gicon}.svg", icon_size=[30, 30]
            # )
            # marker = ipl.Marker(location=scale([lloc[1], lloc[0]]), icon=icon)
            if update_icons:
                imo = place_image(
                    scale([lloc[1], lloc[0]]), 1, f"{PATH2ICONS}{gicon}.svg"
                )

                self.gen_icons += [imo]
        gj = self.make_gen_fc()
        # self.lgs["gens"].layers = self.gen_icons + [gj]
        newlayers = [gj] + self.gen_icons
        self._update_lgs("gens", newlayers)

    def make_gen_fc(self):
        if "gens" not in self.el2feature:
            self.el2feature["gens"] = {}

        obs = self.env.get_obs()
        features = []
        fc = {"type": "FeatureCollection", "features": features}

        for lid, locs in self.gen2loc.items():
            f = {
                "type": "Feature",
                "properties": {
                    "ftype": "gen",
                    "fid": lid,
                    "style": {"color": "yellow", "weight": 3},
                },
            }
            t = np.array(locs[1]) - np.array(locs[0])
            t /= np.linalg.norm(t)

            p0 = (np.array(locs[0]) + t * 3 / 2).tolist()
            nlocs = [p0, locs[1]]

            f["geometry"] = {"type": "LineString", "coordinates": nlocs}

            # features += [f]
            col = "green" if obs.gen_p[lid] > 0 else "black"
            fpoly = make_reg_poly(locs[0], 3 / 2, 6, fid=lid, color=col)
            f = merge_feature_geometries(fpoly, f)
            features += [f]
            self.el2feature["gens"][lid] = f

        hover_style = {"weight": 7}

        def oh(**a):
            props = a["feature"]["properties"]
            lid = props["fid"]
            self._on_hover_gen(lid)

        def oc(**a):
            with self.app.output:
                if a["event"] == "click":
                    self.selected_gen = a["feature"]["properties"]["fid"]

        gj = ipl.GeoJSON(data=fc, hover_style=hover_style)
        gj.on_hover(oh)
        gj.on_click(oc)
        return gj

    def _make_loads(self, update_icons=True):
        obs = self.env.get_obs()
        sub2pos = self.sub2pos
        scale = self._scale  # lambda p: self._scale([p[1], p[0]])

        load2loc = {}
        self.load2loc = load2loc
        r = 50
        # markers = []
        if update_icons:
            self.load_icons = []
        for lid, sid in enumerate(obs.load_to_subid):
            sloc = sub2pos[f"sub_{sid}"][obs.load_bus[lid]]

            sl = np.array(sloc)
            a = 2 * 3.1415 / 16 * obs.load_to_sub_pos[lid]
            x = sl[0] + r * np.cos(a)
            y = sl[1] + r * np.sin(a)
            lloc = np.array([x, y]).tolist()
            load2loc[lid] = [
                scale(lloc),
                scale(sloc),
            ]  # {"loc": (x, y), "sub_loc": sloc}
            # icon = ipl.Icon(
            #     icon_url="/files/nvgrid/assets/power-plug.svg", icon_size=[30, 30]
            # )
            # marker = ipl.Marker(location=scale([lloc[1], lloc[0]]), icon=icon)
            if update_icons:
                imo = place_image(
                    scale([lloc[1], lloc[0]]), 1, f"{PATH2ICONS}/power-plug.svg"
                )
                self.load_icons += [imo]
        gj = self.make_load_fc()
        # self.lgs["loads"].layers =
        newlayers = [gj] + self.load_icons
        self._update_lgs("loads", newlayers)

    def make_load_fc(self):
        if "loads" not in self.el2feature:
            self.el2feature["loads"] = {}

        obs = self.env.get_obs()
        features = []
        fc = {"type": "FeatureCollection", "features": features}

        for lid, locs in self.load2loc.items():
            f = {
                "type": "Feature",
                "properties": {
                    "ftype": "load",
                    "fid": lid,
                    "style": {"color": "black", "weight": 3},
                },
            }
            t = np.array(locs[1]) - np.array(locs[0])
            t /= np.linalg.norm(t)

            p0 = (np.array(locs[0]) + t * 3 / 2).tolist()
            nlocs = [p0, locs[1]]

            f["geometry"] = {"type": "LineString", "coordinates": nlocs}

            # features += [f]

            col = "black"
            if obs.load_p[lid] > 0:
                col = "orange"
            elif obs.load_p[lid] < 0:
                col = "green"
            fpoly = make_reg_poly(locs[0], 3 / 2, 4, fid=lid, color=col)

            f = merge_feature_geometries(fpoly, f)

            features += [f]
            self.el2feature["loads"][lid] = f

        hover_style = {"weight": 7}

        def oh(**a):
            props = a["feature"]["properties"]
            lid = props["fid"]
            self._on_hover_load(lid)

        gj = ipl.GeoJSON(data=fc, hover_style=hover_style)
        gj.on_hover(oh)
        return gj


#####
# GEoJSON utilities
def make_polygon_feature(locs, fid="", color="black", weight=1):
    f = {
        "type": "Feature",
        "properties": {
            "ftype": "gen",
            "fid": fid,
            "style": {"color": color, "weight": weight},
        },
    }
    f["geometry"] = {"type": "Polygon", "coordinates": [locs]}
    return f


def make_reg_poly(loc, r, n, fid="", color="black", weight="1"):
    cx, cy = loc
    locs = []
    for i in range(n + 1):
        a = 2 * 3.1415 / n * i
        x = cx + r * np.cos(a)
        y = cy + r * np.sin(a)
        locs += [[x, y]]

    return make_polygon_feature(locs, fid=fid, color=color, weight=weight)


def place_image(loc, r, fname):
    x, y = loc
    bounds = [[x - r, y - r], [x + r, y + r]]
    imo = ipl.ImageOverlay(url=fname, bounds=bounds)
    return imo


def merge_feature_geometries(f1, f2):
    geom = {
        "type": "GeometryCollection",
        "geometries": [f["geometry"] for f in [f1, f2]],
    }

    f = {k: v for k, v in f1.items()}
    f["geometry"] = geom
    return f
