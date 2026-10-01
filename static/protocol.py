"""The static protocol of sections/static.tex, simulated.

The simulation computes globally what each dispatcher computes from its two-hop knowledge; the numbers are the same.
"""
import json, sys, time, argparse, os
import numpy as np
from scipy.spatial import Voronoi, cKDTree
from shapely.geometry import Polygon, Point, LineString, GeometryCollection
import shapely

import geometry as G

CONTENT = 0.07          # a dispatcher is content when its load is within 7% of each neighbour's (5% until 14:48, 10% until 16:42 on 2026-09-30)
RATIO = 2.0             # compactness: diameter / width <= 2
RW_TRIES = 10           # random-walk directions tried before giving up
HALVINGS = 3            # (superseded by LENGTHS)
LENGTHS = 7             # step lengths tried per direction: dist/2, dist/4, ..., dist/128, where dist is the distance to the heaviest neighbour
NEW_NEIGHBOURS = True   # a move may change the neighbours; the objective is then taken over the old and the new neighbourhood together
RELOC_RATIO = 3.0       # compactness bound on the cells a departure or split makes; the moves round them off
RW_RETRIES = 0          # random walks are off (Udi, 2026-09-30 15:25): a failed departure or split leaves the dispatcher where it is
DIRECTIONS = 32         # directions scanned for the move (1 = toward the heaviest neighbour only)
LOOKAHEAD = True        # the walk of a departure or split looks one hop ahead (two-hop knowledge)
OBJECTIVE = "squares"   # "gap": sum of the neighbourhood mean absolute gaps; "squares": sum of squared loads of the cells whose loads change
BLOCKED_CONTENT = True  # a dispatcher lighter than its neighbours whose departure is blocked by compactness is content
RESTARTS = 0            # (superseded by BACKTRACK)
BACKTRACK = True        # at the end of the walk, try the host, then each of its neighbours, then backtrack one step and try again, to the start; deterministic
EXTREMES = True         # departure at every local minimum and splitting at every local maximum, ties by identifier; the objective decides
COMPACT = "neighbourhood"  # "cell": each cell compact; "neighbourhood": each cell together with its neighbours compact (Udi, 2026-09-30 16:06; default since 16:42)


