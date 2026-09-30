# Manhattan: exact balance with a local atomic hexagon rule

Verified on the original 5,986 pickups from 8:00–8:15, with 38 hexagons.

## Result

- 20 hexagons contain 158 pickups; 18 contain 157.
- Population variance: 0.2493074792243767, the smallest possible for these integer counts.
- Every pickup belongs to exactly one cell.
- Every cell is a strictly convex, six-sided polygon.
- Pairwise cell overlap area: zero in the independent clipping audit.
- All of the supplied Manhattan polygon is covered, within floating-point tolerance (uncovered area about 1.3e-13 square kilometres).
- Minimum shape score 4πA/P²: 0.2021501855; required minimum 0.20.
- Hexagons extend offshore. Their intersection with Manhattan need not have six sides.
- The comparison K-means + merging result has variance approximately 1,374. It was not designed to minimize this same exact-balance objective.

The final result was independently checked by reconstructing every pickup's membership, intersecting every cell pair, triangulating Manhattan and clipping its triangles against all cells. See `verification.json` and `audit_solution.py`.

## Open the result

Open `Replay.html` in a browser. It starts at the final map. Use the slider or Play button to inspect the 162-round recorded run. “Show complete hexagons offshore” displays all six sides, including water areas. This page replays saved states; it does not execute a new optimization.

`comparison.png` shows both methods on the same pickups.

## Reproduce the search

A C++17 compiler is required:

```sh
sh run.sh
```

Equivalent commands:

```sh
g++ -O3 -std=c++17 local_anneal.cpp -o local_anneal
./local_anneal start.txt reproduced.json 500 0.20 0.005 11
```

Arguments are input, best-output filename, maximum rounds, shape floor, local-temperature coefficient, and random seed. The tested environment reached exact balance at round 162, and a fresh replay reproduced the saved vertex coordinates and counts. C++ standard-library normal random generators may differ across platforms, so the same seed is not a cross-platform bit-for-bit guarantee. `balanced.json` preserves the verified result.

To rerun the independent audit (Python standard library only):

```sh
python3 audit_solution.py
```

The audit verifies the included `balanced.json`. The search creates `reproduced.json` and `reproduced.json.last.json`.

## Local rule

1. Activate every mesh vertex once per round, in a random permutation. Boundary vertices can move.
2. An active vertex proposes an atomic displacement of itself and its edge-neighbours: four vertices at an interior junction, fewer at some boundary junctions. Evaluate every cell incident to those vertices, normally six for an interior patch.
3. Try 24 proposals in that activation. Proposal types mix single-vertex, correlated and independently directed displacements. Scales are sampled logarithmically from 0.0008 to 0.45 times the initial hexagon side.
4. Two proposal types move vertices toward the nearest pickup to an underfilled cell's vertex-average centre, using only pickups in the affected cells. This guides empty offshore cells toward data; it does not change the count objective.
5. Let L=157 and U=158. For affected cell c with population n_c, define g_c=max(L-n_c, 0, n_c-U). Set T=0.005 times the sum of g_c² over the affected cells. There is no heating or cooling schedule.
6. Evaluate E=sum(n_c²) over the affected cells. Accept a feasible proposal if it does not increase E; otherwise accept with probability exp(-(E_new-E_old)/T). A patch with T=0 does not move.
7. Feasibility requires strict convexity, area at least 2% of initial area, shape score at least 0.20, no lost pickups, a simple outer boundary, and complete shoreline coverage. Changes to coordinates and pickup ownership are committed together. Equal-score moves undergo the same feasibility checks.

Because every pickup remains in one cell, minimizing the sum of squared counts is equivalent to minimizing variance. For 5,986=38×157+20 pickups, the integer optimum has 20 counts of 158 and 18 counts of 157. Its variance is 20×18/38².

## Scope and provenance

This is a serial simulation of local atomic agent moves. Its population objective, temperature and data-directed proposals use only the affected cells. The current feasibility implementation scans the full mesh boundary and modeled shoreline for boundary moves; it is not yet a fully distributed collision/coverage protocol. Concurrent execution would also need atomic conflict handling between overlapping patches.

This run demonstrates attainment of the optimum for this data and saved starting map. It does not establish convergence for all inputs, and does not establish adaptation performance on moving pickups.

The search continued from the earlier work, but a stronger audit found overlapping outer edges in an earlier saved map. That invalid geometry was repaired before the valid search. The enclosed `start.txt` is the valid, audited continuation state with variance 670.8282548 and one empty offshore cell. The final guided phase shown in the replay begins there. The shape bound was relaxed from the earlier 0.35 to 0.20. All final claims concern the audited result, not the invalid intermediate maps.

Files: `start.txt` and `start.json` are the continuation state; `balanced.json` is the optimum; `geometry.json` supplies the topology, points, modeled outline and final coordinates; `history.json` contains rounds 0–162; `local_anneal.cpp` is the runner.
