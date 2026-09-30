# 100-turn center relocation batch

Open animation.html offline for before/after playback with 0.1–1 s adjustable pause, scrubber, and label selection. animation.mp4 is a fixed 0.5 s/turn preview. Labels display modeled after-weights; final_map.png uses refreshed snapshot counts.

The source starts from the saved end-round59 state. Selection is badness-weighted with replacement; 100 selections do not guarantee a turn for each center. Qualifying selections complete the whole depart-route-insert operation in one turn. Others retain ordinary combined-grade movement.

Dependency requirements: Python, NumPy, SciPy, Shapely >=2.1, Matplotlib, FFmpeg (video only). From the extracted root: python3 work/voronoi_migrate100/verify.py verifies the saved batch; python3 work/voronoi_migrate100/render.py rebuilds its animation. The saved run is already complete; run.py --until 100 does not rerun it.

See manifest.json for the local rules, density-transfer conventions, tolerances and source hashes. This is a sequential geometry simulation, not a concurrent distributed implementation. No convergence claim.