class Config:
    """A configuration of centres; cells, loads and neighbours are computed on demand and cached.

    A configuration made from a parent by moving a few centres, or by changing the requests, inherits from the parent whatever
    the change leaves the same, rather than recomputing it: a cell whose Voronoi region is the same polygon, the neighbours
    of a cell whose ridges are the same, the ratio of a cell whose cell and neighbours' cells are the same, and the owner of a
    request that no moved centre is nearer to than its owner was.  The numbers are exactly those of a computation from scratch.
    The parent is kept only until this configuration has a child of its own, so at most two configurations are ever live."""

    def __init__(self, centres, city, req, far, parent=None):
        self.c = np.asarray(centres, float)
        self.n = len(self.c)
        self.city = city   # prepared by Sim, so shapely's containment tests on it are fast
        self.req = req
        self.vor = Voronoi(np.vstack([self.c, far]))
        self.ridges = {}
        for (i, j), rv in zip(self.vor.ridge_points, self.vor.ridge_vertices):
            if i < self.n and j < self.n:
                self.ridges.setdefault(i, []).append((j, rv)); self.ridges.setdefault(j, []).append((i, rv))
        self._cell = {}; self._nb = {}; self._ratio = {}; self._key = {}; self._rkey = {}
        if parent is not None and parent._p is not None:
            parent.adopt()
        self._p = parent if parent is not None and parent.n == self.n else None
        if self._p is not None and req is parent.req:
            self.owner, self.dist = parent.owners_after(self.c)
        elif len(req):
            self.dist, self.owner = cKDTree(self.c).query(req)
        else:
            self.dist, self.owner = np.zeros(0), np.zeros(0, int)
        self.load = np.bincount(self.owner, minlength=self.n)

    # ---- inheritance ----
    def region_key(self, k):
        """The Voronoi region of k as a hashable set of vertices; None when unbounded."""
        if k not in self._key:
            reg = self.vor.regions[self.vor.point_region[k]]
            self._key[k] = None if -1 in reg or len(reg) == 0 else frozenset(map(tuple, np.round(self.vor.vertices[reg], 9)))
        return self._key[k]

    def ridge_key(self, k):
        """The ridges of k as a hashable set of (neighbour, vertices); None when a ridge is unbounded."""
        if k not in self._rkey:
            out = set()
            for j, rv in self.ridges.get(k, []):
                if -1 in rv:
                    out = None; break
                out.add((j, frozenset(map(tuple, np.round(self.vor.vertices[rv], 9)))))
            self._rkey[k] = None if out is None else frozenset(out)
        return self._rkey[k]

    def adopt(self):
        """Take from the parent every cell, neighbour set and ratio still the same here, and let the parent go."""
        p = self._p
        if p is None:
            return
        for k in p._cell:
            if k not in self._cell and self.region_key(k) is not None and self.region_key(k) == p.region_key(k):
                self._cell[k] = p._cell[k]
        for k in p._nb:
            if k not in self._nb and self.ridge_key(k) is not None and self.ridge_key(k) == p.ridge_key(k):
                self._nb[k] = p._nb[k]
        for k in p._ratio:
            if k not in self._ratio and self._cell.get(k) is p._cell.get(k) and k in self._nb and self._nb[k] is p._nb.get(k) and all(self._cell.get(j) is p._cell.get(j) for j in self._nb[k]):
                self._ratio[k] = p._ratio[k]
        self._p = None

    def owners_after(self, new_c):
        """The owners of the requests, and their distances, with the centres moved to new_c: exact, from this configuration's owners.

        A request keeps its owner unless its owner moved, in which case its nearest centre is found afresh, or a moved centre is
        now nearer than its owner, in which case that centre takes it."""
        moved = np.flatnonzero(np.any(self.c != new_c, axis=1))
        owner = self.owner.copy(); dist = self.dist.copy()
        if len(self.req) and len(moved):
            mask = np.isin(owner, moved)
            if mask.any():
                dist[mask], owner[mask] = cKDTree(new_c).query(self.req[mask])
            for m in moved:
                dm = np.hypot(*(self.req - new_c[m]).T)
                better = dm < dist
                owner[better] = m; dist[better] = dm[better]
        return owner, dist

    def gain(self, new_c):
        """The change of the squares objective when the centres move to new_c: the sum over every cell of the new load squared less the
        old, which is the change over the cells the move touches, since every other cell keeps its load.  No geometry is computed."""
        owner, _ = self.owners_after(new_c)
        new_load = np.bincount(owner, minlength=self.n)
        return float((new_load.astype(np.int64) ** 2).sum() - (self.load.astype(np.int64) ** 2).sum())

    # ---- geometry ----
    def cell(self, i):
        if i not in self._cell:
            p = self._p
            if p is not None and i in p._cell and self.region_key(i) is not None and self.region_key(i) == p.region_key(i):
                self._cell[i] = p._cell[i]
                return self._cell[i]
            reg = self.vor.regions[self.vor.point_region[i]]
            if -1 in reg or len(reg) == 0:
                self._cell[i] = G.halfplane_cell(i, self.c, self.city)
            else:
                poly = Polygon(self.vor.vertices[reg])
                # a region inside the city is its own cell; only a region crossing the shore is clipped
                self._cell[i] = poly if shapely.contains(self.city, poly) else poly.intersection(self.city)
        return self._cell[i]

    def nb(self, i):
        if i not in self._nb:
            p = self._p
            if p is not None and i in p._nb and self.ridge_key(i) is not None and self.ridge_key(i) == p.ridge_key(i):
                self._nb[i] = p._nb[i]
                return self._nb[i]
            s = set()
            for j, rv in self.ridges.get(i, []):
                if -1 in rv:
                    ok = self.cell(i).boundary.intersection(self.cell(j).boundary).length > G.TOL
                else:
                    v = self.vor.vertices[rv]
                    # a ridge of positive length with an end inside the city has positive length in it; only one with both ends outside is clipped
                    ok = np.hypot(*(v[1] - v[0])) > G.TOL and (shapely.contains_xy(self.city, v[0][0], v[0][1]) or shapely.contains_xy(self.city, v[1][0], v[1][1]) or LineString(v).intersection(self.city).length > G.TOL)
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
        if k not in self._ratio:
            p = self._p
            if p is not None and k in p._ratio and self.cell(k) is p._cell.get(k) and self.nb(k) == p._nb.get(k) and all(self.cell(j) is p._cell.get(j) for j in self.nb(k)):
                self._ratio[k] = p._ratio[k]   # the same cell with the same neighbours' cells has the same ratio
                return self._ratio[k]
            if COMPACT == "neighbourhood":
                # the convex hull of the union of the cells is the hull of the cells together, so no union is computed
                u = GeometryCollection([self.cell(k)] + [self.cell(j) for j in self.nb(k)])
                d, w = G.width_and_diameter(u)
            else:
                d, w = G.width_and_diameter(self.cell(k))
            self._ratio[k] = d / w if w > G.TOL else np.inf
        return self._ratio[k]

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
        shapely.prepare(city)   # in place: shapely's containment tests on the city are then fast
        self.cfg = self.make(centres)

    def make(self, centres):
        self.evals += 1
        return Config(centres, self.city, self.req, self.far, parent=self.cfg if hasattr(self, 'cfg') else None)

    def with_centre(self, i, p):
        c = self.cfg.c.copy(); c[i] = p
        return self.make(c)

    def inside(self, p):
        return bool(shapely.contains_xy(self.city, p[0], p[1]))

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
                if not (self.inside(p) and not self.collides(cfg.c, p, i)):
                    continue
                if OBJECTIVE == "squares":
                    # the change of the objective needs no geometry; the configuration is built only for a candidate that lowers it
                    c = cfg.c.copy(); c[i] = p
                    gain = cfg.gain(c)
                    if not gain < -1e-12:
                        continue
                    new = self.make(c)
                    nb1 = new.nb(i)
                else:
                    new = self.with_centre(i, p)
                    nb1 = new.nb(i)
                    if nb1 == nb0:
                        b, a = before, new.objective(S)
                    elif NEW_NEIGHBOURS:
                        S2 = S | nb1
                        b, a = cfg.objective(S2), new.objective(S2)
                    else:
                        continue
                    gain = a - b
                    if not gain < -1e-12:
                        continue
                if new.compact({i} | nb1, RATIO, cfg):
                    if best is None or gain < best[0]:
                        best = (gain, new, nb1 != nb0, h_)
                    break
        if best is None:
            stats["rejected"] += 1
            return False
        gain, new, changed, h_ = best
        self.cfg = new; new.adopt()
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
        if EXTREMES:
            Li = int(cfg.load[i])
            return all(Li < cfg.load[j] or (Li == cfg.load[j] and i < j) for j in nb) and any(cfg.load[j] > Li for j in nb)
        return cfg.load[i] < min(cfg.load[j] for j in nb) and cfg.load[i] < d / (d + 1) * cfg.median_nb(i)

    def wants_split(self, i):
        cfg = self.cfg; nb = cfg.nb(i)
        if not nb:
            return False
        d = len(nb)
        if EXTREMES:
            Li = int(cfg.load[i])
            return all(Li > cfg.load[j] or (Li == cfg.load[j] and i < j) for j in nb) and any(cfg.load[j] < Li for j in nb)
        return cfg.load[i] > max(cfg.load[j] for j in nb) and cfg.load[i] > (d + 1) / d * cfg.median_nb(i)

    @staticmethod
    def walk_path(cfg, start, up):
        """The path of the walk, from start to its end."""
        sign = 1 if up else -1
        k = start; seen = {k}; path = [k]
        while True:
            nb = [j for j in cfg.nb(k) if j not in seen]
            if not nb:
                return path
            def reach(j):
                v = sign * int(cfg.load[j])
                if LOOKAHEAD:
                    v = max([v] + [sign * int(cfg.load[m]) for m in cfg.nb(j) if m != k])
                return v
            best = max(nb, key=reach)
            if reach(best) > sign * int(cfg.load[k]):
                k = best; seen.add(k); path.append(k); continue
            return path

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
        """Departure of i (light) or split by i (heavy). None if neither applies; else True/False for done/rejected.

        The walk ends at a host; the host is tried, then each of its neighbours, then the walk backtracks one step and tries
        again, down to its start. The first candidate that keeps the structure and lowers the objective is taken. Deterministic."""
        depart = self.wants_departure(i)
        split = self.wants_split(i)
        if not (depart or split):
            return None
        cfg = self.cfg; c0 = cfg.c
        S = {i} | cfg.nb(i)
        kind = "departure" if depart else "split"
        if depart:
            # the walk is on the loads before the departure, from i's heaviest neighbour; the split uses the cells after it
            others = [k for k in range(cfg.n) if k != i]
            red = self.make(c0[others])
            idx = {t: k for k, t in enumerate(others)}
            start = max(cfg.nb(i), key=lambda j: cfg.load[j])
            path = [t for t in self.walk_path(cfg, start, up=True) if t != i]
        else:
            cm0, cp0 = G.split_cell(cfg.cell(i), self.req[cfg.owner == i])
            if np.hypot(*(cm0 - c0[i])) > np.hypot(*(cp0 - c0[i])):
                cm0, cp0 = cp0, cm0
            start = min(cfg.nb(i), key=lambda j: cfg.load[j])
            path = self.walk_path(cfg, start, up=False)
        # candidates: the host, its neighbours, then backtrack
        cands = []
        for k in reversed(path):
            for c in [k] + sorted(cfg.nb(k)):
                if c != i and c not in cands:
                    cands.append(c)
            if not BACKTRACK:
                break
        why = "objective"; tried = 0
        for k in cands:
            if depart:
                target = k; kr = idx[k]
                cm, cp = G.split_cell(red.cell(kr), self.req[red.owner == kr])
                if np.hypot(*(cm - c0[target])) > np.hypot(*(cp - c0[target])):
                    cm, cp = cp, cm
                new = c0.copy(); new[target] = cm; new[i] = cp
                touched = S | {target} | cfg.nb(target)
            else:
                new = c0.copy(); new[i] = cm0; new[k] = cp0
                touched = S | {k} | cfg.nb(k)
            tried += 1
            if not all(self.inside(new[t]) for t in touched):
                continue
            if OBJECTIVE == "squares":
                # the change of the objective needs no geometry.  The compactness of a candidate is computed when it lowers the
                # objective, since it may then be taken, and otherwise only until one compact candidate has been seen, since all
                # a candidate that does not lower the objective can do is mark, once, that a compact candidate exists
                dec = cfg.gain(new) < -1e-12
                if not dec and why == "objective_seen":
                    continue
                newcfg = self.make(new)
                S2 = set(touched)
                for t in list(touched):
                    S2 |= cfg.nb(t) | newcfg.nb(t)
                comp = newcfg.compact(S2, RELOC_RATIO, cfg)
            else:
                newcfg = self.make(new)
                S2 = set(touched)
                for t in list(touched):
                    S2 |= cfg.nb(t) | newcfg.nb(t)
                dec = newcfg.objective(S2) < cfg.objective(S2) - 1e-12
                comp = newcfg.compact(S2, RELOC_RATIO, cfg)
            if dec and comp:
                self.cfg = newcfg; newcfg.adopt()
                self.blocked.pop(i, None)
                stats[kind] += 1
                stats["restarts"] += tried - 1
                return True
            if depart and not comp and why != "objective_seen":
                why = "compact"
            if dec and not comp:
                pass
            elif comp:
                why = "objective_seen"
        self.blocked[i] = "compact" if why == "compact" else "objective"
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
                self.cfg = new; new.adopt()
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
            if r is False and RW_RETRIES == 0:
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
        dw = [cfg.ratio(i) for i in range(n)]
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


