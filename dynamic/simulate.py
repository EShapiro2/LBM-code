"""The dynamic case: serving the calls of a period with the cells moving as the load moves.

The load of a dispatcher is the calls of the last fifteen minutes in its cell. A call is served by the closest free car in the
caller's cell or an adjacent one; if there is none, a car is invented at the caller's location and counted. The car returns at
the drop-off when the ride ends. After each call, the dispatchers whose contentment the call changed take turns of the static
protocol, at zero time, until every dispatcher is content or no move is admissible; then the clock advances.

Rules of 2026-09-30 evening (Udi).
"""
import json, sys, os, time, argparse, heapq
import numpy as np
from shapely.geometry import Point, Polygon
from shapely import prepared
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static"))
import geometry as G
import protocol as P

WINDOW = 15 * 60          # the load is the calls of the last fifteen minutes
MAX_SWEEPS = 20           # sweeps of turns after an event before giving up on quiescence


def secs(ts):
    h, m, s = ts[11:19].split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def load_trips(path, T, city_prep, W, H):
    A, B, C, D = T["A"], T["B"], T["C"], T["D"]
    out = []
    for r in json.load(open(path)):
        try:
            plon, plat = float(r["pickup_longitude"]), float(r["pickup_latitude"])
            dlon, dlat = float(r["dropoff_longitude"]), float(r["dropoff_latitude"])
        except (KeyError, ValueError, TypeError):
            continue
        if plon == 0 or plat == 0:
            continue
        p = np.array([(A * plon + B) / 65535 * W, (C * plat + D) / 65535 * H])
        d = np.array([(A * dlon + B) / 65535 * W, (C * dlat + D) / 65535 * H]) if dlon != 0 and dlat != 0 else None
        out.append(dict(t=secs(r["pickup_datetime"]), p=p, te=secs(r["dropoff_datetime"]), d=d,
                        p_in=city_prep.contains(Point(p)), d_in=d is not None and city_prep.contains(Point(d))))
    return out


