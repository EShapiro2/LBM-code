from pathlib import Path
p=Path('outputs/local_mesh_balancing_merged_recovered.tex')
s=p.read_text()
s=s.replace('The latter\nsection documents', 'The latter\nsection documents')
s=s.replace('Manhattan run, which was manually stopped without reaching its termination target.', 'Manhattan run, which was manually stopped without reaching its termination target.\nSections~\\ref{sec:method-catalog}--\\ref{sec:source-catalog} add the recovered\nexperimental alternatives, including Manhattan tests performed after the historical\nvertex discussion. Historical statements that Manhattan had not yet been tested\napply to that earlier discussion, not to the entire updated record.')
append=r'''
\clearpage
\section{Recovered alternatives: scope and comparison rules}
\label{sec:method-catalog}
This catalog spells out the alternatives identified in the recovered discussions,
source programs, saved results, and archive notes. It is a retrospective review;
no experiment was restarted to prepare it. ``Implemented'' means source was
recovered; ``executed'' requires a saved result or an explicit archived execution
record. A proposed method without a complete rule is identified as such.
These are not interchangeable versions of one experiment.

\paragraph{Three different objects carry load.}
In a cell partition, a pickup belongs to one geographic cell. In a vertex method,
it belongs to one agent whose stored location need not be its globally nearest
location after local updates. In overlapping disks, a covered pickup usually
splits its unit load equally among every covering disk. Covering all sampled
points with disks does not cover every location in Manhattan.

\paragraph{Metrics.}
For $K$ agents and conserved total load $N$, let $t=N/K$ and
$\mathrm{CV}=\operatorname{sd}(L)/t$. Tables below express CV as a percentage.
Worst error means $\max_i|L_i/t-1|$. Operational RMS uses the assigned agent's
position; centroid RMS replaces it by the centroid of its assigned pickups.
These distances must not be mixed. Where coverage is lost, an RMS deviation
from $t$ is not the same as CV around the remaining mean load.
The older shape score $4\pi A/P^2$ is also not the current diameter/minimum-width
ratio. A good score under one definition does not certify the other.

\begin{longtable}{p{.36\linewidth}p{.55\linewidth}}
\toprule Family & Recovered status and stopping interpretation\\\midrule
\endhead
Recursive clustering and merging & Implemented; saved 38-region comparison.\\
Pressure-driven and greedy hexagons & Implemented interactive alternatives; no new execution here.\\
Coordinated hexagon annealing & Executed: older 38-cell exact load target; later compact 38-cell median target; 100-cell run manually stopped.\\
Disk initialization and local heat & Executed fixed-budget tests; best snapshots distinguished from terminal states.\\
Disk sleep/wake & Executed 100-disk tolerance termination.\\
Self-Pareto and neighbor-harm disk rules & Executed fixed-budget tests, not balanced at termination.\\
Nearest-center fallback disks & Executed fixed-budget tests with uncovered points assigned externally.\\
Vertex Rules 2 and 3; Lloyd variants & Executed synthetic and Manhattan comparisons, with distinct stopping criteria.\\
All-movable Rule 2 & Executed, manually stopped after severe collapse.\\
Driver disks and ride allocation & Different data; static disk tests and global dispatch executed; local dispatch remained a prototype.\\
Lifted triangle, optional objectives, Delaunay & Discussed; incomplete or unexecuted alternatives identified below.\\
\bottomrule
\end{longtable}

\section{Clustering and geographic-cell alternatives}
\subsection{Recursive k-means followed by mutual-neighbor merging}
\textbf{Implemented and represented in the saved 38-region comparison.}
A region with more than $T$ pickups is recursively split into $k$ children.
K-means++ chooses its first center randomly and later centers with probability
proportional to the squared distance to the nearest chosen center. There cannot
be more centers than points. Lloyd iterations assign points to their nearest
child and replace nonempty child centers by their point centroids. Each split
stops when assignments stabilize or after 80 iterations. Empty children are
removed; a split leaving one nonempty child above $T$ is marked unsplittable.
The child service polygons are Voronoi cells clipped to the parent polygon.
The retained tree can route a new point by nearest-child descent.

Merging operates on adjacent leaf groups. A group's representative is the
pickup-count-weighted mean of its leaf centroids. Each group chooses its nearest
adjacent group whose combined load is at most $T'$, resolving equal distances
by lower identifier. All mutual choices merge in one round. Their polygons are
united and adjacency is updated. Stop when no pair is available; if a legal pair
exists but no mutual pair is found, report a stalled state. The resulting
connected unions need not be hexagons or compact under the later shape rule.

The saved 5,986-pickup, 38-group comparison has variance 1,373.775623,
CV 23.5291\%, loads 88--200, and centroid RMS 0.446803 km.
The exact seed and split/merge settings of that saved comparison were not
established from its result record; these numbers therefore do not define a
fully specified rerun. The interactive serving-cost display uses the nearest
retained leaf center within a group, which is a different distance statistic.

\subsection{Original pressure-driven shared-corner hexagons}
\textbf{Implemented in the original interactive program.}
For a movable interior vertex $v$ incident to three cells, let $n_i$ be their
loads, $\bar n$ their mean, and $q_i$ their polygon area centroids. Form
\[
 F=\sum_{i=1}^3(n_i-\bar n)\frac{q_i-v}{\|q_i-v\|},\qquad
 v'=v+\eta\frac{F}{\max(1,\|F\|)}.
\]
The implementation tries successively the full displacement and factors
$1/2,1/4,1/8$, accepting the first geometrically valid move. Validity here means
simple affected polygons and area above a configured fraction of initial area.
It is not the later convexity/compactness test. Boundary vertices are fixed.
The affected pickups are reassigned locally after a move. There is no
load-energy acceptance test, so a valid move may worsen load variance.
A sweep makes as many random activations, with replacement, as there are
movable vertices. It does not visit each vertex exactly once.
The interactive live mode uses a 900-second window, advances 20 seconds, and
cycles its start through 2,700 seconds; the frozen comparison uses the first
15 minutes. Run-specific slider settings and a separate quantitative terminal
result were not recovered sufficiently to assert a benchmark for this rule.

\subsection{Greedy single-corner hexagons}
\textbf{Implemented in the modified interactive program.}
Boundary vertices remain fixed. Each sweep shuffles the interior vertices and
visits each once. For an activated corner, pool the pickups in its three incident
cells and measure $E=\sum_i n_i^2$. Test 12 equally spaced directions at each
candidate distance $\eta,2\eta,4\eta,8\eta,16\eta$ not exceeding $0.45s$, where
$s$ is the mesh side scale. If the list is empty use $0.45s$; append $0.2s$ if
the largest retained distance is smaller than that. All trials are relative to
the original corner position.

Each affected cell must remain convex, exceed its configured initial-area floor,
and satisfy $4\pi A/P^2\geq0.35$. Every pooled pickup must remain assigned,
using the first containing cell. Commit the feasible candidate with the greatest
strict reduction in $E$; otherwise leave the corner unchanged. There is no
uphill acceptance. With frozen data this decreases variance at each accepted
move, but can stall with no improving candidate. The live-window version also
changes its input data, so the same monotonicity statement does not apply
across window changes. No independent terminal result is asserted here.

\subsection{Older coordinated 38-cell annealing with an isoperimetric bound}
\textbf{Executed; an exact integer load target was attained.}
The shared-corner and coordinated-neighbor proposal family is the seven-mode
family specified in Section~\ref{sec:compact-cell-annealing}: root plus its edge
neighbors, 24 trials per activation, random displacement scale, and local
reallocation. Unlike the two interactive methods above, boundary vertices can
move. This earlier run used all 5,986 pickups and a modeled 38-point shoreline,
not the later full-resolution main-island boundary.

Require convexity, area at least 2\% of initial area, and
$4\pi A/P^2\geq0.20$; the earlier 0.35 bound had been relaxed. Boundary simplicity
and modeled shoreline coverage remain hard checks. For this run, the desired
integer loads are 157 or 158. Let $e_i$ be distance from that interval and use
local temperature $T=0.005\sum e_i^2$. The energy is the sum of squared affected
loads: accept nonincreases, or an increase $\Delta E$ with probability
$\exp(-\Delta E/T)$. Skip a patch whose interval-error sum is zero.

The archived seed-11 run had a 500-round budget and reached the target at round
162: 20 cells with 158 and 18 with 157, variance 0.249307479 and CV 0.316967\%.
The minimum isoperimetric score was 0.2021501855. Its audited starting state was
a continuation with variance about 670.828 and one empty cell, after a boundary
crossing had been repaired; it was not a fresh regular initialization.
These results certify neither the later official boundary nor the later shape
ratio. Earlier invalid layouts are not counted as successes.

\subsection{Full-boundary compact 38-cell variants}
\textbf{Implemented interval-target variant; executed median-target variant.}
Both retain the coordinated proposal family but replace the old shape score by
$\operatorname{diam}/w_{\min}\leq2$ for whole and clipped cells. The full domain
includes its hole and uses 5,983 inside pickups, retaining three outside records
separately. During geometric repair, the energy is
$\sum_i\max(0,r(S_i)-1.98)^2$. Underlying-cell validity and coverage are enforced;
repair permits clipped ratios above 2 while reducing that penalty. Balancing
starts only after feasible geometry is obtained, then enforces the clipped bound.

The earlier compact program terminates successfully only if every load is in
$[\lceil0.9N/38\rceil,\lfloor1.1N/38\rfloor]=[142,173]$.
Its presence as source alone does not establish a successful execution.
The later median program keeps the same movement and acceptance family but
uses the median-of-local-medians termination test in the protocol. The median
is not its acceptance energy.

For the saved median run, regular vertices were scaled by 1.04 about
$(4.3677736382465335,8.64255525349333)$ km. Repair seed 7 required two rounds;
balancing used seed 17 and $\alpha=0.02$. The initial median was 100\%; its first
passing round was 53, with $M=4.830597135\%$. CV was about 60.6228\% and four
cells were empty. Maximum whole/clipped ratios were approximately
1.999919/1.999584. This is a success under that median rule, not evidence that
all cells were balanced. The 100-cell successor and its manual stop are already
fully specified in Section~\ref{sec:compact-cell-annealing}.

\section{Disk alternatives on the 5,986 pickup locations}
\subsection{Common fractional-load convention}
For disk $i$ with center $z_i$ and radius $r_i$, let
$C(p)=\{i:\|p-z_i\|\leq r_i\}$ and $m(p)=|C(p)|$.
Except for the fallback variant, a covered pickup contributes $1/m(p)$ to each
covering disk and an uncovered pickup contributes zero. Two disks are neighbors
when their closed disks intersect. A disk's graph degree and a pickup's coverage
multiplicity are different quantities. Distances in these implementations are km.

\subsection{K-means cover followed by degree-reducing shrinkage}
\textbf{Executed initialization study, not a balancing algorithm.}
For $K\in\{40,80,150\}$, k-means uses random state 17, three initializations,
and at most 100 iterations. A disk is centered on each k-means center, with
radius equal to its farthest assigned pickup distance plus $10^{-6}$.
For a degree cap, consider every offending intersecting pair and shrinking
either endpoint to $\max(0,\|z_i-z_j\|-r_j-10^{-7})$.
Choose lexicographically by newly uncovered pickups, lost memberships,
negative disk degree, disk identifier, then radius. Stop when compliant or
after $K^2$ shrink iterations. Centers never move and load balance is not the
shrink objective.

\begin{center}\begin{tabular}{rrrrrr}
\toprule $K$ & No cap & Cap 2 & Cap 3 & Cap 4 & Cap 6\\\midrule
40 &0&489&148&62&0\\80&0&682&219&110&47\\150&0&430&164&41&0\\\bottomrule
\end{tabular}\end{center}
Entries are uncovered pickups. Failure of this initialization does not prove
that a covering configuration with the requested cap cannot exist.

\subsection{Single-disk adaptive local heat with coverage and a degree cap}
\label{sec:disk-heat}
\textbf{Executed fixed-budget balancing tests.}
Choose a disk at random. Draw scale $\sigma$ from
$(0.008,0.03,0.1,0.25)$ with probabilities $(0.25,0.35,0.30,0.10)$.
Propose a center displacement with independent normal coordinates of standard
deviation $\sigma r_i+0.003$. Its minimum new radius covers all pickups that
were uniquely covered by this disk, with $10^{-7}$ margin and a small positive
floor. To obey degree cap $d$, the maximum radius is just below the $(d+1)$th
smallest distance $\|z'_i-z_j\|-r_j$; also forbid a new edge to any already
saturated old nonneighbor. Reject incompatible bounds. Otherwise clamp
\[
 r_i+0.06(1-L_i/t)r_i+\mathcal N(0,(\sigma r_i)^2)
\]
to them. Recompute coverage and degrees and reject any violation.

The affected set contains every disk whose load changed, the moving disk, and
its old and new neighbors. With $E_i=(L_i/t-1)^2$, use
$\Delta E=\sum_{i\in A}(E'_i-E_i)$ and
$T=0.035\operatorname{mean}_{i\in A}E_i$.
Accept $\Delta E\leq0$; otherwise accept with probability $e^{-\Delta E/T}$.
At zero temperature no worsening is accepted. There is no scheduled cooling:
``heat'' is recomputed from local error. Initialization must cover every pickup.
The random seed is $921+d+K$. Budgets were 80,000 proposals for the 40- and
150-disk tests and 200,000 for 100 disks.

\begin{center}\begin{tabular}{rrrr}
\toprule Disks & Cap & Best CV (\%) & Best load range\\\midrule
40&6&0.4764&148.6667--150.8333\\
40&8&0.2044&149.0833--150.3333\\
150&6&6.1480&33.5833--43.8333\\
100&6&0.4393&59.2500--60.3333\\\bottomrule
\end{tabular}\end{center}
These are the \emph{best CV configurations encountered}, not necessarily the
terminal Markov states. All listed snapshots cover the points; connectivity was
not a requirement. Reloading a disk snapshot with a reset random stream is not
exact trajectory continuation.

\subsection{Ten-percent sleep/wake quiescence}
\textbf{Executed and terminated with all disks asleep.}
Keep the preceding single-disk rule, $K=100$, cap 6, and seed 1027, but begin
from the original initialization rather than the best fixed-budget snapshot.
Disk $i$ sleeps exactly when it and every current neighbor lie within 10\% of
$t=59.86$. At round start, shuffle the currently awake set. Skip an entry if it
has since fallen asleep; a newly awake disk outside that snapshot waits for the
next round. After acceptance notify the moving disk, old/new neighbors, every
changed-load disk, and neighbors of those changed-load disks, then reevaluate
sleep status. Stop immediately when all are asleep, possibly within a round.

The saved termination occurred during round 642 after 28,110 proposals and
8,189 acceptances. Loads were 53.9166667--65.8333333, worst error 9.97884\%,
CV 7.73785\%, with full point coverage and cap 6. Individual disks received
61--642 proposals. This is a different schedule and stopping rule from the
fixed-budget runs; it is not their first tolerance-crossing time.

\subsection{Strict self-and-neighbor Pareto improvement}
\label{sec:pareto}
\textbf{Executed; budget exhausted without balance.}
Define tolerance violation $b_i=\max(0,|L_i/t-1|-0.10)$ and degree $d_i$.
The moving disk may worsen neither quantity and must strictly improve at least
one (a $b$ decrease exceeding $10^{-10}$ or an integer degree decrease).
Every old or new neighbor must also worsen neither quantity. Coverage and graph
connectivity are mandatory; this variant has no degree cap.

Five equiprobable proposal types are center-only, radius-only, two joint
center/radius types, and direct deletion of an existing edge by shrinking to
just below tangency. Scales and the center offset floor follow the earlier disk
rule; radius proposals include its 0.06 load drift and are clamped to retain
uniquely covered points. There is no annealing in this strict variant.
The initially disconnected 100-disk cover was connected by expanding disks
13 and 20 by about 0.08067046 km each, adding an edge without changing loads.
Seed 1027 shuffles all 100 disks each round, including balanced disks that may
still lower degree. The budget is 200,000 proposals; success requires worst
load error at most 10\%.

Only 277 proposals were accepted. Worst error decreased from 189.01\% to
170.07\%, CV from 53.99\% to 47.46\%, and mean degree from 3.94 to 3.56;
maximum degree remained 6. Coverage and connectivity held. A new neighbor
would suffer an increased degree, so strict neighbor Pareto protection prevents
adding any edge. This can lock the graph into a restrictive topology.

\subsection{Allow neighbor harm through fixed-temperature annealing}
\textbf{Executed low-, medium-, and high-temperature tests; all capped.}
Retain the moving disk's strict self-Pareto requirement and coverage/connectivity.
For old/new neighbors define
\[
 h_b=\max_j(b'_j-b_j)_+,\quad h_d=\max_j(d'_j-d_j)_+,\quad
 p_{\rm accept}=\exp[-\max(h_b/T_b,h_d/T_d)].
\]
Use $(T_b,T_d)=(0.02,0.25),(0.10,1),(0.50,5)$, respectively.
These are fixed temperatures, with the proposal family and seed of the strict
test; they are not the adaptive energy heat in Section~\ref{sec:disk-heat}.
Neighbors can now suffer harm and edges can be exchanged, but total edge count
cannot increase because the moving disk's degree cannot increase.

\begin{center}\begin{tabular}{lrrrr}
\toprule Setting & Accepted & Worst error (\%) & CV (\%) & Mean/max degree\\\midrule
Low&1082&144.74&41.60&3.22/6\\
Medium&910&177.31&42.24&3.12/5\\
High&858&159.49&43.48&3.04/5\\\bottomrule
\end{tabular}\end{center}
These are final states at 200,000 proposals, not convergence claims or the
separately retained best-worst-error snapshots.

\subsection{Nearest-center fallback outside every disk}
\textbf{Executed, capped at 200,000 proposals.}
Keep fractional allocation inside disks. If $m(p)=0$, assign the pickup's full
unit to the nearest disk center, with lower identifier resolving ties.
Require a connected disk graph and degree at most 6, but do not require point
coverage. Use the strict self-Pareto condition and the same three neighbor-harm
temperature pairs. There are 100 disks, seed 1027, and 2,000 rounds.

The five proposal types again comprise center-only, radius-only, two joint
moves, and direct edge deletion. Center scale is $\sigma r+0.003$, the radius
has 0.06 load drift and Gaussian noise, but the unique-coverage lower bound is
removed; retain only a $10^{-5}$ positive radius floor. For edge deletion,
propose $\|z_i-z_j\|-r_j-10^{-7}$ when positive and below the current radius.
A move can change fallback ownership and therefore loads of nonneighbors.
The neighbor-harm test still examines only old/new disk neighbors, not every
disk whose fallback load changes.

\begin{center}\begin{tabular}{lrrrrr}
\toprule & Accepted & Worst (\%) & CV (\%) & Mean/max degree & Fallback points\\\midrule
Low&2403&141.40&39.35&2.22/5&1966\\
Medium&3448&182.33&42.37&2.28/5&2477\\
High&4342&151.42&40.23&2.26/6&2469\\\bottomrule
\end{tabular}\end{center}
Accepted moves harming a nonneighbor numbered 670, 1,400, and 1,848.
The best worst-error values encountered were 133.88\%, 102.14\%, and 118.84\%,
respectively. None met the all-disk 10\% criterion; this was not a median test.

\section{Vertex alternatives and later Manhattan comparisons}
\subsection{Rule 2: remove, move to a load-weighted neighbor centroid, reclaim}
\textbf{Executed; distinct from the pooled-point centroid rule.}
Use a fixed 100-vertex honeycomb with 68 degree-three interior vertices and
32 fixed boundary vertices. For an activated interior vertex, pool its own and
its neighbors' stored pickups; skip an empty pool. First transfer its own
pickups to their nearest neighbor. With the resulting neighbor loads $w_j$, set
\[
 c'_v=\frac{\sum_{j\in N(v)} w_jc_j}{\sum_{j\in N(v)} w_j}.
\]
Then reclaim from each neighbor only those pickups whose nearest location among
$v$ and its neighbors is $v$. Do \emph{not} redistribute pickups between two
neighbors merely because one of them is now closer. Squared-distance ties
within $10^{-14}$ use the lower identifier. Accept every update. There is no
balance filter, global reassignment, or separate geometry test.

Each sweep shuffles eligible vertices, using seeds 11, 22, 33 with the archived
shuffle generator initialized by seed plus 999. The stopping test is five
consecutive sweeps with no net per-update ownership changes and maximum movement
below $10^{-6}$ initial edge lengths, with a 320-sweep cap. The saved PCA-fitted
initial mesh uses scale 0.8007194245 and rotation 1.0938725761 radians.
All 5,986 points were included, including the three later flagged outside points.

\begin{center}\begin{tabular}{rrrrrr}
\toprule Seed & Sweeps & CV (\%) & Operational RMS & Centroid RMS & Empty\\\midrule
11&320&97.5593&0.502964&0.353815&13\\
22&320&96.1198&0.505681&0.359120&15\\
33&320&99.5138&0.504958&0.359696&16\\\bottomrule
\end{tabular}\end{center}
Distances are km. All three runs hit the cap. Tests on the first 400 records
also hit 320 sweeps, with CV 111.018\%, 106.478\%, and 92.804\%.
These are not successful balance terminations.

\subsection{Rule 3: pooled-point centroid projected to the neighbors' triangle}
\textbf{Executed on Manhattan after the original discussion.}
The full rule is given in the earlier local-update section: pool the four stored
pickup sets, project their point centroid to the three neighbors' closed
triangle, and reassign all pooled pickups among those four positions. There is
no preliminary transfer and every proposal is accepted. It differs from Rule 2
both in the point centroid used for motion and in full four-way redistribution.
The fixed mesh, initial assignments, shuffled seeds, 320-sweep cap, and
five-stable-sweep test are as in the preceding comparison.

Initial CV was 136.4873\%, operational RMS 0.397645 km, with 30 empty vertices.
\begin{center}\begin{tabular}{rrrrr}
\toprule Seed & Stable at sweep & CV (\%) & Operational RMS (km) & Empty\\\midrule
11&73&80.0520&0.322642&18\\
22&66&79.7785&0.322446&18\\
33&67&80.1074&0.321531&17\\\bottomrule
\end{tabular}\end{center}
Global nearest-center disagreement was 1.3197\%, 1.1861\%, and 1.1193\%.
Stability does not imply balanced loads or convergence under the later median
criterion. First-400-record checks stabilized at sweeps 43 and 24 for seeds 11
and 33; seed 22 hit the 320-sweep cap. The earlier synthetic comparisons remain
separate experiments with their own generated data and units.

\subsection{Ordinary Lloyd comparisons, with and without fixed boundary}
\textbf{Executed.} Assign every pickup to its globally nearest center; move each
eligible nonempty center to its own assigned-point centroid. Empty centers
remain where they are. No triangle constraint, local pool, or balance acceptance
is used. The fixed-boundary comparison holds the same 32 boundary centers fixed;
the all-free comparison allows all 100 nonempty centers to move. Use the same
initialization and stability test for the 5,986-point comparison.
The fixed-boundary run stabilized at sweep 53 with CV 114.6078\%, RMS
0.289736 km and 31 empty centers. The all-free run stabilized at sweep 54 with
CV 105.1562\%, RMS 0.268392 km and 29 empty centers. Lloyd optimizes assignment
distance, not load equality, so the two criteria need not improve together.

\subsection{Lloyd with farthest-point reseeding of empty centers}
\textbf{Executed improved baseline.} After ordinary centroid updates and global
reassignment, repeatedly choose the lowest-identifier empty center. Move it to
the pickup having greatest distance from its current assigned center, resolving
ties by the lowest input index; reassign globally after each reseed. Permit at
most 100 reseeds per sweep. Nearest-center squared-distance ties within
$10^{-14}$ use lower center identifier. Stop after five stable sweeps or 320.
Starting with the same saved mesh, this stabilized after 27 sweeps and 30 reseeds:
CV 74.9754\%, RMS 0.220041 km, loads 1--198, no empty centers.
With the separate all-movable experiment's initialization below, it stabilized
after 32 sweeps, with CV 69.7400\%, RMS 0.216862 km, loads 1--189, no empties.
Neither is an equal-load result.

\subsection{Rule 2 with every vertex movable: collapse experiment}
\textbf{Executed, then manually stopped.}
Construct a complete-cell patch of 35 hexagons in columns 11, 13, 11: 100
vertices, 134 edges, 32 degree-two and 68 degree-three vertices. All vertices
are eligible. Use PCA-fitted scale 0.83091156475 and the preceding rotation.
Generalize Rule 2 to each vertex's two or three neighbors, retaining its
remove/weighted-centroid/reclaim operations. There is no fixed rim, coverage
condition, or geometry acceptance check. Initial CV was 148.7686\% and RMS
0.404079 km. Success would require every load in 54--65 after a completed sweep;
an exact immobile unbalanced state is separately classified as absorbing.

\begin{center}\begin{tabular}{rrrrrr}
\toprule Seed & Last sweep & CV (\%) & RMS (km) & Mesh diameter (km) & Empty\\\midrule
11&11700&672.7866&2.858818&0.392908&34\\
22&11700&692.0420&2.930854&0.244342&41\\
33&11600&673.3917&2.820690&0.341206&32\\\bottomrule
\end{tabular}\end{center}
Transverse widths had fallen to roughly $10^{-14}$ km. These are manually
stopped collapsed states, not convergence. Every weighted-average move lies
inside the current convex hull, so the hull cannot expand; that observation
alone is not a proof about all possible infinite-precision trajectories.

\section{Different-data experiment: drivers, disks, and ride allocation}
\subsection{Global nearest-free-driver construction}
\textbf{Executed.} This uses taxi trips, not the 5,986 static pickups.
On 15 January 2015, use 12:00--13:00 as warm-up and 13:00--14:00 as the next
hour. From 42,002 raw city records, the recovered processing retains 20,110 and
19,171 valid rides, respectively. Remove invalid/zero/nonfinite coordinates and
nonpositive duration; quarantine trips longer than six hours or straight-line
distance above 100 km. A current official Manhattan polygon selects historical
pickups; retain dropoffs outside it. Coordinates use a fixed equirectangular
transform around latitude 40.75 degrees. Driver identities are synthetic,
not inferred taxi identities.

Process requests by pickup time with deterministic ties; process simultaneous
dropoffs first. Assign the nearest free driver globally; create one if none is
free. Pickup travel takes zero time. A driver is busy for the recorded trip
duration and then located at its recorded endpoint. Warm-up creates 4,587
drivers, of whom 4,211 are busy and 376 free at its end. The second global hour
adds 45, giving 4,632. This is the peak-concurrency requirement under the
zero-pickup-travel assumption, not a realistic fleet-size guarantee.

The proposed local dispatch chooses the nearest free driver sharing a disk
with the request, otherwise creates one; disk load targets are fleet size/100
and relaxation is triggered by pickups/dropoffs. The recovered second-hour
local-dispatch code is a prototype, not a completed comparison result.

\subsection{Driver disks with cap six: stalled original rule}
\textbf{Executed.} Apply the single-disk squared-error adaptive heat rule with
full coverage and sleep/wake activation to the 4,587-driver snapshot. At one
million proposals it remained outside tolerance, with worst error about 18.83\%.
There were two graph components: 91 disks with total weight 4,233, and nine
with weight 354. At target $45.87$, those nine would need at least 371.547
weight to all reach the lower tolerance bound. Their mean deficit already
implies about 14.25\% error unless weight can cross components. An enormous
radius, about 21.7 million km, also demonstrates the absence of useful spatial
compactness control. This was a stalled budget-limited run, not success.

\subsection{Exploratory hinge objective and coordinated disk proposals}
\textbf{Implemented and reported to reach tolerance before interruption; rejected
as a substitute for the requested original method.}
Replace ordinary squared error by
$\sum_i\max(|L_i/t-1|-0.10,0)^2$. Keep temperature based on the affected disks'
ordinary squared errors, multiplied by 0.035. After 20,000 proposals, use a
coordinated block with probability 0.25: a root disk plus one or two randomly
chosen neighbors. Move their centers with independent Gaussian increments;
propose radii with 0.10 rather than 0.06 load drift and Gaussian scale noise,
clamped below by $10^{-5}$.

Protect points whose current covering disks are all in the block. If any lose
coverage, expand a selected block disk using the smallest required expansion
relative to its old radius, with denominator floor 0.01. Reject remaining
coverage or degree-cap violations. Apply the hinge-energy Metropolis test to
the block, its old/new neighbors and all changed-load disks. This changes both
proposal and acceptance rules. The archive narrative reports reaching tolerance,
but an exact terminal metric and unambiguous execution trace for that exploratory
revision were not recovered; no numerical success benchmark is inferred.

\subsection{Connected driver disks with no degree cap}
\textbf{Executed controlled return to the original squared-error rule.}
Use only single-disk proposals, full coverage, ordinary squared-error adaptive
heat, and seed 1027. Remove the degree cap; require connectedness instead.
Initially connect components by repeatedly finding the closest intercomponent
disk boundaries and expanding both radii by half their positive gap plus
$10^{-7}$. During balancing, the minimum proposed radius covers uniquely
covered points (positive floor $10^{-5}$ plus margin); there is no upper bound.
Reject a proposed edge removal if it disconnects the graph. There is no
coordinated motion, hinge objective, radius penalty, or cooling schedule.

At each round shuffle the disks that are themselves outside 10\% tolerance or
have an outside-tolerance neighbor. Recheck each before activation. Termination
is tested at round boundaries; the attempt budget is one million. Recompute
loads independently at the end and check coverage and connectedness.
A fresh initialization reached tolerance after 195 rounds and 13,442 proposals:
worst error 9.9121\%, mean/max degree 24.32/55, mean/max point multiplicity
7.96/23, median radius 1.34 km and maximum radius 22.05 km.
Restarting from the stalled configuration reached tolerance after 90 rounds and
2,150 proposals, worst error 9.9993\%, mean/max degree 6.4/16, but retained an
approximately 20.9-million-km maximum radius. These load successes do not
establish geographical locality, nor do they validate the unexecuted local
ride-allocation proposal.

\section{Discussed alternatives without a complete executed specification}
\subsection{Nonintersecting disks and line-of-sight adjacency}
The earlier concept used nonintersecting disks, no full-domain coverage
requirement, and adjacency when the center-to-center segment passed through no
third disk. A pickup inside a disk belonged to it; an outside pickup went to
the nearest center. An illustrative objective rewarded covered dots and
penalized squared neighbor-load differences. No definitive objective coefficient,
proposal distribution, acceptance test, or scheduler was adopted in the recovered
discussion. This concept cannot be represented as a fully specified tested
algorithm. It differs from the later intersecting fractional-load disks.

\subsection{Lifted three-dimensional triangle and geometric-mean suggestion}
Temporarily give the active vertex's dots to its three neighbors. Lift neighbor
positions to $A=(x_a,y_a,w_a)$, $B=(x_b,y_b,w_b)$, $C=(x_c,y_c,w_c)$, intersect
their triangle with a plane $z=w'$, and use the horizontal coordinates of the
intersection segment's midpoint as the proposed position. A subsequent
reclamation operation was discussed. For $(100,10,10)$ and arithmetic mean
$w'=40$, the endpoints are $(A+2B)/3$ and $(A+2C)/3$, giving midpoint
$(A+B+C)/3$. This cancellation is a special calculation, not a general identity
for every height triple. Equal heights can give the entire triangle rather
than a unique segment; plane/end-point degeneracies require additional rules.
The geometric mean was mentioned as another height but never selected.
No complete execution convention or independent result is recovered for either
lifted-plane variant. The later weighted-centroid Rule 2 is a separate,
fully implemented method, documented above.

\subsection{Optional local variance or variance-plus-distance acceptance}
For a fixed four-agent pool, the proposed score
$B_v=\sum_{u\in U_v}(w_u-\bar w)^2$ changes by the same amount as the global
sum of squared loads, since the pool's total load is conserved. Requiring strict
improvement would therefore make that scalar monotone. The alternative
$J_v=B_v+\mu\sum_{u\in U_v}\sum_{p\in D_u}\|p-c_u\|^2$ adds assignment distance;
its change also matches the corresponding global score when only the pool is
updated. No $\mu$ or acceptance filter was adopted for the reported vertex
experiments. These are discussed modifications, not tests whose outcomes can
be attached to Rule 2 or Rule 3.

\subsection{Triangular lattice, dynamic mesh, and Delaunay}
An initial six-neighbor triangular-lattice interpretation was corrected to a
three-neighbor honeycomb. No separate triangular-lattice result is established.
Rebuilding adjacency after motion and using Delaunay triangulation were discussed
but not adopted. Maintaining degree three alone does not ensure planar
hexagonal faces; Delaunay yields variable degree and can require nonlocal edge
changes. There is no recovered implementation or executed benchmark for these
alternatives. Discussion of distributed or balanced k-means likewise does not
supply an additional specified algorithm beyond the concrete Lloyd and
recursive-clustering programs documented above.

\section{Source inventory and remaining reproducibility limits}
\label{sec:source-catalog}
The following are paths within recovered archives, not promises that original
Mac paths are accessible. The merged document is a recovered-source cloud copy;
comparison and writeback to the Mac remain pending. Source inspection and
saved results, rather than new runs, support the added catalog.
\begin{description}
\item[Interactive cell methods:] \path{Manhattan_Taxi_Regions.html} in original
and local-rule archives; \path{disk_experiment.py} for the shrink study.
\item[Older cell annealing:] \path{Manhattan_Balanced_Hexagons/local_anneal.cpp}.
\item[Later compact cells:] \path{work/compact38/anneal.cpp},
\path{work/median38/anneal.cpp}, \path{work/median38/transfer.json}, and
\path{work/median100/anneal.cpp}, with their input and checkpoint files.
\item[Adaptive disks:] \path{Disks_100/disk_local.py} and the
\path{Balanced_Disks} archive; \path{Disks_100_Quiescence} for sleep/wake.
\item[Pareto disks:] \path{Original_Local_Annealing/test_local_rule.py},
\path{LOCAL_RULE.md}, and saved result files.
\item[Fallback:] \path{Nearest_Fallback/simulate.py} and its saved results.
\item[Vertices:] \path{work/rule2/run.js}, \path{work/vertex_only},
\path{work/four_compare}, \path{work/all_movable/run.js}, and their results.
\item[Lloyd reseeding:] \path{Manhattan_Comparison/lloyd.js} and
\path{lloyd.json}.
\item[Driver experiment:] \path{Ride_Allocation/README.md},
\path{disks.py}, \path{test_connected_unbounded.py}, and saved driver snapshots
and result records.
\end{description}

The recovered historical discussion came from chat
\path{01a0ddd5-d823-78f3-8007-4e6affbc3f0b}, turn
\path{01a0e248-be23-7c00-b6f6-8998d8156940}; the protocol supplement came from chat
\path{01a0e288-2186-7bf0-9df7-4ecf938cb3c6}, turn
\path{01a0e446-20fc-7712-ab87-a13b33a6983a}.
The later compact recovery bundle has persistent identifier
\path{libfile_dc84879b89c08191b3fb5efe83d086ad}.
The catalog cannot fill missing run-specific GUI settings, unrecorded proposal
choices, or missing exploratory terminal traces by inference. Those gaps are
explicitly marked above. ``All alternatives'' here means all identifiable
alternatives in these recovered records, not proof that every past conversation
or transient implementation has survived.
'''
s=s.replace('\\end{document}',append+'\n\\end{document}')
p.write_text(s)
