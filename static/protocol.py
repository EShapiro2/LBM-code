"""The static protocol of sections/static.tex, simulated.

The simulation computes globally what each dispatcher computes from its two-hop knowledge; the numbers are the same.
"""
import json, sys, time, argparse, os
import numpy as np
from scipy.spatial import Voronoi, cKDTree
from shapely.geometry import Polygon, Point, LineString

import geometry as G

CONTENT = 0.10          # a dispatcher is content when its load is within 10% of each neighbour's (5% until 2026-09-30 14:48)
RATIO = 2.0             # compactness: diameter / width <= 2
RW_TRIES = 10           # random-walk directions tried before giving up
HALVINGS = 3            # (superseded by LENGTHS)
LENGTHS = 7             # step lengths tried per direction: dist/2, dist/4, ..., dist/128, where dist is the distance to the heaviest neighbour
NEW_NEIGHBOURS = True   # a move may change the neighbours; the objective is then taken over the old and the new neighbourhood together
RELOC_RATIO = 3.0       # compactness bound on the cells a departure or split makes; the moves round them off
RW_RETRIES = 1          # after a failed departure or split: one random walk, which takes no time, and one more attempt in the same turn
DIRECTIONS = 32         # directions scanned for the move (1 = toward the heaviest neighbour only)
LOOKAHEAD = True        # the walk of a departure or split looks one hop ahead (two-hop knowledge)
OBJECTIVE = "squares"   # "gap": sum of the neighbourhood mean absolute gaps; "squares": sum of squared loads of the cells whose loads change
BLOCKED_CONTENT = True  # a dispatcher lighter than its neighbours whose departure is blocked by compactness is content
RESTARTS = 10           # a walk whose host is rejected restarts from a random neighbour of the host, this many times, within the turn


class Config:
    """A configuration of centres; cells, loads and neighbours are computed on demand and cached."""

    def __init__(self, centres, city, req, far):
        self.c = np.asarray(centres, float)
        self.n = len(self.c)
        self.city = city
        self.req = req
        self.vor = Voronoi(np.vstack([self.c, far]))
        self.ridges = {}
        for (i, j), rv in zip(self.vor.ridge_points, self.vor.ridge_vertices):
            if i < self.n and j < self.n:
                self.ridges.setdefault(i, []).append((j, rv)); self.ridges.setdefault(j, []).append((i, rv))
        _, idx = cKDTree(self.c).query(req)
        self.owner = idx
        self.load = np.bincount(idx, minlength=self.n)
        self._cell = {}
        self._nb = {}

    def cell(self, i):
        if i not in self._cell:
            reg = self.vor.regions[self.vor.point_region[i]]
            if -1 in reg or len(reg) == 0:
                self._cell[i] = G.halfplane_cell(i, self.c, self.city)
            else:
                self._cell[i] = Polygon(self.vor.vertices[reg]).intersection(self.city)
        return self._cell[i]

    def nb(self, i):
        if i not in self._nb:
            s = set()
            for j, rv in self.ridges.get(i, []):
                if -1 in rv:
                    ok = self.cell(i).boundary.intersection(self.cell(j).boundary).length > G.TOL
                else:
                    ok = LineString(self.vor.vertices[rv]).intersection(self.city).length > G.TOL
                if ok:
                    s.add(j)
            self._nb[i] = s
        return self._nb[i]

    def gap(self, i):
        nb = self.nb(i)
        if not nb:
            return 0.0
        return float(np.mean([abs(int(self.load[i]) - int(self.load[j])) for j in nb]))

    def objective(self, S):
        if OBJECTIVE == "squares":
            return float(sum(int(self.load[k]) ** 2 for k in S))
        return sum(self.gap(k) for k in S)

    def content(self, i):
        Li = int(self.load[i])
        return all(abs(Li - int(self.load[j])) <= CONTENT * max(Li, int(self.load[j])) for j in self.nb(i))

    def ratio(self, k):
        d, w = G.width_and_diameter(self.cell(k))
        return d / w if w > G.TOL else np.inf

    def compact(self, S, bound=RATIO, before=None):
        """Every cell of S within the bound, except a cell already beyond it in `before` that has not got worse."""
        for k in S:
            if self.cell(k).is_empty:
                continue
            r = self.ratio(k)
            if r <= bound + 1e-9:
                continue
            if before is not None and r <= before.ratio(k) + 1e-9:
                continue
            return False
        return True

    def median_nb(self, i):
        return float(np.median([self.load[j] for j in self.nb(i)]))


