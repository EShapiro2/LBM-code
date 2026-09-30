import json,sys,datetime,re,os
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
from shapely.geometry import Polygon
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from audit import audit,dom,P
p=Path('work/median100');f=p/'balance.json.checkpoint.json'
with f.open('rb') as h:raw=h.read();stamp=os.fstat(h.fileno()).st_mtime
s=json.loads(raw);r=s['round'];snap=p/f'interim_round_{r}.json';snap.write_bytes(raw);a=audit(snap);json.dump(a,open(p/f'interim_round_{r}_audit.json','w'),indent=2)
proc=[]
for q in Path('/proc').iterdir():
 if not q.name.isdigit():continue
 try:
  argv=(q/'cmdline').read_bytes().split(b'\0')
  if argv and argv[0]==b'work/median100/anneal':proc.append({'pid':int(q.name),'state':next(v.split(':',1)[1].strip() for v in (q/'status').read_text().splitlines() if v.startswith('State:'))})
 except (OSError,StopIteration):pass
hist=[(int(x),float(y)) for x,y in re.findall(r'CHECK (\d+) M (\S+)',(p/'balance.log').read_text()) if int(x)<=r]
out={'stage':'interim_100_cell_snapshot','status':'UNFINISHED','round':r,'checkpointTimeNY':datetime.datetime.fromtimestamp(stamp,ZoneInfo('America/New_York')).isoformat(),'M':a['M'],'bestPriorOrCurrentM':min(v for _,v in hist),'processes':proc,'session':44581,'K':100,'records':5986,'owned':a['uniqueAssigned'],'outsideIndices':[309,4705,5212],'emptyCells':a['counts'].count(0),'minLoad':min(a['counts']),'maxLoad':max(a['counts']),'cv':a['cv'],'centroidRmsKm':a['centroidRmsKm'],'maxUnderlyingRatio':a['maxUnderlyingRatio'],'maxClippedRatio':a['maxClippedRatio'],'uncoveredKm2':a['coverageResidualKm2'],'overlapKm2':a['overlapKm2'],'underlyingOverlapKm2':a['underlyingOverlapKm2'],'minServiceAreaKm2':a['minServiceAreaKm2'],'positiveAreaCells':a['positiveAreaRegions'],'multipleAssignments':a['multipleAssigned'],'convexSixSided':a['convexSixSided'],'countsMatchSolver':a['countsMatchSimulation'],'auditPassed':a['feasible'],'units':'km; same verified NYC DCP 26b island and hole, north-up frame','displayDecimals':5,'audit':'Full precision; displayed coordinates rounded. Infinity encoded as string. Solver untouched.','rowSchema':['id','count','localMedianPercent','serviceNeighbors','clippedCentroid','orderedUnderlyingVertices'],'cells':[]}
for i,c in enumerate(a['cells']):out['cells'].append([i,c['count'],round(a['localMedians'][i],5) if isinstance(a['localMedians'][i],float) else a['localMedians'][i],a['neighbors'][i],[round(v,5) for v in c['clippedCentroid']],[[round(v,5) for v in z] for z in c['vertices']]])
fout=p/f'interim_round_{r}_transfer.json';fout.write_text(json.dumps(out,separators=(',',':'),allow_nan=False))
fig,ax=plt.subplots(figsize=(7,12));norm=Normalize(0,120);cmap=plt.get_cmap('viridis')
for c in a['cells']:
 g=Polygon(c['vertices']).intersection(dom)
 for poly in ([g] if g.geom_type=='Polygon' else g.geoms):
  if poly.geom_type!='Polygon':continue
  x,y=poly.exterior.xy;ax.fill(x,y,color=cmap(norm(c['count'])),ec='white',lw=.4)
  for hole in poly.interiors:x,y=hole.xy;ax.fill(x,y,color='white')
 x,y=c['clippedCentroid'];ax.text(x,y,str(c['count']),fontsize=4.8,ha='center',va='center',bbox={'facecolor':'white','alpha':.8,'pad':.1,'edgecolor':'none'})
x,y=dom.exterior.xy;ax.plot(x,y,c='black',lw=.4);q=P[[309,4705,5212]];ax.scatter(q[:,0],q[:,1],marker='x',c='red',s=22,zorder=10);ax.set_aspect('equal');ax.set_xlim(-1,10);ax.set_ylim(-1,21);ax.set_xlabel('km');ax.set_ylabel('km north');ax.plot([0,2],[-.6,-.6],c='black');ax.text(1,-.4,'2 km',ha='center',fontsize=8);ax.annotate('N',xy=(9,20.3),xytext=(9,19),ha='center',arrowprops={'arrowstyle':'->'});ax.set_title(f'INTERIM — 100 service regions — round {r}\nM={a["M"]:.4f}% (target ≤5%); labels show loads\n5,983 owned pickups; 3 outside land marked ×',fontsize=11);fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,label='Pickup count',shrink=.65);fig.tight_layout();png=p/f'interim_round_{r}_map.png';fig.savefig(png,dpi=160,bbox_inches='tight');print(json.dumps({'json':str(fout),'png':str(png),'bytes':fout.stat().st_size,'round':r,'M':a['M'],'processes':proc}))
