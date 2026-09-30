# Center relocation batch — completed

100 selections from saved end round59, before weighted selection. 19 depart-insert transactions, 57 ordinary accepted moves, 24 unchanged turns. Original runs untouched. Final checkpoint is final.json and checkpoint.json, completed=100. No solver remains running.

Departure: strict local minimum and W < d/(d+1) neighbor median. A complete departure-route-insertion is one turn. Routing is one-hop uphill on frozen post-deletion weights; sequential execution avoids concurrent changes. Geometric covariance/equal-area/centroid insertion has no numerical optimization. Ordinary moves retain the prior combined-grade numerical method. Weight transport for relocation uses frozen spatial density intersections; pickups refresh next selection only. See manifest.json for precise conventions.

Control test stopped without advancing, then resumed to exactly the same centers and RNG as uninterrupted two-turn execution. All 100 host polygons passed analytical equal-area tests. Final verifier replayed selection RNG, triggers and all 19 relocations. Every turn audited coverage, overlap, distinct sites, in-region centers, convexity, adjacency, and assignment count. Ordinary numerical path searches were not independently repeated.

Outputs: animation.html (offline, controllable 0.1–1 second delay), animation.mp4 (before/after each turn), per-turn JSON, summary.json, validation files, final map and checkpoint. Current batch is finite completion, not convergence. Do not restart or continue without the user's next instruction.
