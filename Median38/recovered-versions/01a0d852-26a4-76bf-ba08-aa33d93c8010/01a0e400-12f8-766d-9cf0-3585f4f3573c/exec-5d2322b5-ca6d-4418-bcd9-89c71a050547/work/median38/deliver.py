import json,hashlib,math,re,zipfile
from pathlib import Path
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from shapely.geometry import Polygon
from audit import audit,dom,P,D
p=Path('work/median38');a=json.load(open(p/'initial_audit.json'));b=audit(p/'balance.json.last.json');assert b['feasible'] and b['M']<=5
hist=[]
for line in (p/'balance.log').read_text().splitlines():
 m=re.match(r'CHECK (\d+) M (\S+) energy (\S+)',line)
 if m:hist.append([int(m[1]),float(m[2]),float(m[3])])
assert len(hist)==b['round'] and all(h[1]>5 for h in hist[:-1])
json.dump(b,open(p/'final_audit.json','w'),indent=2)
prov=json.load(open(p/'provenance.json'));bp=Path('work/verified38/main_island_km.geojson');prov['boundaryKmSha256']=hashlib.sha256(bp.read_bytes()).hexdigest();prov['sourceBoundarySha256']=hashlib.sha256(Path('work/verified38/borough_boundaries.json').read_bytes()).hexdigest()
summaryKeys=['M','cv','centroidRmsKm','maxUnderlyingRatio','maxClippedRatio','coverageResidualKm2','overlapKm2','uniqueAssigned','multipleAssigned','convexSixSided','countsMatchSimulation']
out={'stage':'new_median_termination_result','status':'success','actualExecution':True,'K':38,'records':5986,'owned':5983,'outsideIndices':[309,4705,5212],'units':'km; same recovered north-up affine frame','boundary':'NYC DCP 26b Manhattan main island, full resolution, hole retained','provenance':prov,'initial':{k:a[k] for k in summaryKeys},'final':{k:b[k] for k in summaryKeys},'repairRounds':2,'balanceRounds':b['round'],'firstPassingRound':b['round'],'initialAlreadyPassed':False,'tolerances':{'coverageAcceptanceKm2':1e-10,'auditAreaKm2':1e-8,'positiveBoundaryKm':1e-9,'pickupCrossKm2':1e-10,'mapDecimalPlaces':6},'checks':'Full-precision geometry independently checked with Shapely; all 38 convex six-sided; no overlaps; all 5983 land pickups assigned once; rounded coordinates below are for display. Infinity is encoded as string.','rowSchema':['id','count','localMedianPercent','originalMeshNeighbors','serviceNeighbors','clippedCentroid','orderedHexagonVertices','underlyingRatio','clippedRatio'],'cells':[]}
for i,c in enumerate(b['cells']):out['cells'].append([i,c['count'],b['localMedians'][i],b['meshNeighbors'][i],b['neighbors'][i],[round(v,6) for v in c['clippedCentroid']],[[round(v,6) for v in z] for z in c['vertices']],round(c['underlyingRatio'],9),round(c['clippedRatio'],9)])
out['initialCounts']=a['counts'];out['initialLocalMedians']=a['localMedians'];out['initialServiceNeighbors']=a['neighbors']
(p/'transfer.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False))
fig,axs=plt.subplots(1,2,figsize=(10,10));norm=Normalize(0,300);cmap=plt.get_cmap('viridis')
for ax,r,title in zip(axs,[a,b],['Repaired regular mesh; before balance',f'New result: first passing round {b["round"]}']):
 for c in r['cells']:
  s=Polygon(c['vertices']).intersection(dom)
  for g in ([s] if s.geom_type=='Polygon' else s.geoms):
   if g.geom_type!='Polygon':continue
   x,y=g.exterior.xy;ax.fill(x,y,color=cmap(norm(c['count'])),ec='white',lw=.55)
   for hole in g.interiors:x,y=hole.xy;ax.fill(x,y,color='white')
  x,y=c['clippedCentroid'];ax.text(x,y,str(c['count']),fontsize=5,ha='center',va='center',color='black',bbox={'facecolor':'white','alpha':.75,'pad':.2,'edgecolor':'none'})
 x,y=dom.exterior.xy;ax.plot(x,y,c='black',lw=.45);q=P[[309,4705,5212]];ax.scatter(q[:,0],q[:,1],marker='x',c='red',s=22,zorder=10)
 ax.set_aspect('equal');ax.set_xlim(-1,10);ax.set_ylim(-1,21);ax.set_title(title+'\nM='+f'{r["M"]:.3f}%'+f'; loads {min(r["counts"])}–{max(r["counts"])}',fontsize=10);ax.set_xlabel('km');ax.set_ylabel('km north');ax.plot([0,2],[-.6,-.6],c='black');ax.text(1,-.4,'2 km',ha='center',fontsize=8);ax.annotate('N',xy=(9,20.3),xytext=(9,19),ha='center',arrowprops={'arrowstyle':'->'})
fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=axs,label='Pickup count (colors saturate above 300)',shrink=.65);fig.suptitle('38 compact hexagonal service regions • official Manhattan main island\n5,983 assigned pickups; 3 outside land marked × • labels show loads',fontsize=12)
fig.savefig(p/'new_median_map.png',dpi=180,bbox_inches='tight');fig.savefig(p/'new_median_map.pdf',bbox_inches='tight')
(p/'README.txt').write_text('Fresh run starting from original regular vertices, inflated uniformly 1.04 about official domain centroid. Repair seed7; 2 complete rounds. Fresh balancing seed17, alpha .02, original proposal/energy/temperature logic. Stop first complete round with median of local medians <=5. The 3 outside land points remain in original dataset and are excluded from ownership. Full-resolution official domain including hole used for geometry checks. No previous optimized coordinates used. Run prepare.py, compile anneal.cpp linked to GEOS, then repair and balance as documented in logs/provenance. audit.py independently checks full precision. deliver.py builds outputs. Checkpoint includes RNG and normal-distribution state; deterministic complete rerun possible. Integer topology remains native_input cells. Float64 tolerances in transfer.json.\n')
with zipfile.ZipFile(p/'New_Median_Hexagons.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in p.iterdir():
  if f.is_file() and f.suffix not in ['.zip'] and f.name!='anneal':z.write(f,'median38/'+f.name)
 for f in ['work/native_input.json','work/regular_vertices.txt','Manhattan_Pickups_2015-01-15_0800-0815.json','work/verified38/main_island_km.geojson','work/verified38/assessment.json','work/verified38/boundary_metadata.json']:z.write(f,f)
print('FINAL',b['round'],b['M'],'transfer bytes',len((p/'transfer.json').read_bytes()))
