"""The dynamic case: serving the calls of a period with the cells moving as the load moves.

The load of a dispatcher is the calls of the last fifteen minutes in its cell.  A call is served by the closest free car in the
caller's cell or an adjacent one; if there is none, a car is invented at the caller's location and counted.  The car returns
at the drop-off when the ride ends.  A dispatcher takes a turn of the static protocol, at zero time, when it is discontent and
its own load or a neighbour's has changed since its last turn --- by a call arriving or expiring, or by a neighbour's step ---
until no woken dispatcher has an admissible step (quiescence); then the clock advances to the next call.

Initial cars: one car per call of the preparatory segment, the fifteen minutes before the start, placed at the call and riding
to its drop-off; at the start it is free at the drop-off if the ride has ended on the island, and returns when it ends
otherwise.  Invented cars are counted from the start.

Rules of 2026-09-30 (Udi, in discussion with LBM #1 and LBM #2); the design is in LBM/docs/decisions.md.
"""
import json, sys, os, time, argparse, heapq
import numpy as np
from shapely.geometry import Point
from shapely import prepared

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static"))
import geometry as G
import protocol as P

WINDOW = 15 * 60          # the load is the calls of the last fifteen minutes
MAX_SWEEPS = 50           # sweeps of turns after a call before giving up on quiescence
STATS = ("accepted", "cut", "halved", "rejected", "blocked", "restarts", "departure", "departure_rejected", "split", "split_rejected", "random", "random_failed")


