import json,math,hashlib,collections
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
D=Path('work/four_compare'); src=Path('Manhattan_Pickups_2015-01-15_0800-0815.json'); inp=json.loads(src.read_text()); pts=np.array(inp['points']); old=json.load(open('work/compare_data.json')); geom=json.load(open('work/Manhattan_Balanced_Hexagons/geometry.json')); full=json.load(open('Manhattan_Vertex_Only_Full_Outputs.json'))['runs'][-1]['result']; local=next(r for r in full['results'] if r['method']=='local' and r['seed']==11); lloyd=json.load(open(D/'lloyd.json'))
assert np.array_equal(pts,np.array(old['pts'])) and np.array_equal(pts,np.array(geom['points']))
v=np.array(list(zip(geom['verticesX'],geom['verticesY']))); hexes=[v[c].tolist() for c in geom['cells']]
def membership(groups):
 own=np.full(len(pts),-1); hits=np.zeros(len(pts),int)
 for i,polys in enumerate(groups):
  inside=np.zeros(len(pts),bool)
  for poly in polys:
   p=np.array(poly); e=np.roll(p,-1,axis=0)-p; z=e[:,0,None]*(pts[:,1]-p[:,1,None])-e[:,1,None]*(pts[:,0]-p[:,0,None]); inside |= (z>=-1e-9).all(axis=0)|(z<=1e-9).all(axis=0)
  hits+=inside;own[(own<0)&inside]=i
 assert (own>=0).all(), int((own<0).sum())
 return own,{'unassigned':int((own<0).sum()),'multiple_regions':int((hits>1).sum())}
groups=[g['polys'] for g in old['merged']]; oo,oa=membership(groups); ho,ha=membership([[p] for p in hexes]);assert np.array_equal(np.bincount(oo,minlength=38),[g['size'] for g in old['merged']])
def metrics(own,n,ps=None):
 own=np.array(own);loads=np.bincount(own,minlength=n); centers=np.zeros((n,2));
 for i in range(n):
  if loads[i]:centers[i]=pts[own==i].mean(axis=0)
 m={'count':len(pts),'regions':n,'cv':float(loads.std()/loads.mean()),'population_variance':float(loads.var()),'min':int(loads.min()),'max':int(loads.max()),'empty':int((loads==0).sum()),'rms_to_assigned_pickup_centroid_km':float(np.sqrt(((pts-centers[own])**2).sum(axis=1).mean())),'rms_to_operational_center_km':None,'loads':loads.tolist()}
 if ps is not None:m['rms_to_operational_center_km']=float(np.sqrt(((pts-np.array(ps)[own])**2).sum(axis=1).mean()))
 return m
ms=[metrics(oo,38),metrics(ho,38),metrics(local['own'],100,local['ps']),metrics(lloyd['own'],100,lloyd['ps'])]
# Union each historical group by splitting shared edges at all collinear vertices, then cancelling interiors.
def union_loops(polys):
 points=np.array([p for poly in polys for p in poly]);edges=collections.Counter();coords={}
 def key(p):
  k=tuple(np.round(p,8));coords[k]=p.tolist();return k
 for poly in polys:
  for a,b in zip(np.array(poly),np.roll(np.array(poly),-1,axis=0)):
   ab=b-a;den=ab@ab
   if den<1e-20:continue
   t=(points-a)@ab/den; cr=ab[0]*(points[:,1]-a[1])-ab[1]*(points[:,0]-a[0]); ix=np.where((abs(cr)<1e-7)&(t>=-1e-9)&(t<=1+1e-9))[0];ks=[]
   for j in sorted(ix,key=lambda j:t[j]):
    k=key(points[j]);
    if not ks or k!=ks[-1]:ks.append(k)
   for c,d in zip(ks,ks[1:]):edges[tuple(sorted((c,d)))]+=1
 remain={e for e,num in edges.items() if num%2};loops=[]
 while remain:
  a,b=min(remain);remain.remove((a,b));chain=[a,b]
  while chain[-1]!=chain[0]:
   opts=sorted(e for e in remain if chain[-1] in e);assert opts,'open boundary';e=opts[0];remain.remove(e);chain.append(e[1] if e[0]==chain[-1] else e[0])
  p=[coords[k] for k in chain[:-1]]
  # remove collinear subdivision points
  clean=[]
  for i,b in enumerate(p):
   a=np.array(p[i-1]);b=np.array(b);c=np.array(p[(i+1)%len(p)]);u=b-a;w=c-b
   if abs(u[0]*w[1]-u[1]*w[0])>1e-7:clean.append(b.tolist())
  loops.append(clean)
 return loops