class Sim:
    def __init__(self, centres, city, requests, rng):
        self.city = city
        self.req = requests
        self.rng = rng
        minx, miny, maxx, maxy = city.bounds
        pad = 10 * max(maxx - minx, maxy - miny)
        self.far = np.array([[minx - pad, miny - pad], [maxx + pad, miny - pad], [maxx + pad, maxy + pad], [minx - pad, maxy + pad]])
        self.evals = 0
        self.blocked = {}
        self.cfg = self.make(centres)

    def make(self, centres):
        self.evals += 1
        return Config(centres, self.city, self.req, self.far)

    def with_centre(self, i, p):
        c = self.cfg.c.copy(); c[i] = p
        return self.make(c)

    def inside(self, p):
        return self.city.contains(Point(p))

    def collides(self, c, p, i):
        d = np.hypot(*(c - p).T); d[i] = np.inf
        return d.min() < 1e-6

    # ---- the move ----
    def cut_short(self, i, u, s, nb0):
        """Largest s' <= s along u such that i's neighbours stay nb0, by bisection on the exact test."""
        c = self.cfg.c
        p = c[i] + s * u
        if self.inside(p) and not self.collides(c, p, i) and self.with_centre(i, p).nb(i) == nb0:
            return s, False
        lo, hi = 0.0, s
        for _ in range(20):
            mid = (lo + hi) / 2
            p = c[i] + mid * u
            ok = self.inside(p) and not self.collides(c, p, i) and self.with_centre(i, p).nb(i) == nb0
            if ok:
                lo = mid
            else:
                hi = mid
        return lo * 0.999, True

    def move(self, i, stats):
        cfg = self.cfg
        nb0 = set(cfg.nb(i))
        if not nb0:
            return False
        h = max(nb0, key=lambda j: cfg.load[j])
        Li, Lh = int(cfg.load[i]), int(cfg.load[h])
        d = cfg.c[h] - cfg.c[i]
        dist = np.hypot(*d)
        if dist < 1e-9 or Li == Lh:
            return False
        u0 = d / dist
        if Lh < Li:
            u0 = -u0
        frac = abs(Li - Lh) / max(Li, Lh)
        s = frac * dist
        S = {i} | nb0
        before = cfg.objective(S)
        if DIRECTIONS <= 1:
            dirs = [u0]
        else:
            a0 = np.arctan2(u0[1], u0[0])
            dirs = [np.array([np.cos(a0 + 2 * np.pi * k / DIRECTIONS), np.sin(a0 + 2 * np.pi * k / DIRECTIONS)]) for k in range(DIRECTIONS)]
        best = None
        lengths = [dist / 2 ** k for k in range(1, LENGTHS + 1)]   # dist/2, dist/4, ..., independent of the load difference
        for u in dirs:
            for h_, s2 in enumerate(lengths):
                p = cfg.c[i] + s2 * u
                if self.inside(p) and not self.collides(cfg.c, p, i):
                    new = self.with_centre(i, p)
                    nb1 = new.nb(i)
                    if nb1 == nb0:
                        b, a = before, new.objective(S)
                    elif NEW_NEIGHBOURS:
                        S2 = S | nb1
                        b, a = cfg.objective(S2), new.objective(S2)
                    else:
                        s2 = None
                    if s2 is not None and a < b - 1e-12 and new.compact({i} | nb1, RATIO, cfg):
                        if best is None or a - b < best[0]:
                            best = (a - b, new, nb1 != nb0, h_)
                        break
        if best is None:
            stats["rejected"] += 1
            return False
        gain, new, changed, h_ = best
        self.cfg = new
        stats["accepted"] += 1
        stats["cut"] += int(changed)
        stats["halved"] += h_
        return True

    # ---- departure and splitting ----
    def wants_departure(self, i):
        cfg = self.cfg; nb = cfg.nb(i)
        if not nb:
            return False
        d = len(nb)
        if cfg.load[i] == 0:
            return any(cfg.load[j] > 0 for j in nb)
        return cfg.load[i] < min(cfg.load[j] for j in nb) and cfg.load[i] < d / (d + 1) * cfg.median_nb(i)

    def wants_split(self, i):
        cfg = self.cfg; nb = cfg.nb(i)
        if not nb:
            return False
        d = len(nb)
        return cfg.load[i] > max(cfg.load[j] for j in nb) and cfg.load[i] > (d + 1) / d * cfg.median_nb(i)

    @staticmethod
    def walk(cfg, start, up):
        """From start, step towards the heaviest (up) or lightest (down) load within two hops until none is better than the current."""
        sign = 1 if up else -1
        k = start; seen = {k}
        while True:
            nb = [j for j in cfg.nb(k) if j not in seen]
            if not nb:
                return k
            def reach(j):
                v = sign * int(cfg.load[j])
                if LOOKAHEAD:
                    v = max([v] + [sign * int(cfg.load[m]) for m in cfg.nb(j) if m != k])
                return v
            best = max(nb, key=reach)
            if reach(best) > sign * int(cfg.load[k]):
                k = best; seen.add(k); continue
            return k

    def relocate(self, i, stats):
        """Departure of i (light) or split by i (heavy). None if neither applies; else True/False for done/rejected."""
        depart = self.wants_departure(i)
        split = self.wants_split(i)
        if not (depart or split):
            return None
        cfg = self.cfg; c0 = cfg.c
        S = {i} | cfg.nb(i)
        kind = "departure" if depart else "split"
        if depart:
            others = [k for k in range(cfg.n) if k != i]
            red = self.make(c0[others])
            start = max(range(len(others)), key=lambda j: red.load[j] if others[j] in S else -1)
            walk_cfg, up = red, True
        else:
            cm0, cp0 = G.split_cell(cfg.cell(i), self.req[cfg.owner == i])
            if np.hypot(*(cm0 - c0[i])) > np.hypot(*(cp0 - c0[i])):
                cm0, cp0 = cp0, cm0
            start = min(cfg.nb(i), key=lambda j: cfg.load[j])
            walk_cfg, up = cfg, False
        why = "objective"
        for attempt in range(RESTARTS + 1):
            k = self.walk(walk_cfg, start, up=up)
            if depart:
                target = others[k]
                cm, cp = G.split_cell(red.cell(k), self.req[red.owner == k])
                if np.hypot(*(cm - c0[target])) > np.hypot(*(cp - c0[target])):
                    cm, cp = cp, cm
                new = c0.copy(); new[target] = cm; new[i] = cp
                touched = S | {target} | cfg.nb(target)
            else:
                if k == i:
                    why = "objective"
                else:
                    new = c0.copy(); new[i] = cm0; new[k] = cp0
                    touched = S | {k} | cfg.nb(k)
            if not (split and k == i):
                if all(self.inside(new[t]) for t in touched):
                    newcfg = self.make(new)
                    S2 = set(touched)
                    for t in list(touched):
                        S2 |= cfg.nb(t) | newcfg.nb(t)
                    before = cfg.objective(S2)
                    after = newcfg.objective(S2)
                    comp = newcfg.compact(S2, RELOC_RATIO, cfg)
                    if after < before - 1e-12 and comp:
                        self.cfg = newcfg
                        self.blocked.pop(i, None)
                        stats[kind] += 1
                        stats["restarts"] += attempt
                        return True
                    why = "compact" if (depart and not comp) else "objective"
            if why == "compact":
                break
            # the host is rejected: restart the walk from a random neighbour of the host; the walk takes no time
            nbk = [j for j in walk_cfg.nb(k)]
            if not nbk:
                break
            start = int(self.rng.choice(nbk))
        self.blocked[i] = why
        stats[kind + "_rejected"] += 1
        return False

    # ---- random walk ----
    def random_walk(self, i, stats):
        cfg = self.cfg
        cell = cfg.cell(i)
        if cell.is_empty:
            return False
        r = cell.boundary.distance(Point(cfg.c[i]))
        if r < 1e-6:
            r = 0.05
        for _ in range(RW_TRIES):
            ang = self.rng.uniform(0, 2 * np.pi)
            L = self.rng.uniform(0, r)
            p = cfg.c[i] + L * np.array([np.cos(ang), np.sin(ang)])
            if not self.inside(p) or self.collides(cfg.c, p, i):
                continue
            new = self.with_centre(i, p)
            if new.compact({i} | new.nb(i), RATIO, cfg):
                self.cfg = new
                stats["random"] += 1
                return True
        stats["random_failed"] += 1
        return False

    # ---- a turn ----
    def turn(self, i, stats):
        if self.cfg.content(i):
            return
        for _ in range(RW_RETRIES + 1):
            r = self.relocate(i, stats)
            if r is False and BLOCKED_CONTENT and self.blocked.get(i) == "compact":
                stats["blocked"] += 1
                return
            if r is None:
                self.move(i, stats)
                return
            if r is True:
                return
            # a departure or split failed: random walk, which takes no time, and try again
            if not self.random_walk(i, stats):
                return

    # ---- reporting ----
    def report(self):
        cfg = self.cfg; n = cfg.n
        cont = sum(cfg.content(i) or (BLOCKED_CONTENT and self.blocked.get(i) == "compact") for i in range(n))
        dw = []
        for i in range(n):
            d, w = G.width_and_diameter(cfg.cell(i)); dw.append(d / w if w > G.TOL else np.inf)
        gaps = [cfg.gap(i) for i in range(n)]
        return dict(content=int(cont), min_load=int(cfg.load.min()), max_load=int(cfg.load.max()),
                    ratio=float(cfg.load.max() / max(1, cfg.load.min())), empty=int((cfg.load == 0).sum()),
                    mean_gap=float(np.mean(gaps)), max_gap=float(max(gaps)),
                    max_dw=float(max(dw)), noncompact=int(sum(x > RATIO + 1e-9 for x in dw)))


