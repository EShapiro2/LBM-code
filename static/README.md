# static — simulation of the static protocol of LBM `sections/static.tex`

`protocol.py` runs the protocol on the inputs in `../inputs`: 100 dispatchers on a regular lattice, the 5,983 pickups on the main island, turns in a random order per round. Every quantity is computed exactly (Voronoi cells clipped to the island, loads by nearest centre, neighbours by shared edge of positive length, diameter and width of the convex hull). `geometry.py` holds the geometry.

Options beyond the paper, off by default: `--empty-departs` (an empty dispatcher is not content and departs, walking across a plateau), `--rw-after N` (random walk only after N consecutive failed turns), `--halvings K` (try s/2, s/4, ... when the proposed step is rejected), `--reloc-ratio R` (compactness bound applied to the cells after a departure or split).

Runs are in `runs/<name>/`: `log.jsonl` one line per round, `state.json` the centres and loads at the last round (resume with `--resume`), `round_NNN.png` maps. A run is executed in chunks of 170 s from the Cowork shell, resuming each time.

- `run1`: the paper's rules as written (2026-09-30, seed 1, 100 rounds).
- `run2`: `--empty-departs --rw-after 3`.
- `run3`: `--empty-departs --rw-after 3 --halvings 3 --reloc-ratio 3`.