unions=[union_loops(g) for g in groups]
result={'actual_execution':True,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'date':inp['date'],'window':inp['window'],'units':'km','sample_indices':[i*len(pts)//300 for i in range(300)],'historical_checks':{'merged':oa,'balanced':ha},'mesh':full['mesh'],'solutions':[],'distance_definition':'Common RMS: each pickup to centroid of pickups in its actual assigned region. Operational RMS: pickup to final agent/center; unavailable for historical regions.'}
names=['Historical K-means + merging','Historical balanced convex hexagons','Triangle-constrained pooled centroid','Lloyd with empty-center reseeding']
for i,m in enumerate(ms):
 result['solutions'].append({'name':names[i],'status':'recovered geometry; freshly verified metrics' if i<2 else 'recovered completed run' if i==2 else 'fresh run','seed':11 if i==2 else None,'termination':local['termination'] if i==2 else lloyd['termination'] if i==3 else None,'lastSweep':local['lastSweep'] if i==2 else lloyd['lastSweep'] if i==3 else None,**m})
result['reseed_procedure']=lloyd['reseedProcedure'];result['reseed_count']=lloyd['reseedCount'];result['reseed_log']=lloyd['reseedLog'];json.dump(result,open(D/'results.json','w'),separators=(',',':'))
# Shared north-up map coordinates; rendering precision only is rounded to 0.1px.
W=880;H=628;scale=16.5;xlo=-1.5;yhi=20.4
xy=lambda p:((p[0]-xlo)*scale,(yhi-p[1])*scale)
fmt=lambda x:('%0.1f'%x).rstrip('0').rstrip('.')
def path(poly,close=True):
 return 'M'+' '.join((','.join(map(fmt,xy(p)))) for p in poly)+('Z' if close else '')
colors=['#f1f1f1','#d9e9f4','#91bfdb','#4b9b83','#f0aa54','#cb5145']
def cat(load,mean):return 0 if load==0 else 1 if load<.5*mean else 2 if load<mean else 3 if load<1.5*mean else 4 if load<2*mean else 5
sample=pts[result['sample_indices']]; outline=old['outline'];shore=path(outline);dots=''.join('M'+','.join(map(fmt,xy(p)))+'h.1' for p in sample)
s=['<svg xmlns="http://www.w3.org/2000/svg" width="880" height="628" viewBox="0 0 880 628">','<style>text{font:11px sans-serif;fill:#23313b}.title{font-size:14px;font-weight:bold}.small{font-size:10px}.edge{fill:none;stroke:#596574;stroke-width:.65} </style>',f'<defs><path id="land" d="{shore}"/><clipPath id="clip"><use href="#land"/></clipPath><path id="dots" d="{dots}"/></defs>','<path fill="white" d="M0 0H880V628H0Z"/>','<text x="14" y="20" class="title">Manhattan pickups · 15 Jan 2015, 08:00–08:15 · n=5,986</text>','<text x="14" y="37">Same scale, north up; identical 300-point sample. Calculations use all pickups.</text>']
titles=['38 regions · merged','38 cells · balanced','100 vertices · local','100 centers · Lloyd'];sub=['Recovered geometry','Recovered geometry','Seed 11 · stopped 73','Fresh run · stopped 27']
for j in range(4):
 offset=10+j*218;m=ms[j];mean=len(pts)/m['regions'];s.extend([f'<g transform="translate({offset},0)"><text x="0" y="59" class="title">{titles[j]}</text><text x="0" y="74" class="small">{sub[j]}</text><g transform="translate(0,83)">','<use href="#land" fill="#f6f8fa" stroke="#9aa6af" stroke-width=".8"/>'])
 if j<2:
  for i,loops in enumerate(unions if j==0 else [[p] for p in hexes]):
   p=''.join(path(l) for l in loops);s.append(f'<path d="{p}" fill="{colors[cat(m["loads"][i],mean)]}" stroke="#5b6873" stroke-width=".6" clip-path="url(#clip)"/>')
 else:
  ps=local['ps'] if j==2 else lloyd['ps']
  if j==2:
   edges=''.join(path([ps[a],ps[b]],False) for a,nei in enumerate(full['adjacency']) for b in nei if a<b);s.append(f'<path class="edge" d="{edges}"/>')
  for c in range(6):
   p=''.join('M'+','.join(map(fmt,xy(p)))+'h.1' for i,p in enumerate(ps) if cat(m['loads'][i],mean)==c)
   if p:s.append(f'<path d="{p}" fill="none" stroke="{colors[c]}" stroke-width="5" stroke-linecap="round"/>')
  if j==2:
   p=''.join('M'+','.join(map(fmt,xy(ps[i])))+'h.1' for i,a in enumerate(full['adjacency']) if len(a)!=3);s.append(f'<path d="{p}" stroke="#27313b" stroke-width="1.4" stroke-linecap="round"/>')
 s.extend(['<use href="#dots" stroke="#151b24" stroke-width="1.2" stroke-linecap="round" opacity=".52"/>','</g>'])
 lines=[f'CV {m["cv"]:.6f} · variance {m["population_variance"]:.3f}',f'Load {m["min"]}–{m["max"]} · empty {m["empty"]}',f'Centroid RMS {m["rms_to_assigned_pickup_centroid_km"]:.6f} km','Agent RMS '+(f'{m["rms_to_operational_center_km"]:.6f} km' if j>=2 else 'not defined')]
 for k,t in enumerate(lines):s.append(f'<text x="0" y="{450+15*k}">{t}</text>')
 loads=sorted(m['loads']);p=''.join(('M' if i==0 else 'L')+f'{fmt(i*198/(len(loads)-1))},{fmt(550-load/mean*13)}' for i,load in enumerate(loads));s.extend([f'<path d="M0 537H198" stroke="#9aa6af" stroke-dasharray="2 2"/><path d="{p}" fill="none" stroke="#365c82" stroke-width="1.4"/>','<text x="0" y="565" class="small">Sorted load / mean (dashed = 1)</text></g>'])
s.append('<text x="14" y="585" class="small">Color = load / mean:</text>')
for i,label in enumerate(['empty','0–0.5','0.5–1','1–1.5','1.5–2','≥2']):s.append(f'<path fill="{colors[i]}" d="M{125+i*87}575h12v12h-12Z"/><text x="{141+i*87}" y="585" class="small">{label}</text>')
s.extend(['<text x="14" y="604" class="small">Old boundaries are actual cells, clipped to land. Local edges show fixed topology, not ownership boundaries; black cores = fixed vertices.</text>','<text x="14" y="620" class="small">Centroid RMS uses actual ownership in every panel. Agent RMS uses final vertex/center locations. Each map: 1 km = 16.5 px.</text>','</svg>']);svg=''.join(s);(D/'comparison.svg').write_text(svg)
# Equivalent PNG and PDF using full precision map geometry.
fig,axs=plt.subplots(1,4,figsize=(14,9));fig.suptitle('Manhattan · 5,986 pickups · 2015-01-15 08:00–08:15',fontsize=15)
for j,ax in enumerate(axs):
 m=ms[j];mean=len(pts)/m['regions'];land=Polygon(outline,facecolor='#f6f8fa',edgecolor='#9aa6af',lw=.7);ax.add_patch(land)
 if j<2:
  for i,loops in enumerate(unions if j==0 else [[p] for p in hexes]):
   for poly in loops:
    patch=Polygon(poly,facecolor=colors[cat(m['loads'][i],mean)],edgecolor='#5b6873',lw=.5);patch.set_clip_path(land);ax.add_patch(patch)
 else:
  ps=np.array(local['ps'] if j==2 else lloyd['ps'])
  if j==2:
   for a,nei in enumerate(full['adjacency']):
    for b in nei:
     if a<b:ax.plot(ps[[a,b],0],ps[[a,b],1],color='#596574',lw=.55)
  ax.scatter(ps[:,0],ps[:,1],c=[colors[cat(l,mean)] for l in m['loads']],s=26,zorder=3)
  if j==2:
   fixed=[i for i,a in enumerate(full['adjacency']) if len(a)!=3];ax.scatter(ps[fixed,0],ps[fixed,1],s=3,c='#27313b',zorder=4)
 ax.scatter(sample[:,0],sample[:,1],s=2,c='#151b24',alpha=.52,zorder=5);ax.set_xlim(-1.5,11);ax.set_ylim(-1,20.4);ax.set_aspect('equal');ax.set_title(titles[j]+'\n'+sub[j],fontsize=11);ax.axis('off');ax.text(0,-.035,f'CV {m["cv"]:.6f}  Var {m["population_variance"]:.3f}\nLoad {m["min"]}–{m["max"]}; empty {m["empty"]}\nCentroid RMS {m["rms_to_assigned_pickup_centroid_km"]:.6f} km\nAgent RMS '+(f'{m["rms_to_operational_center_km"]:.6f} km' if j>=2 else 'not defined'),transform=ax.transAxes,fontsize=9,va='top')
fig.text(.06,.06,'Colors: empty, <0.5, <1, <1.5, <2, ≥2 times mean load. Same 300 real pickups sampled on each map.\nHistorical boundaries clipped to land. Local mesh edges are topology, not ownership. Black cores: fixed vertices.\nCentroid RMS uses actual assignments; agent RMS uses final operational centers. North up; same geographic scale.',fontsize=9);fig.savefig(D/'comparison.png',dpi=180,bbox_inches='tight');fig.savefig(D/'comparison.pdf',bbox_inches='tight');print(json.dumps({'svg_chars':len(svg),'metrics':result['solutions'],'checks':result['historical_checks']},indent=2))
