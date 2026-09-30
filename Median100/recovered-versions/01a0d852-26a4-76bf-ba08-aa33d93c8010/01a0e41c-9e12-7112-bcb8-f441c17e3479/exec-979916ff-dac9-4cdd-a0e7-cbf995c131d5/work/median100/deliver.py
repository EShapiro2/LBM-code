import json,math,re,hashlib,zipfile
from pathlib import Path
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from shapely.geometry import Polygon
from audit import audit,dom,P,D
p=Path('work/median100');a=json.load(open(p/'initial_audit.json'));b=audit(p/'balance.json.last.json');assert b['feasible'] and b['M']<=5 and len(b['cells'])==100
history=[]
for line in (p/'balance.log').read_text().splitlines():
 m=re.match(r'CHECK (\d+) M (\S+) energy (\S+)',line)
 if m:history.append({'round':int(m[1]),'M':float(m[2]),'energy':float(m[3])})
assert len(history)==b['round'] and all(h['M']>5 for h in history[:-1]);json.dump(history,open(p/'history.json','w'),indent=2);json.dump(b,open(p/'final_audit.json','w'),indent=2)
prov=json.load(open(p/'provenance.json'));prov['boundaryKmSha256']=hashlib.sha256(Path('work/verified38/main_island_km.geojson').read_bytes()).hexdigest()
keys=['M','cv','centroidRmsKm','maxUnderlyingRatio','maxClippedRatio','coverageResidualKm2','overlapKm2','uniqueAssigned','multipleAssigned','convexSixSided','countsMatchSimulation','minConvexCrossKm2','underlyingOverlapKm2']
meta={k:prov[k] for k in ['sideKm','offsetFractions','vertices','repairSeed','balanceSeed','alpha','inputSha256','boundaryKmSha256','scaleOffsetCandidatesTested','exact100Candidates']}
out={'stage':'new_100_cell_median_termination_result','status':'success','actualExecution':True,'processAlive':False,'K':100,'records':5986,'owned':5983,'outsideIndices':[309,4705,5212],'units':'km; unchanged recovered north-up affine frame','boundary':'NYC DCP 26b main island, same full-resolution polygon and hole','provenance':meta,'initial':{k:a[k] for k in keys},'final':{k:b[k] for k in keys},'repairRounds':a['round'],'balanceRounds':b['round'],'firstPassingRound':b['round'],'initialAlreadyPassed':a['M']<=5,'priorRounds':{'count':len(history)-1,'minimumM':min(h['M'] for h in history[:-1]) if len(history)>1 else None,'lastM':history[-2]['M'] if len(history)>1 else None},'tolerances':{'coverageAcceptanceKm2':1e-10,'auditAreaKm2':1e-8,'positiveBoundaryKm':1e-9,'pickupCrossKm2':1e-10,'mapDecimals':6},'rowSchema':['id','count','localMedianPercent','originalMeshNeighbors','serviceNeighbors','clippedCentroid','orderedHexagonVertices','underlyingRatio','clippedRatio'],'cells':[]}
for label,r in [('initial',a),('final',b)]:out[label].update({'meanLoad':sum(r['counts'])/100,'populationVariance':float(np.var(r['counts'])),'minLoad':min(r['counts']),'maxLoad':max(r['counts']),'emptyCells':r['counts'].count(0),'isolatedRegions':sum(not n for n in r['neighbors']),'positiveAreaRegions':100})
for i,c in enumerate(b['cells']):out['cells'].append([i,c['count'],round(b['localMedians'][i],9) if isinstance(b['localMedians'][i],float) else b['localMedians'][i],b['meshNeighbors'][i],b['neighbors'][i],[round(v,6) for v in c['clippedCentroid']],[[round(v,6) for v in z] for z in c['vertices']],round(c['underlyingRatio'],9),round(c['clippedRatio'],9)])
out['checks']='Actual full-precision independent audit: 100 positive-area service cells, strict convex six-sided underlying cells, ratio bounds, full island coverage, no overlaps, no isolated regions, 5983 unique assignments. Rounded map coordinates are not the audit input. Infinity encoded as string.'
(p/'transfer100.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False))
fig,axs=plt.subplots(1,2,figsize=(12,13));norm=Normalize(0,150);cmap=plt.get_cmap('viridis')
for ax,r,title in zip(axs,[a,b],['100 cells: repaired regular initialization',f'100 cells: first passing round {b["round"]}']):
 for c in r['cells']:
  s=Polygon(c['vertices']).intersection(dom)
  for g in ([s] if s.geom_type=='Polygon' else s.geoms):
   if g.geom_type!='Polygon':continue
   x,y=g.exterior.xy;ax.fill(x,y,color=cmap(norm(c['count'])),ec='white',lw=.45)
   for hole in g.interiors:x,y=hole.xy;ax.fill(x,y,color='white')
  x,y=c['clippedCentroid'];ax.text(x,y,str(c['count']),fontsize=4.4,ha='center',va='center',color='black',bbox={'facecolor':'white','alpha':.75,'pad':.1,'edgecolor':'none'})
 x,y=dom.exterior.xy;ax.plot(x,y,c='black',lw=.4);q=P[[309,4705,5212]];ax.scatter(q[:,0],q[:,1],marker='x',c='red',s=20,zorder=10);ax.set_aspect('equal');ax.set_xlim(-1,10);ax.set_ylim(-1,21);ax.set_title(title+'\nM='+f'{r["M"]:.3f}%'+f'; loads {min(r["counts"])}–{max(r["counts"])}',fontsize=10);ax.set_xlabel('km');ax.set_ylabel('km north');ax.plot([0,2],[-.6,-.6],c='black');ax.text(1,-.4,'2 km',ha='center',fontsize=8);ax.annotate('N',xy=(9,20.3),xytext=(9,19),ha='center',arrowprops={'arrowstyle':'->'})
fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=axs,label='Pickup count (colors saturate above 150)',shrink=.7);fig.suptitle('Fresh 100-cell compact hexagon simulation • authoritative Manhattan island\n5,983 assigned pickups; 3 outside land marked × • labels show loads',fontsize=12)
fig.savefig(p/'median100_map.png',dpi=180,bbox_inches='tight');fig.savefig(p/'median100_map.pdf',bbox_inches='tight')
with zipfile.ZipFile(p/'Manhattan_100_Compact_Hexagons.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in p.iterdir():
  if f.is_file() and f.suffix!='.zip' and f.name!='anneal':z.write(f,'work/median100/'+f.name)
 for f in ['work/median38/anneal.cpp','work/median38/audit.py','Manhattan_Pickups_2015-01-15_0800-0815.json','work/verified38/main_island_km.geojson','work/verified38/assessment.json','work/verified38/boundary_metadata.json']:z.write(f,f)
print('FINAL',b['round'],b['M'],'bytes',len((p/'transfer100.json').read_bytes()),'prior min',out['priorRounds']['minimumM'])
