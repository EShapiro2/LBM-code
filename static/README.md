# static — simulation of the static protocol of LBM `sections/static.tex`

`protocol.py` runs the protocol on the inputs in `../inputs`: 100 dispatchers on a regular lattice, the 5,983 pickups on the main island, turns in a random order per round. Every quantity is computed exactly (Voronoi cells clipped to the island, loads by nearest centre, neighbours by shared edge of positive length, diameter and width of the convex hull). `geometry.py` holds the geometry.

Rules of 2026-09-30 afternoon (Udi): an empty dispatcher with a non-empty neighbour departs; the cells a split makes may have ratio up to 3 (`--reloc-ratio`); a rejected step is retried at s/2, s/4, s/8 (`--halvings`); after a failed departure or split, one random walk, which takes no time, and one more attempt in the same turn (`--rw-retries`). Under test: `--directions K` (scan K directions for the move and take the best decreasing one; 1 = toward the heaviest neighbour only), `--no-lookahead` (the walk looks only one hop), `--objective gap|squares` (the acceptance objective: sum of the neighbourhood mean gaps, or sum of squared loads of the cells that change), and the split by equal load rather than equal area.

Runs are in `runs/<name>/`: `log.jsonl` one line per round, `state.json` the centres and loads at the last round (resume with `--resume`), `round_NNN.png` maps. A run is executed in chunks of 170 s from the Cowork shell, resuming each time.

- `run1`: the paper's rules as written (2026-09-30, seed 1, 100 rounds).
- `run2`: `--empty-departs --rw-after 3`.
- `run3`: `--empty-departs --rw-after 3 --halvings 3 --reloc-ratio 3` (options of an earlier version).
- `run4`: the afternoon rules, move toward the heaviest neighbour, gap objective: stalls at gap 7 with 8 empty cells.
- `run5`: plus 16-direction scan, lookahead walk, equal-load split; gap objective: stalls at gap 7, 7 empty cells, loads 0-115.
- `run6`: plus `--objective squares`: empties gone by round 4; loads 3-88 at round 27, gap 4.7, still moving.
- `run7`: the rules adopted 2026-09-30 14:20 (squares objective, direction scan, equal-load split, blocked departure is content), plus two fixes found on the way: a cell already beyond the compactness bound does not block its neighbours' moves so long as it gets no worse, and the step lengths scanned are dist/2 ... dist/64 rather than a load-proportional step, which at small gaps moved no request. Round 47: no empty cell, loads 8-77 (the north strip 8 and 25, the rest 43-77), mean gap 2.5, 40 content; the rest are on a slope of 43 to 72 with neighbour gaps of 5-6%.
- `run8`: tolerance 10% (Udi, 14:48): stalled with a low region of ten cells (0-18) in the north whose walks ended at local maxima of 2.
- `run9`: plus walk restarts (a rejected host: restart from a random neighbour of it, up to 10 times in the turn): fixed point at round 16, 65 content, loads 13-76; 15 of the 35 discontent had an improving move only if their neighbours change.
- `run10`: plus moves that change the neighbours (objective over the old and new neighbourhood together), 32 directions x 7 lengths, colour scale white/light blue/yellow/orange/deep red with a bar (Udi, 15:02): 80 content by round 17 and hovering at 74-83; loads 46-76 outside the north strip (4, 23); mean gap 3.
- `run11`: from run10's state, departure at every local minimum and splitting at every local maximum (Udi, 15:18): diverged, 80 -> 42 content in 9 rounds; the random walks after the many rejected relocations scrambled the loads. Stopped.
- `run13`: no random walk; backtracking search along the walk (Udi, 15:25): the host, its neighbours, one step back, ... to the start; deterministic. From the lattice. Fixed point at round 16: 67 content, loads 14-74. The walk was on the loads after absorption, so it ended at the absorbing neighbour (a bug).
- `run14`: the walk on the loads before the departure. Fixed point at round 11: 58 content at 10%, loads 48-75 (ratio 1.56), no north strip (upper Manhattan is one cell of 61), mean gap 3.7, max gap 9.9. `final.png`.
