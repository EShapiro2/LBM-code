# Manhattan compact hexagon experiment handoff

Updated 27 September 2026 (cloud workspace). This is a recovered-source cloud copy. The Mac files have not been read, compared, or changed.

## Source provenance

- Supplemental protocol: complete Add-file record, chat `01a0e288-2186-7bf0-9df7-4ecf938cb3c6`, turn `01a0e446-20fc-7712-ab87-a13b33a6983a`; supplied verbatim in the supervising user message. Cloud file `compact_hexagon_protocol.tex`.
- Historical original note: complete Add-file record, chat `01a0ddd5-d823-78f3-8007-4e6affbc3f0b`, turn `01a0e248-be23-7c00-b6f6-8998d8156940`; originally `/Users/udi/Documents/Codex/2026-09-26/i-want-to-try-a-different/outputs/local_mesh_balancing.tex`. Supplied in user message and recovered into `local_mesh_balancing_recovered.tex`.
- Intended Mac comparison/writeback target: `/Users/udi/Grassroots/tmp/local_mesh_balancing.tex`. Its current contents are unknown. Compare before replacing; local writeback pending.
- Prepared Mac supplement path: `/Users/udi/Documents/Codex/2026-09-27/do-you-have-access-to-the/outputs/hexagon_simulation_protocol.tex`. Its current bytes are unknown.

## Completed cloud preflight

- Local desktop `/bin/sh`, Node and computer-control runtimes reportedly exited 134 after two app restarts. No further restart requested. Linux cloud `python3` and shell ran successfully; `pdflatex` installed.
- Merged the supplied supplement once before `\end{document}` in `local_mesh_balancing_merged_recovered.tex`; historical 100-vertex discussion retained. `pdflatex -halt-on-error` succeeded, producing an eight-page PDF. The new 100-cell protocol supersedes the historical 100-vertex experiment as the current task.
- Recovered `Manhattan_Project_Files.zip` from Library. Nested `Manhattan_Balanced_Hexagons.zip` includes `local_anneal.cpp`, `start.txt`, `start.json`, `balanced.json`, `geometry.json`, `history.json`, `audit_solution.py`, README, replay. This is the historical 38-cell solver, not a 100-cell implementation. `geometry.json` has 107 vertices, 38 cells, 5986 points and a 38-point outline. `Manhattan_100_Balanced_Disks.zip` has 5986 points and a 38-point outline, but is a different disk model.
- Historical `local_anneal.cpp` uses shuffled vertex order, 24 local proposals per activation, moving root and edge neighbors; affected cells evaluated atomically. Geometric rejection checks strict convexity, area >=2% initial, shape score 4πA/P² >=0.20, boundary simplicity and shoreline coverage. Acceptance uses affected-cell squared-count energy and temperature `alpha * sum(gap²)`, with `alpha=.005` in documented reproduction. A historical newer record reports repair seed 7, balance seed 17, alpha .02, but its exact code and full boundary were not recovered here. Do not silently equate the two variants.
- A separate `transfer.json` records a 38-cell run on 5983 inside pickups with outside indices 309,4705,5212; input SHA256 `eabfaa334493582b9f407956134e408fb066ba9d0ee3ca8c78bb737b6dc77f77`, km boundary SHA256 `ae10c1484a54894062bebfaf571df4e635a428695c2ef6d674a894894f5d7326`, source boundary SHA256 `361ac589847bee86f45179afddef98304ca05f7b04650924873b58d09f8be39f`. These are historical assertions; matching original files have not been located and hashes have not been independently verified.
- Process check found no verified current solver corresponding to historical PID 105627/session 44581. No 100-cell solver launched. `historical_38_cell_transfer_test.svg` is a deliberately labeled snapshot transfer test, not an initial 100-cell map.

## Current 100-cell requirements

Exactly 100 convex shared-vertex underlying hexagons; clipped regions positive area, full Manhattan main-island coverage with hole retained and no positive-area overlap; 5983 inside pickups assigned exactly once, three outside flagged. Diameter/minimum projection width <=2 for every underlying and clipped cell. Neighbors share positive-length service border. Empty-load handling and median-of-local-median percentage gap are specified in the supplement. Successful stop only at first completed balancing round with M<=5%. Median is termination only; preserve original compact-cell movement/acceptance. Per-minute timestamped maps and counters, audited initial map, atomic exact-resume checkpoints, bounded interruptible batches and tested Stop control required before full launch.

## Exact blocker and next action

The recovered 38-cell code implements the 4πA/P² floor, not the new diameter/width limit on both underlying and clipped regions; it models only a 38-point outline, not the verified full-resolution NYC DCP26b boundary with hole. The archived exact source for the later 38-cell repair/balance variant and its original input/boundary files (hashes above), plus a valid 100-cell seed or documented construction/repair procedure, remain missing. Locate those in project history or Library. Then implement the new constraints and resumable control without changing original proposals/acceptance, audit a 100-cell initialization, run a short stop/resume and snapshot-transfer test, show initial map, and only then launch a monitored solver. Do not invent a replacement source, claim a 38-cell map is the 100-cell initial map, or leave an unmonitored background process.
