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
