import os


def load_template(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


def rho2color(rho):
    color = "black"
    color = "green"
    if rho > 0.70:
        color = "#888800"
    if rho > 0.80:
        color = "orange"
    if rho > 0.99:
        color = "red"
    return color


def dict2pretty_string(d):
    from pprint import pprint
    from io import StringIO

    o = StringIO()
    pprint(d, o, width=30)
    o.seek(0)
    return o.read()


class AllTopoActions:
    def __init__(self, env):
        self.env = env
        obs = env.get_obs()

        self.subid2actids = {}
        self.nsubs = len(obs.time_before_cooldown_sub)
        self.actions = []
        for subid, cdt in enumerate(obs.time_before_cooldown_sub):
            acts = env.action_space.get_all_unitary_topologies_change(
                env.action_space, sub_id=subid
            )
            n = len(self.actions)
            self.actions += acts
            self.subid2actids[subid] = list(range(n, len(self.actions)))

        self.nactions = len(self.actions)

    def get_actions(self, exclude_subs=[]):
        obs = self.env.get_obs()
        excludesubs = exclude_subs + [
            subid for subid, cdt in enumerate(obs.time_before_cooldown_sub) if cdt > 0
        ]
        print("excludesubs", excludesubs)
        acts = []
        for subid in range(self.nsubs):
            if subid not in excludesubs:
                acts += [(aid, self.actions[aid]) for aid in self.subid2actids[subid]]
        return acts

    def get_action(self, aid):
        return self.actions[aid]
