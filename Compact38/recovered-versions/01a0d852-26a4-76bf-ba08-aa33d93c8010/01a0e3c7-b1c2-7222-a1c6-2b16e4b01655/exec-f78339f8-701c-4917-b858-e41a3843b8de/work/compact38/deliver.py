import sys,json,hashlib,zipfile,csv
from pathlib import Path
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
sys.path.insert(0,'work/compact38');from audit import D,triangles,clip,audit
p=Path('work/compact38');original=json.load(open(p/'initial_audit.json'));sets=[]
for name,f in [('Feasible start','repair_best.json'),('Best constrained result','balanced_best.json')]:
 s=json.load(open(p/f));v=list(zip(s['verticesX'],s['verticesY']));r=audit(v);r['round']=s['round'];r['geometry']={'vertices':v,'cells':D['cells'],'outline':D['outline'],'clippedRegionTrianglePieces':[[q for t in triangles if (q:=clip(t[:],[v[j] for j in c]))] for c in D['cells']]};sets.append((name,r))
summary={'inputSha256':hashlib.sha256(Path('Manhattan_Pickups_2015-01-15_0800-0815.json').read_bytes()).hexdigest(),'N':5986,'K':38,'targetCounts':[142,173],'ratioDefinition':'Maximum vertex-pair distance divided by minimum projection span over edge normals of the convex hull. For nonconvex clipped regions, directional widths equal those of their convex hull; actual intersections are retained as triangulated polygon pieces, not replaced by that hull for assignment or area.','originalAndHistoricalAudit':original,'feasibleInitial':sets[0][1],'bestConstrained':sets[1][1],'certificate':json.load(open(p/'impossibility_certificate.json')),'result':'Joint load and clipped-region ratio targets impossible for this modeled domain and dataset, by northern-tip certificate. Feasible compact geometry was constructed. Best balancing iterate is not a successful balanced result.','run':{'repairSeed':7,'repairRounds':2,'balanceSeed':17,'bestBalanceRound':sets[1][1]['round'],'lastLoggedCompletedRound':420,'approximateLoggedWallSeconds':35,'status':'stopped after geometric impossibility certificate, not cap or convergence','exitCode':130},'historicalMerged':{'cv':.23529071368402776,'centroidRmsKm':.4468031164662795,'newShapeConstraint':'unconstrained; not asserted compliant'}}
(p/'results.json').write_text(json.dumps(summary,indent=2))
with open(p/'per_cell.csv','w') as f:
 w=csv.writer(f);w.writerow(['state','cell','count','underlying_width_ratio','clipped_width_ratio','clipped_area_km2'])
 for name,r in sets:
  for i in range(38):w.writerow([name,i,r['counts'][i],r['underlyingRatios'][i],r['clippedRatios'][i],r['clippedAreas'][i]])
fig,axs=plt.subplots(1,2,figsize=(9,10),layout='constrained');norm=matplotlib.colors.Normalize(0,350);cmap=plt.get_cmap('viridis');sample=np.array(D['points'])[[i*5986//300 for i in range(300)]]
for ax,(name,r) in zip(axs,sets):
 land=Polygon(D['outline'],facecolor='#f6f6f6',edgecolor='black',lw=.7);ax.add_patch(land);v=r['geometry']['vertices']
 for i,c in enumerate(D['cells']):
  xy=[v[j] for j in c];patch=Polygon(xy,facecolor=cmap(norm(r['counts'][i])),edgecolor='#333333',lw=.65);patch.set_clip_path(land);ax.add_patch(patch);ax.add_patch(Polygon(xy,fill=False,edgecolor='#808080',lw=.4,linestyle='--',alpha=.5))
 ax.scatter(sample[:,0],sample[:,1],s=1.5,c='black',alpha=.5);ax.set_xlim(-2,12);ax.set_ylim(-2,22);ax.set_aspect('equal');ax.set_title(f'{name}\nCV {r["cv"]:.4f}; counts {r["min"]}–{r["max"]}\nWorst ratio: underlying {r["worstUnderlying"]:.4f}, clipped {r["worstClipped"]:.4f}',fontsize=10);ax.set_xlabel('km east');ax.set_ylabel('km north')
fig.suptitle('38 convex hexagonal cells · full modeled Manhattan coverage\nBoth width ratios ≤2; load balance not achieved',fontsize=13);fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm,cmap=cmap),ax=axs,shrink=.6,label='Pickup count (colors saturate above 350)',extend='max');fig.supxlabel('Filled: actual clipped service regions. Dashed: underlying six-sided cells.\nSame geographic scale and 300-point display sample; all 5,986 points used in calculation.',fontsize=9);fig.savefig(p/'before_after.png',dpi=160);fig.savefig(p/'before_after.pdf')
(p/'README.txt').write_text('Results: both underlying and clipped width ratios constrained to 2. Original regular geometry was infeasible: coverage gap and clipped slivers.\nFeasibility repair begins from regular geometry uniformly enlarged 1.06 about mean shoreline vertices. Repair optimizes clipped ratio violation while retaining underlying <=2, convexity, coverage and embedding. It found feasible geometry in 2 rounds.\nBalance uses established local shared-corner plus graph-neighbor displacement proposals, local imbalance-based annealing, rejection of invalid geometry/coverage, and exact in-cell dot reassignment. Feasible input: feasible_start.txt.\nCompile: g++ -O3 -std=c++17 work/compact38/anneal.cpp -o work/compact38/anneal\nRepair: work/compact38/anneal work/compact38/start.txt work/compact38/repair_best.json 200 0 .01 7 repair\nBalance: work/compact38/anneal work/compact38/feasible_start.txt work/compact38/balanced_best.json 1000 0 .02 17 balance\nThe 1000-round argument is only a bounded budget, never convergence. Actual run was stopped after round 420 was logged, upon establishing the geometric impossibility certificate. Best iterate at round 412.\nAudit: python3 work/compact38/audit.py. Utilities use work/native_input.json for unchanged topology/domain/points and the retained original/historical vertex files.\nNo result satisfies load target. The northern-tip proof applies to clipped regions with ratio <=2; it does not rule out a solution constraining underlying cells alone.\n')
with zipfile.ZipFile(p/'Compact38_Experiment.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in p.iterdir():
  if f.is_file() and f.suffix!='.zip':z.write(f,str(f))
 for f in ['Manhattan_Pickups_2015-01-15_0800-0815.json','work/native_input.json','work/regular_vertices.txt','work/guided020_best.json','work/audit_solution.py','work/local_anneal.cpp']:z.write(f,f)
print('saved')
