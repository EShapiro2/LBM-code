# Continuation: rounds 26–50

This is an exact continuation of the completed 25-round local Voronoi trial. `run.py` and frozen input are unchanged. The saved round-25 centers and PCG64 state were loaded; the original seed was not reset. All completed checkpoints 0–50 and all 5,000 step logs are retained. Old hexagon runs and the previously delivered Voronoi25 bundle were not changed.

See `outputs/voronoi50/summary.json` for continuation statistics (rounds 26–50 only), initial=round25, final=round50, and original_initial=round0. Validation covers all 51 checkpoints, all 5,000 transitions and all 50 permutations. Independent bisector adjacency is checked at rounds0,25,50. The 51-record measures.csv/json and plots cover rounds0–50; the before/after map compares rounds25 and50 on equal axes.

`python3 work/voronoi25/verify50.py` recomputes the validation. `python3 work/voronoi25/render50.py` renders these outputs. Stop/resume behavior and geometric tolerances remain as documented in README.md. The existing latest checkpoint is round50: running `run.py run --until 50` again does not repeat rounds. To reproduce from round25, work in a separate copy, set latest.json to checkpoint_25.json, retain only steps with round<=25 in steps.jsonl, remove any partial.json, then run through50. Preserve the original bundle while doing so.

Completion at round50 is a fixed-budget endpoint, not convergence. No future round is started automatically.
