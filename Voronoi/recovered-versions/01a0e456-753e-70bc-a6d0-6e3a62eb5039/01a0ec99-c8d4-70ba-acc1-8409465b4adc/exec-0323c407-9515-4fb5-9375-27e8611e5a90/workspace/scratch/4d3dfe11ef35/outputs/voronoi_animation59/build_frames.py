import importlib.util,json,numpy as np
from pathlib import Path
sp=importlib.util.spec_from_file_location('R','work/voronoi_tradeoff75/run.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
p=R.O;start=json.load(open(p/'checkpoint_58.json'));end=json.load(open(p/'checkpoint_59.json'));d=json.load(open(R.WPATH/'input.json'));P=R.Polygon(d['P']);pts=np.array(d['points']);c=np.array(start['centers']);logs=[x for x in map(json.loads,(p/'steps.jsonl').read_text().splitlines()) if x['round']==59];frames=[];previous={}
for t in range(101):
 row=logs[t-1] if t else None
 if row:
  assert c[row['site']].tolist()==row['old_center'];c[row['site']]=row['new_center']
 ps,nb=R.base.geometry(c,P);W,owners=R.base.counts(c,pts);polys={};labels={}
 for i,poly in enumerate(ps):
  coords=np.round(np.array(poly.normalize().exterior.coords),5).tolist()
  if previous.get(str(i))!=coords:polys[str(i)]=coords;labels[str(i)]=np.round(np.array(poly.centroid.coords)[0],5).tolist()
  previous[str(i)]=coords
 fr=dict(t=t,polys=polys,labels=labels,counts=W.tolist(),C=[round(R.circularity(poly),5) for poly in ps])
 if row:fr.update(site=row['site'],center=row['new_center'],old=row['old_center'],kind=row['kind'],status=row['status'],reason=row.get('reason'),acceptance=row.get('acceptance'),distance=row['actual'])
 else:fr['centers']=c.tolist()
 frames.append(fr)
assert c.tolist()==end['centers'] and W.tolist()==end['counts'];assert [r['site'] for r in logs]==end['permutations'][-1]
out=dict(round=59,frames=frames,domain=d['P'],records=len(pts),tracked=47,maxCount=max(max(f['counts']) for f in frames))
f=Path('outputs/voronoi_animation59/frames.json');f.write_text(json.dumps(out,separators=(',',':')));print('VERIFIED',len(frames),'frames',f.stat().st_size,'bytes')