def lattice(city, n):
    """n centres on a regular triangular lattice inside the city, by searching the spacing."""
    minx, miny, maxx, maxy = city.bounds
    lo, hi = 0.05, 5.0
    best = None
    for _ in range(60):
        a = (lo + hi) / 2
        pts = []
        h = a * np.sqrt(3) / 2
        row = 0; y = miny + h / 2
        while y < maxy:
            x = minx + (a / 2 if row % 2 else 0) + a / 4
            while x < maxx:
                if city.contains(Point(x, y)):
                    pts.append((x, y))
                x += a
            y += h; row += 1
        best = np.array(pts)
        if len(pts) == n:
            break
        if len(pts) > n:
            lo = a
        else:
            hi = a
    if len(best) != n:
        raise SystemExit(f"lattice gave {len(best)} points, wanted {n}")
    return best


def render(sim, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.cm import ScalarMappable
    cfg = sim.cfg
    fig, ax = plt.subplots(figsize=(7, 12))
    vmax = max(1, int(cfg.load.max()))
    # white for empty, light blue for sparse, through yellow and orange to deep red for the densest
    cmap = LinearSegmentedColormap.from_list("loads", [(0.0, "white"), (0.02, "#cfe8ff"), (0.3, "#7fbfff"), (0.55, "#ffe066"), (0.75, "#ff8c1a"), (0.9, "#e03000"), (1.0, "#7a0000")])
    norm = Normalize(0, vmax)
    for i in range(cfg.n):
        cell = cfg.cell(i)
        polys = [cell] if cell.geom_type == "Polygon" else [g for g in cell.geoms if g.geom_type == "Polygon"]
        for p in polys:
            ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, facecolor=cmap(norm(cfg.load[i])), edgecolor="k", linewidth=0.4))
        cx, cy = cfg.c[i]
        ax.text(cx, cy, str(int(cfg.load[i])), fontsize=5, ha="center", va="center", color="w" if cfg.load[i] > 0.6 * vmax else "k")
    x, y = cfg.city.exterior.xy
    ax.plot(x, y, "k-", lw=0.6)
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
    b = cfg.city.bounds
    ax.set_xlim(b[0] - 0.2, b[2] + 0.2); ax.set_ylim(b[1] - 0.2, b[3] + 0.2)
    ax.axis("off")
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("requests in the cell", fontsize=8); cb.ax.tick_params(labelsize=7)
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    global HALVINGS, RELOC_RATIO, RW_RETRIES, DIRECTIONS, LOOKAHEAD, OBJECTIVE, LENGTHS, NEW_NEIGHBOURS
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default="../inputs")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--rounds", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="runs/run1")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--halvings", type=int, default=HALVINGS)
    ap.add_argument("--reloc-ratio", type=float, default=RELOC_RATIO)
    ap.add_argument("--rw-retries", type=int, default=RW_RETRIES)
    ap.add_argument("--directions", type=int, default=DIRECTIONS)
    ap.add_argument("--no-lookahead", action="store_true")
    ap.add_argument("--objective", default=OBJECTIVE, choices=["gap", "squares"])
    ap.add_argument("--lengths", type=int, default=LENGTHS)
    ap.add_argument("--no-new-neighbours", action="store_true")
    a = ap.parse_args()
    OBJECTIVE = a.objective; LENGTHS = a.lengths; NEW_NEIGHBOURS = not a.no_new_neighbours
    HALVINGS = a.halvings; RELOC_RATIO = a.reloc_ratio; RW_RETRIES = a.rw_retries; DIRECTIONS = a.directions; LOOKAHEAD = not a.no_lookahead
    os.makedirs(a.out, exist_ok=True)
    city = G.load_city(f"{a.inputs}/manhattan_main_island_km.json")
    req = G.load_requests(f"{a.inputs}/pickups_2015-01-15_0800-0815_quantized.json")
    req = req[[city.contains(Point(p)) for p in req]]
    rng = np.random.default_rng(a.seed)
    r0 = 0
    if a.resume and os.path.exists(f"{a.out}/state.json"):
        s = json.load(open(f"{a.out}/state.json")); centres = np.array(s["centres"]); r0 = s["round"]
        rng = np.random.default_rng([a.seed, r0])
        log = open(f"{a.out}/log.jsonl", "a")
    else:
        centres = lattice(city, a.n)
        log = open(f"{a.out}/log.jsonl", "w")
    sim = Sim(centres, city, req, rng)
    if r0 == 0:
        rep = sim.report(); rep.update(round=0); print(json.dumps(rep), flush=True); log.write(json.dumps(rep) + "\n"); log.flush()
        render(sim, f"{a.out}/round_000.png", f"round 0: {rep['content']} content, loads {rep['min_load']}-{rep['max_load']}")
    t0 = time.time()
    for r in range(r0 + 1, a.rounds + 1):
        stats = dict(accepted=0, cut=0, halved=0, rejected=0, blocked=0, restarts=0, departure=0, departure_rejected=0, split=0, split_rejected=0, random=0, random_failed=0)
        sim.evals = 0
        for i in rng.permutation(sim.cfg.n):
            sim.turn(int(i), stats)
        rep = sim.report(); rep.update(round=r, secs=round(time.time() - t0, 1), evals=sim.evals, **stats)
        print(json.dumps(rep), flush=True); log.write(json.dumps(rep) + "\n"); log.flush()
        json.dump(dict(round=r, centres=sim.cfg.c.tolist(), loads=sim.cfg.load.tolist()), open(f"{a.out}/state.json", "w"))
        if r % 10 == 0 or rep["content"] == sim.cfg.n:
            render(sim, f"{a.out}/round_{r:03d}.png", f"round {r}: {rep['content']} content, loads {rep['min_load']}-{rep['max_load']}")
        if rep["content"] == sim.cfg.n:
            print("TERMINATED: every dispatcher is content", flush=True); break
    log.close()


if __name__ == "__main__":
    main()
