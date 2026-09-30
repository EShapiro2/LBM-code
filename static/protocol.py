"""The static protocol of sections/static.tex, simulated.

The simulation computes globally what each dispatcher computes from its two-hop knowledge; the numbers are the same.
"""
import json, sys, time, argparse, os
import numpy as np
from scipy.spatial import Voronoi, cKDTree
from shapely.geometry import Polygon, Point, LineString

import geometry as G

CONTENT = 0.05          # a dispatcher is content when its load is within 5% of each neighbour's
RATIO = 2.0             # compactness: diameter / width <= 2
RW_TRIES = 10           # random-walk directions tried before giving up
EMPTY_DEPARTS = False   # variant: an empty dispatcher is not content and departs
RW_AFTER = 1            # variant: random walk only after this many consecutive failed turns
HALVINGS = 0            # variant: if the proposed step is rejected, try s/2, s/4, ... this many times
RELOC_RATIO = 2.0       # variant: compactness bound applied to the cells after a departure or split


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
        return sum(self.gap(k) for k in S)

    def content(self, i):
        Li = int(self.load[i])
        if EMPTY_DEPARTS and Li == 0:
            return False
        return all(abs(Li - int(self.load[j])) <= CONTENT * max(Li, int(self.load[j])) for j in self.nb(i))

    def compact(self, S):
        return all(G.compact(self.cell(k), RATIO) for k in S if not self.cell(k).is_empty)

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
        self.cfg = self.make(centres)
        self.fails = np.zeros(self.cfg.n, int)

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
        u = d / dist
        if Lh < Li:
            u = -u
        frac = abs(Li - Lh) / max(Li, Lh)
        s = frac * dist
        S = {i} | nb0
        before = cfg.objective(S)
        s2, cut = self.cut_short(i, u, s, nb0)
        if s2 <= 1e-9:
            stats["rejected"] += 1
            return False
        for h_ in range(HALVINGS + 1):
            new = self.with_centre(i, cfg.c[i] + s2 * u)
            after = new.objective(S)
            if after < before - 1e-12 and new.compact({i} | new.nb(i)):
                self.cfg = new
                stats["accepted"] += 1
                stats["cut"] += int(cut)
                stats["halved"] += h_
                return True
            s2 /= 2
        stats["rejected"] += 1
        return False

    # ---- departure and splitting ----
    def wants_departure(self, i):
        cfg = self.cfg; nb = cfg.nb(i)
        if not nb:
            return False
        d = len(nb)
        if EMPTY_DEPARTS and cfg.load[i] == 0:
            return True
        return cfg.load[i] < min(cfg.load[j] for j in nb) and cfg.load[i] < d / (d + 1) * cfg.median_nb(i)

    def wants_split(self, i):
        cfg = self.cfg; nb = cfg.nb(i)
        if not nb:
            return False
        d = len(nb)
        return cfg.load[i] > max(cfg.load[j] for j in nb) and cfg.load[i] > (d + 1) / d * cfg.median_nb(i)

    @staticmethod
    def walk(cfg, start, up):
        """From start, step to the heaviest (up) or lightest (down) neighbour until at a local extremum."""
        k = start; seen = {k}
        while True:
            nb = cfg.nb(k)
            if not nb:
                return k
            best = max(nb, key=lambda j: cfg.load[j]) if up else min(nb, key=lambda j: cfg.load[j])
            better = cfg.load[best] > cfg.load[k] if up else cfg.load[best] < cfg.load[k]
            if better and best not in seen:
                k = best; seen.add(k); continue
            # on a plateau, continue to an unvisited neighbour of equal load
            eq = [j for j in nb if cfg.load[j] == cfg.load[k] and j not in seen]
            if eq:
                k = min(eq); seen.add(k); continue
            return k

    def relocate(self, i, stats):
        """Departure of i (light) or split by i (heavy). None if neither applies; else True/False for done/rejected."""
        depart = self.wants_departure(i)
        split = self.wants_split(i)
        if not (depart or split):
            return None
        cfg = self.cfg; c0 = cfg.c
        S = {i} | cfg.nb(i)
        if depart:
            # i's cell is absorbed; on the loads after absorption, the freed dispatcher walks uphill from i's heaviest neighbour
            others = [k for k in range(cfg.n) if k != i]
            red = self.make(c0[others])
            start = max(range(len(others)), key=lambda j: red.load[j] if others[j] in S else -1)
            k = self.walk(red, start, up=True)
            target = others[k]
            cm, cp = G.split_cell(red.cell(k))
            if np.hypot(*(cm - c0[target])) > np.hypot(*(cp - c0[target])):
                cm, cp = cp, cm
            new = c0.copy(); new[target] = cm; new[i] = cp
            kind = "departure"; touched = S | {target} | cfg.nb(target)
        else:
            # i splits; the anti-dispatcher walks downhill from i's lightest neighbour to a local minimum k, which is eliminated and takes the new half
            cm, cp = G.split_cell(cfg.cell(i))
            if np.hypot(*(cm - c0[i])) > np.hypot(*(cp - c0[i])):
                cm, cp = cp, cm
            start = min(cfg.nb(i), key=lambda j: cfg.load[j])
            k = self.walk(cfg, start, up=False)
            if k == i:
                stats["split_rejected"] += 1
                return False
            new = c0.copy(); new[i] = cm; new[k] = cp
            kind = "split"; touched = S | {k} | cfg.nb(k)
        if not all(self.inside(new[t]) for t in touched):
            stats[kind + "_rejected"] += 1
            return False
        newcfg = self.make(new)
        S2 = set(touched)
        for t in list(touched):
            S2 |= cfg.nb(t) | newcfg.nb(t)
        before = cfg.objective(S2)
        after = newcfg.objective(S2)
        if after < before - 1e-12 and all(G.compact(newcfg.cell(k), RELOC_RATIO) for k in S2 if not newcfg.cell(k).is_empty):
            self.cfg = newcfg
            stats[kind] += 1
            return True
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
            if new.compact({i} | new.nb(i)):
                self.cfg = new
                stats["random"] += 1
                return True
        stats["random_failed"] += 1
        return False

    # ---- a turn ----
    def turn(self, i, stats):
        if self.cfg.content(i):
            self.fails[i] = 0
            return
        r = self.relocate(i, stats)
        if r is True or (r is None and self.move(i, stats)):
            self.fails[i] = 0
            return
        self.fails[i] += 1
        if self.fails[i] >= RW_AFTER:
            self.random_walk(i, stats)
            self.fails[i] = 0

    # ---- reporting ----
    def report(self):
        cfg = self.cfg; n = cfg.n
        cont = sum(cfg.content(i) for i in range(n))
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
    cfg = sim.cfg
    fig, ax = plt.subplots(figsize=(6, 12))
    vmax = max(1, cfg.load.max())
    for i in range(cfg.n):
        cell = cfg.cell(i)
        polys = [cell] if cell.geom_type == "Polygon" else [g for g in cell.geoms if g.geom_type == "Polygon"]
        for p in polys:
            ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, facecolor=plt.cm.viridis(cfg.load[i] / vmax), edgecolor="k", linewidth=0.4))
        cx, cy = cfg.c[i]
        ax.text(cx, cy, str(int(cfg.load[i])), fontsize=5, ha="center", va="center", color="w")
    x, y = cfg.city.exterior.xy
    ax.plot(x, y, "k-", lw=0.6)
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
    b = cfg.city.bounds
    ax.set_xlim(b[0] - 0.2, b[2] + 0.2); ax.set_ylim(b[1] - 0.2, b[3] + 0.2)
    ax.axis("off")
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default="../inputs")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--rounds", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="runs/run1")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--empty-departs", action="store_true")
    ap.add_argument("--rw-after", type=int, default=1)
    ap.add_argument("--halvings", type=int, default=0)
    ap.add_argument("--reloc-ratio", type=float, default=2.0)
    a = ap.parse_args()
    global EMPTY_DEPARTS, RW_AFTER, HALVINGS, RELOC_RATIO
    EMPTY_DEPARTS = a.empty_departs; RW_AFTER = a.rw_after; HALVINGS = a.halvings; RELOC_RATIO = a.reloc_ratio
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
        stats = dict(accepted=0, cut=0, halved=0, rejected=0, departure=0, departure_rejected=0, split=0, split_rejected=0, random=0, random_failed=0)
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