def _lab_to_rgb(L, a, b):
    fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    def finv(f): return f ** 3 if f ** 3 > 0.008856 else (f - 16 / 116) / 7.787
    X, Y, Z = 0.95047 * finv(fx), 1.0 * finv(fy), 1.08883 * finv(fz)
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    bb = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    def gam(c):
        c = min(max(c, 0.0), 1.0)
        return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c
    return (gam(r), gam(g), gam(bb))


def _rgb_to_lab(r, g, b):
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.0
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    def f(t): return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))


def lab_colour(t):
    """The colour at t in [0,1]: the hue of the scale light blue, blue, yellow, orange, deep red, with the lightness replaced by one falling steadily from 93 to 22 (Udi, 2026-09-30 16:35)."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    base = LinearSegmentedColormap.from_list("base", [(0.0, "#cfe8ff"), (0.3, "#7fbfff"), (0.55, "#ffe066"), (0.75, "#ff8c1a"), (0.9, "#e03000"), (1.0, "#7a0000")])
    r, g, b, _ = base(t)
    L, a, bb = _rgb_to_lab(r, g, b)
    return _lab_to_rgb(93 - 71 * t, a, bb)


def render(sim, path, title, vmax=None, cars=None, waiting=None):
    """The map: cells coloured by load, with the load at each centre; `cars`, if given, are drawn as small blue dots and `waiting` calls as red ones (the dynamic case)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.cm import ScalarMappable
    cfg = sim.cfg
    fig, ax = plt.subplots(figsize=(7, 12))
    # the scale is 0 to the largest load plus the smallest, so the loads present sit in its middle (Udi, 2026-09-30 16:27)
    vmax = max(1, int(cfg.load.max()) + int(cfg.load.min())) if vmax is None else vmax
    # white for empty, light blue for sparse, through yellow and orange to deep red for the densest
    # white for empty, light blue for sparse, deep red for the densest, darkening continuously: the hues of the scale with the lightness falling linearly in CIELAB (Udi, 2026-09-30 16:31)
    # white, then yellow, orange, red, deep red, darkening steadily (Udi, 2026-09-30 16:37): matplotlib's YlOrRd, which is monotone in lightness, with white at zero
    base = plt.cm.YlOrRd
    cmap = LinearSegmentedColormap.from_list("loads", [(0.0, "white")] + [(t, base(0.05 + 0.95 * t)) for t in np.linspace(0.02, 1, 60)])
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
    if cars is not None and len(cars):
        cars = np.asarray(cars, float)
        ax.plot(cars[:, 0], cars[:, 1], ".", ms=1.5, color="royalblue", alpha=0.7, lw=0)
    if waiting is not None and len(waiting):
        waiting = np.asarray(waiting, float)
        ax.plot(waiting[:, 0], waiting[:, 1], ".", ms=2.5, color="red", alpha=0.9, lw=0)
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
    b = cfg.city.bounds
    ax.set_xlim(b[0] - 0.2, b[2] + 0.2); ax.set_ylim(b[1] - 0.2, b[3] + 0.2)
    ax.axis("off")
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("requests in the cell", fontsize=8); cb.ax.tick_params(labelsize=7)
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    global HALVINGS, RELOC_RATIO, RW_RETRIES, DIRECTIONS, LOOKAHEAD, OBJECTIVE, LENGTHS, NEW_NEIGHBOURS, EXTREMES, CONTENT, COMPACT
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default="../inputs")
    ap.add_argument("--period", default="0800-0815", help="the pickups file: pickups_2015-01-15_<period>_quantized.json")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--rounds", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="runs/run1")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--start", default=None, help="state.json to start from, as round 0")
    ap.add_argument("--no-extremes", action="store_true")
    ap.add_argument("--content", type=float, default=CONTENT)
    ap.add_argument("--compact", default=COMPACT, choices=["cell", "neighbourhood"])
    ap.add_argument("--halvings", type=int, default=HALVINGS)
    ap.add_argument("--reloc-ratio", type=float, default=RELOC_RATIO)
    ap.add_argument("--rw-retries", type=int, default=RW_RETRIES)
    ap.add_argument("--directions", type=int, default=DIRECTIONS)
    ap.add_argument("--no-lookahead", action="store_true")
    ap.add_argument("--objective", default=OBJECTIVE, choices=["gap", "squares"])
    ap.add_argument("--lengths", type=int, default=LENGTHS)
    ap.add_argument("--no-new-neighbours", action="store_true")
    a = ap.parse_args()
    OBJECTIVE = a.objective; LENGTHS = a.lengths; NEW_NEIGHBOURS = not a.no_new_neighbours; EXTREMES = not a.no_extremes
    CONTENT = a.content; COMPACT = a.compact; DIRECTIONS = a.directions
    HALVINGS = a.halvings; RELOC_RATIO = a.reloc_ratio; RW_RETRIES = a.rw_retries; DIRECTIONS = a.directions; LOOKAHEAD = not a.no_lookahead
    os.makedirs(a.out, exist_ok=True)
    city = G.load_city(f"{a.inputs}/manhattan_main_island_km.json")
    req = G.load_requests(f"{a.inputs}/pickups_2015-01-15_{a.period}_quantized.json")
    req = req[[city.contains(Point(p)) for p in req]]
    rng = np.random.default_rng(a.seed)
    r0 = 0
    if a.resume and os.path.exists(f"{a.out}/state.json"):
        s = json.load(open(f"{a.out}/state.json")); centres = np.array(s["centres"]); r0 = s["round"]
        rng = np.random.default_rng([a.seed, r0])
        log = open(f"{a.out}/log.jsonl", "a")
    elif a.start:
        centres = np.array(json.load(open(a.start))["centres"])
        log = open(f"{a.out}/log.jsonl", "w")
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