class Dynamic:
    def __init__(self, centres, city, rng):
        self.city = city; self.rng = rng
        self.window = []            # (t, p) of the calls of the last fifteen minutes
        self.free = []              # positions of free cars
        self.centres = np.array(centres, float)
        self.sim = None
        self.stats = dict(accepted=0, cut=0, halved=0, rejected=0, blocked=0, restarts=0, departure=0, departure_rejected=0, split=0, split_rejected=0, random=0, random_failed=0)
        self.metrics = dict(calls=0, served=0, invented=0, lost=0, dist=[], moves_per_call=[], events_with_moves=0, sweeps=[])

    def req(self):
        return np.array([p for t, p in self.window]) if self.window else np.zeros((0, 2))

    def rebuild(self):
        self.sim = P.Sim(self.centres, self.city, self.req(), self.rng)

    def slide(self, now):
        cut = now - WINDOW
        self.window = [(t, p) for t, p in self.window if t > cut]

    def cell_of(self, p):
        return int(np.argmin(((self.centres - p) ** 2).sum(1)))

    def serve(self, call):
        p = call["p"]
        cfg = self.sim.cfg
        i = self.cell_of(p)
        allowed = {i} | cfg.nb(i)
        best = None
        if self.free:
            F = np.array(self.free)
            owner = np.argmin(((F[:, None, :] - self.centres[None, :, :]) ** 2).sum(2), axis=1)
            cand = [k for k in range(len(F)) if owner[k] in allowed]
            if cand:
                d = [np.hypot(*(F[k] - p)) for k in cand]
                k = cand[int(np.argmin(d))]
                best = (k, min(d))
        if best is None:
            self.metrics["invented"] += 1
            dist = 0.0
        else:
            k, dist = best
            self.free.pop(k)
        self.metrics["served"] += 1
        self.metrics["dist"].append(float(dist))
        return dist

    def settle(self):
        """Turns of the static protocol at zero time until every dispatcher is content or nothing moves."""
        moves0 = self.stats["accepted"] + self.stats["departure"] + self.stats["split"]
        sweeps = 0
        for sweep in range(MAX_SWEEPS):
            sweeps += 1
            cfg = self.sim.cfg
            disc = [i for i in range(cfg.n) if not cfg.content(i) and self.sim.blocked.get(i) != "compact"]
            if not disc:
                break
            before = self.sim.cfg
            for i in self.rng.permutation(disc):
                self.sim.turn(int(i), self.stats)
            if self.sim.cfg is before:
                break
        self.centres = self.sim.cfg.c.copy()
        moves = self.stats["accepted"] + self.stats["departure"] + self.stats["split"] - moves0
        self.metrics["moves_per_call"].append(moves)
        self.metrics["sweeps"].append(sweeps)
        if moves:
            self.metrics["events_with_moves"] += 1

    def report(self, now):
        cfg = self.sim.cfg
        cont = sum(cfg.content(i) or self.sim.blocked.get(i) == "compact" for i in range(cfg.n))
        d = self.metrics["dist"]
        return dict(time="%02d:%02d:%02d" % (now // 3600, now % 3600 // 60, now % 60), calls=self.metrics["calls"], invented=self.metrics["invented"], lost=self.metrics["lost"],
                    free_cars=len(self.free), window=len(self.window), content=int(cont), min_load=int(cfg.load.min()), max_load=int(cfg.load.max()),
                    mean_dist_km=round(float(np.mean(d)), 3) if d else None, p90_dist_km=round(float(np.percentile(d, 90)), 3) if d else None,
                    moves=self.stats["accepted"], departures=self.stats["departure"], splits=self.stats["split"], events_with_moves=self.metrics["events_with_moves"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default="../inputs")
    ap.add_argument("--start-state", default="../static/runs/run15/state.json")
    ap.add_argument("--from", dest="t0", default="08:15:00")
    ap.add_argument("--to", dest="t1", default="08:30:00")
    ap.add_argument("--out", default="runs/dyn1")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    city = G.load_city(f"{a.inputs}/manhattan_main_island_km.json")
    cp = prepared.prep(city)
    T = json.load(open(f"{a.inputs}/transform_lonlat_to_km.json")); W, H = T["W_km"], T["H_km"]
    t0, t1 = secs("2015-01-15T" + a.t0), secs("2015-01-15T" + a.t1)
    early = load_trips(f"{a.inputs}/source/lbm-trips-0800-0815.json", T, cp, W, H)
    later = load_trips(f"{a.inputs}/source/lbm-trips-0815-0900.json", T, cp, W, H)
    ended = load_trips(f"{a.inputs}/source/lbm-dropoffs-0800-0815.json", T, cp, W, H)
    rng = np.random.default_rng(a.seed)
    dyn = Dynamic(json.load(open(a.start_state))["centres"], city, rng)
    # the window at the start: the calls of the last fifteen minutes on the island
    dyn.window = [(r["t"], r["p"]) for r in early if r["p_in"] and t0 - WINDOW < r["t"] <= t0]
    # the cars at the start: the rides that ended in the last fifteen minutes, on the island
    dyn.free = [r["d"] for r in ended if r["d_in"] and t0 - WINDOW <= r["te"] < t0]
    # rides in progress at the start: cars that will appear when they end
    events = []
    for r in early + later:
        if r["t"] < t0 and r["te"] >= t0 and r["d_in"] and r["te"] < t1:
            heapq.heappush(events, (r["te"], 0, "return", r["d"]))
    calls = sorted([r for r in early + later if r["p_in"] and t0 <= r["t"] < t1], key=lambda r: r["t"])
    for k, r in enumerate(calls):
        heapq.heappush(events, (r["t"], 1, "call", r))
    dyn.rebuild()
    log = open(f"{a.out}/log.jsonl", "w")
    rep = dyn.report(t0); print(json.dumps(rep), flush=True); log.write(json.dumps(rep) + "\n")
    P.render(dyn.sim, f"{a.out}/start.png", f"{a.t0}: {rep['content']} content, loads {rep['min_load']}-{rep['max_load']}, {rep['free_cars']} free cars")
    n = 0; tstart = time.time(); now = t0
    while events:
        now, _, kind, x = heapq.heappop(events)
        if kind == "return":
            dyn.free.append(x)
            continue
        r = x
        dyn.metrics["calls"] += 1
        dyn.slide(now)
        dyn.window.append((r["t"], r["p"]))
        dyn.rebuild()
        dyn.serve(r)
        if r["d_in"] and r["te"] < t1:
            heapq.heappush(events, (r["te"], 0, "return", r["d"]))
        elif not r["d_in"]:
            dyn.metrics["lost"] += 1
        dyn.settle()
        n += 1
        if n % 200 == 0:
            rep = dyn.report(now); rep["secs"] = round(time.time() - tstart, 1); print(json.dumps(rep), flush=True); log.write(json.dumps(rep) + "\n"); log.flush()
            json.dump(dict(time=now, centres=dyn.centres.tolist()), open(f"{a.out}/state.json", "w"))
    rep = dyn.report(now); rep["secs"] = round(time.time() - tstart, 1); print(json.dumps(rep), flush=True); log.write(json.dumps(rep) + "\n"); log.close()
    json.dump(dict(time=now, centres=dyn.centres.tolist(), metrics={k: v for k, v in dyn.metrics.items() if k not in ("dist", "moves_per_call", "sweeps")},
                   dist_mean=float(np.mean(dyn.metrics["dist"])), dist_p50=float(np.median(dyn.metrics["dist"])), dist_p90=float(np.percentile(dyn.metrics["dist"], 90)),
                   moves_total=int(sum(dyn.metrics["moves_per_call"]))), open(f"{a.out}/final.json", "w"), indent=1)
    P.render(dyn.sim, f"{a.out}/final.png", f"{a.t1}: {rep['content']} content, loads {rep['min_load']}-{rep['max_load']}, {rep['free_cars']} free cars")


if __name__ == "__main__":
    main()
