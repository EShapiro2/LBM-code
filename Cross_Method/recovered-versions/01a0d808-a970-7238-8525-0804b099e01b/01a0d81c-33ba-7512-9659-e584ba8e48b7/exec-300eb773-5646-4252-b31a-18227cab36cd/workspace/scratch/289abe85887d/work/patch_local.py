from pathlib import Path

p = Path('work/Manhattan_Taxi_Regions/Manhattan_Taxi_Regions.html')
s = p.read_text()
s = s.replace('An active corner looks at the three hexagons around it and is pulled toward the fuller ones and away from the emptier ones: it moves a fixed step <code>η</code> along <code>Σ (nᵢ − n̄) uᵢ</code>, where <code>uᵢ</code> points toward the centre of hexagon <code>i</code>. A move is shortened or refused if a hexagon would fold or shrink below the area floor.', 'An active corner tests nearby positions and counts pickups in its three incident hexagons. It takes the candidate with the greatest strict reduction in the sum of squared pickup counts. Every accepted move keeps these three cells convex and above the area and shape bounds. The step η sets the smallest search radius.')
s = s.replace('The corner rule never settles by itself, so the run stops after this many rounds.', 'With frozen pickups, every accepted move strictly decreases the variance; the run may stop early at a local optimum.')
s = s.replace('A regular hexagon is 0.907; slivers approach 0.', 'A regular hexagon is 0.907; all movable cells must stay above 0.35.')
s = s.replace('Corners moving</span>', 'Corners searching</span>')
start = s.index('function valid(N, cells){')
end = s.index('function makeWorld(){', start)
replacement = '''// A local coordinate search. The total pickup count is fixed in frozen mode,
// so decreasing sum(n_c^2) is exactly decreasing the population variance.
// Only the three incident cells change when an interior corner moves.
function convex(N, c){
  const r = N.cells[c], X = N.VX, Y = N.VY;
  for (let i = 0; i < 6; i++){
    const a = r[i], b = r[(i + 1) % 6], d = r[(i + 2) % 6];
    if (orient(X[a], Y[a], X[b], Y[b], X[d], Y[d]) <= 1e-10 * N.s * N.s) return false;
  }
  return true;
}
function valid(N, cells){
  const floor = N.floor === undefined ? P.floor : N.floor;
  for (const c of cells){
    const a = area(N, c), p = perim(N, c);
    if (a < floor * N.area0[c] || !convex(N, c) || 4 * Math.PI * a / (p * p) < 0.35) return false;
  }
  return true;
}
function activateVertex(N, v, eta){
  const cs = N.vcells[v], ox = N.VX[v], oy = N.VY[v];
  const base = cs.reduce((sum, c) => sum + N.count[c] * N.count[c], 0);
  const pts = [];
  for (const c of cs) for (const i of N.members[c]) pts.push(i);
  const X = MAN_PTS.x, Y = MAN_PTS.y;
  const steps = [eta, 2 * eta, 4 * eta, 8 * eta, 16 * eta]
    .filter((d, i, a) => d <= 0.45 * N.s && (i === 0 || d !== a[i - 1]));
  if (steps.length === 0) steps.push(0.45 * N.s);
  // Also try a meaningful step even when the user selects a very small eta.
  if (steps[steps.length - 1] < 0.2 * N.s) steps.push(0.2 * N.s);
  let best = base, bx = ox, by = oy;
  for (const d of steps) for (let dir = 0; dir < 12; dir++){
    const angle = 2 * Math.PI * dir / 12;
    N.VX[v] = ox + d * Math.cos(angle);
    N.VY[v] = oy + d * Math.sin(angle);
    N.attempts++;
    if (!valid(N, cs)){ N.rejected++; continue; }
    const counts = [0, 0, 0];
    let covered = true;
    for (const i of pts){
      let j = 0;
      for (; j < 3; j++) if (inCell(N, cs[j], X[i], Y[i])) break;
      if (j === 3){ covered = false; break; }
      counts[j]++;
    }
    if (!covered) continue;
    const score = counts[0] ** 2 + counts[1] ** 2 + counts[2] ** 2;
    if (score < best){ best = score; bx = N.VX[v]; by = N.VY[v]; }
  }
  N.VX[v] = bx; N.VY[v] = by;
  if (best < base){
    N.moves++; N.travel += Math.hypot(bx - ox, by - oy);
    relocateLocal(N, cs);
  }
}
'''
s = s[:start] + replacement + s[end:]
s = s.replace('function sweepNet(N, etaFrac){ // one round: as many activations as there are movable corners\n  const eta = etaFrac * N.s, I = N.ivs;\n  for (let k = 0; k < I.length; k++) activateVertex(N, I[(rand() * I.length) | 0], eta);\n}', 'function sweepNet(N, etaFrac){ // one activation per corner, in random order\n  const eta = etaFrac * N.s, I = N.ivs.slice();\n  for (let i = I.length - 1; i > 0; i--){\n    const j = (rand() * (i + 1)) | 0;\n    [I[i], I[j]] = [I[j], I[i]];\n  }\n  for (const v of I) activateVertex(N, v, eta);\n}')
s = s.replace('Each move is ${step < 10 ? step.toFixed(1) : step.toFixed(0)} m', 'Smallest search radius is ${step < 10 ? step.toFixed(1) : step.toFixed(0)} m')
s = s.replace('const before = hx.travel; HX.sweepNet(hx, C.eta); rounds++; stillMoving = hx.travel > before;', 'const before = hx.travel; HX.sweepNet(hx, C.eta); rounds++; stillMoving = hx.travel > before;')
p.write_text(s)