def secs(ts):
    h, m, s = ts[11:19].split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def hms(t):
    return "%02d:%02d:%02d" % (t // 3600, t % 3600 // 60, t % 60)


def load_trips(path, T, city_prep, W, H):
    """The rides of a source file in the simulator's kilometre frame: t and p the pickup, te and d the drop-off."""
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
        p = [(A * plon + B) / 65535 * W, (C * plat + D) / 65535 * H]
        d = [(A * dlon + B) / 65535 * W, (C * dlat + D) / 65535 * H] if dlon != 0 and dlat != 0 else None
        out.append(dict(t=secs(r["pickup_datetime"]), p=p, te=secs(r["dropoff_datetime"]), d=d,
                        p_in=bool(city_prep.contains(Point(p))), d_in=bool(d is not None and city_prep.contains(Point(d)))))
    return out


class Dynamic:
    def __init__(self, centres, city, rng):
        self.city = city; self.rng = rng
        self.window = []            # [t, x, y] of the calls of the last fifteen minutes
        self.free = []              # [x, y] of the free cars
        self.returns = []           # heap of (te, x, y): cars in a ride, returning at the drop-off
        self.pending = set()        # dispatchers woken since their last turn
        self.sim = P.Sim(np.array(centres, float), city, np.zeros((0, 2)), rng)
        self.stats = {k: 0 for k in STATS}
        self.metrics = dict(calls=0, invented=0, lost=0, events_with_moves=0, quiescent=0, capped=0, turns=0, woken=0)
        self.dist = []              # pickup distance of every served call
        self.calls_log = []         # per-call records not yet written

    # ---- the load ----
    def req(self):
        return np.array([[x, y] for t, x, y in self.window]) if self.window else np.zeros((0, 2))

    def rebuild(self):
        """The configuration with the current window; wakes the dispatchers whose load or neighbourhood changed."""
        old = self.sim.cfg
        self.sim.req = self.req()
        self.sim.cfg = self.sim.make(old.c); self.sim.cfg.adopt()
        self.wake(old, self.sim.cfg)

    def wake(self, old, new):
        changed = [i for i in range(new.n) if int(old.load[i]) != int(new.load[i]) or old.nb(i) != new.nb(i)]
        for i in changed:
            self.pending.add(i)
            self.pending |= old.nb(i) | new.nb(i)

    def slide(self, now):
        cut = now - WINDOW
        self.window = [w for w in self.window if w[0] > cut]

    # ---- the cars ----
    def cell_of(self, p):
        return int(np.argmin(((self.sim.cfg.c - p) ** 2).sum(1)))

    def serve(self, p):
        """The closest free car in the caller's cell or an adjacent one takes the call; none: a car is invented.  Returns the pickup distance, or None."""
        cfg = self.sim.cfg
        p = np.asarray(p, float)
        i = self.cell_of(p)
        allowed = {i} | cfg.nb(i)
        if self.free:
            F = np.array(self.free)
            owner = np.argmin(((F[:, None, :] - cfg.c[None, :, :]) ** 2).sum(2), axis=1)
            cand = np.flatnonzero(np.isin(owner, list(allowed)))
            if len(cand):
                d = np.hypot(*(F[cand] - p).T)
                j = int(np.argmin(d)); k = int(cand[j])
                self.free.pop(k)
                return float(d[j])
        self.metrics["invented"] += 1
        return None

    def do_returns(self, now):
        while self.returns and self.returns[0][0] <= now:
            te, x, y = heapq.heappop(self.returns)
            self.free.append([x, y])

    # ---- the protocol ----
    def settle(self):
        """Turns of the static protocol, at zero time, by the woken dispatchers, until none is woken or the cap is reached."""
        s0 = {k: self.stats[k] for k in ("accepted", "departure", "split")}
        sweeps = 0; turns = 0; woken = 0
        while self.pending and sweeps < MAX_SWEEPS:
            sweeps += 1
            batch = sorted(self.pending); self.pending = set()
            woken += len(batch)
            for idx in self.rng.permutation(len(batch)):
                i = int(batch[idx])
                cfg = self.sim.cfg
                if cfg.content(i):
                    continue
                turns += 1
                self.sim.blocked.pop(i, None)
                self.sim.turn(i, self.stats)
                if self.sim.cfg is not cfg:
                    self.wake(cfg, self.sim.cfg)
        quiescent = not self.pending
        self.pending = set()
        moves = {k: self.stats[k] - s0[k] for k in s0}
        self.metrics["turns"] += turns; self.metrics["woken"] += woken
        if sum(moves.values()):
            self.metrics["events_with_moves"] += 1
        if quiescent:
            self.metrics["quiescent"] += 1
        else:
            self.metrics["capped"] += 1
        return moves, sweeps, turns, woken, quiescent

    def content(self):
        cfg = self.sim.cfg
        return int(sum(cfg.content(i) or self.sim.blocked.get(i) == "compact" for i in range(cfg.n)))

    # ---- one call ----
    def call(self, r):
        now = r["t"]
        self.do_returns(now)
        self.metrics["calls"] += 1
        self.slide(now)
        self.window.append([now, r["p"][0], r["p"][1]])
        self.rebuild()
        cell = self.cell_of(r["p"])
        dist = self.serve(r["p"])
        if dist is not None:
            self.dist.append(dist)
        if r["d_in"]:
            heapq.heappush(self.returns, (r["te"], r["d"][0], r["d"][1]))
        else:
            self.metrics["lost"] += 1
        moves, sweeps, turns, woken, quiescent = self.settle()
        self.calls_log.append(dict(t=hms(now), cell=cell, dist=None if dist is None else round(dist, 4), invented=dist is None,
                                   moves=moves["accepted"], departures=moves["departure"], splits=moves["split"],
                                   sweeps=sweeps, turns=turns, woken=woken, quiescent=quiescent, content=self.content(),
                                   free=len(self.free), min_load=int(self.sim.cfg.load.min()), max_load=int(self.sim.cfg.load.max())))

    # ---- reporting, checkpoints ----
    def report(self, now):
        cfg = self.sim.cfg
        rep = dict(time=hms(now), calls=self.metrics["calls"], invented=self.metrics["invented"], lost=self.metrics["lost"],
                   free_cars=len(self.free), cars_in_ride=len(self.returns), window=len(self.window), content=self.content(),
                   min_load=int(cfg.load.min()), max_load=int(cfg.load.max()),
                   quiescent=self.metrics["quiescent"], capped=self.metrics["capped"], events_with_moves=self.metrics["events_with_moves"],
                   moves=self.stats["accepted"], departures=self.stats["departure"], splits=self.stats["split"],
                   turns=self.metrics["turns"], woken=self.metrics["woken"])
        if self.dist:
            d = np.array(self.dist)
            rep.update(mean_dist_km=round(float(d.mean()), 3), p50_dist_km=round(float(np.median(d)), 3), p90_dist_km=round(float(np.percentile(d, 90)), 3))
        return rep

    def state(self, now, k):
        return dict(time=now, next_call=k, centres=self.sim.cfg.c.tolist(), window=self.window, free=self.free, returns=sorted(self.returns),
                    stats=self.stats, metrics=self.metrics, dist=self.dist, rng=self.rng.bit_generator.state)

    def restore(self, s):
        self.window = s["window"]; self.free = s["free"]; self.returns = [tuple(x) for x in s["returns"]]; heapq.heapify(self.returns)
        self.stats = s["stats"]; self.metrics = s["metrics"]; self.dist = s["dist"]
        self.rng.bit_generator.state = s["rng"]
        self.sim.req = self.req(); self.sim.cfg = self.sim.make(np.array(s["centres"], float)); self.sim.cfg.adopt()
        return s["time"], s["next_call"]


def write_json(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default="../inputs")
    ap.add_argument("--start-state", default="../static/runs/run15/state.json")
    ap.add_argument("--from", dest="t0", default="08:15:00")
    ap.add_argument("--to", dest="t1", default="09:00:00")
    ap.add_argument("--out", default="runs/dyn1")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--checkpoint", type=int, default=500, help="calls between checkpoints (log line, map, state)")
    ap.add_argument("--max-calls", type=int, default=0, help="stop after this many calls in this invocation (0: run to --to)")
    ap.add_argument("--resume", action="store_true", help="continue from <out>/state.json")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    city = G.load_city(f"{a.inputs}/manhattan_main_island_km.json")
    cp = prepared.prep(city)
    T = json.load(open(f"{a.inputs}/transform_lonlat_to_km.json")); W, H = T["W_km"], T["H_km"]
    t0, t1 = secs("2015-01-15T" + a.t0), secs("2015-01-15T" + a.t1)
    early = load_trips(f"{a.inputs}/source/lbm-trips-0800-0815.json", T, cp, W, H)
    later = load_trips(f"{a.inputs}/source/lbm-trips-0815-0900.json", T, cp, W, H)
    rides = early + later
    calls = sorted([r for r in rides if r["p_in"] and t0 <= r["t"] < t1], key=lambda r: r["t"])
    rng = np.random.default_rng(a.seed)
    dyn = Dynamic(json.load(open(a.start_state))["centres"], city, rng)
    if a.resume and os.path.exists(f"{a.out}/state.json"):
        now, k = dyn.restore(json.load(open(f"{a.out}/state.json")))
        log = open(f"{a.out}/log.jsonl", "a"); calls_log = open(f"{a.out}/calls.jsonl", "a")
        print(f"resumed at {hms(now)}, call {k}", flush=True)
    else:
        now, k = t0, 0
        # the window at the start: the calls of the preparatory segment on the island
        dyn.window = [[r["t"], r["p"][0], r["p"][1]] for r in rides if r["p_in"] and t0 - WINDOW < r["t"] < t0]
        # the cars at the start: one per call of the preparatory segment, free at its drop-off if the ride has ended on the island, returning when it ends otherwise
        for r in rides:
            if r["p_in"] and t0 - WINDOW <= r["t"] < t0 and r["d_in"]:
                if r["te"] < t0:
                    dyn.free.append(r["d"])
                else:
                    heapq.heappush(dyn.returns, (r["te"], r["d"][0], r["d"][1]))
        dyn.sim.req = dyn.req(); dyn.sim.cfg = dyn.sim.make(dyn.sim.cfg.c); dyn.sim.cfg.adopt()
        log = open(f"{a.out}/log.jsonl", "w"); calls_log = open(f"{a.out}/calls.jsonl", "w")
        rep = dyn.report(t0); rep["secs"] = 0.0; print(json.dumps(rep), flush=True); log.write(json.dumps(rep) + "\n"); log.flush()
        P.render(dyn.sim, f"{a.out}/ckpt_{a.t0.replace(':', '')}.png", f"{a.t0}: {rep['content']} content, loads {rep['min_load']}-{rep['max_load']}, {rep['free_cars']} free cars", cars=np.array(dyn.free))
        write_json(dyn.state(now, k), f"{a.out}/state.json")
    tstart = time.time(); done = 0; tck = time.time()
    while k < len(calls):
        dyn.call(calls[k]); now = calls[k]["t"]; k += 1; done += 1
        if k % a.checkpoint == 0 or k == len(calls) or done == a.max_calls:
            rep = dyn.report(now); rep["secs"] = round(time.time() - tstart, 1); rep["secs_per_call"] = round((time.time() - tck) / a.checkpoint, 2); tck = time.time()
            print(json.dumps(rep), flush=True); log.write(json.dumps(rep) + "\n"); log.flush()
            for c in dyn.calls_log:
                calls_log.write(json.dumps(c) + "\n")
            dyn.calls_log = []; calls_log.flush()
            P.render(dyn.sim, f"{a.out}/ckpt_{hms(now).replace(':', '')}.png", f"{hms(now)}: {rep['content']} content, loads {rep['min_load']}-{rep['max_load']}, {rep['free_cars']} free cars, {rep['invented']} invented", cars=np.array(dyn.free))
            write_json(dyn.state(now, k), f"{a.out}/state.json")
        if done == a.max_calls:
            break
    log.close(); calls_log.close()
    if k == len(calls):
        print("DONE", flush=True)


if __name__ == "__main__":
    main()
