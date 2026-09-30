import importlib.util,json,numpy as np
from pathlib import Path
sp=importlib.util.spec_from_file_location('R',Path(__file__).parent/'run.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
p=R.O;d=json.load(open(R.WPATH/'input.json'));P=R.Polygon(d['P']);pts=np.array(d['points']);c=np.array(json.load(open(p/'checkpoint_58.json'))['centers']);i=47
logs=[json.loads(l) for l in (p/'steps.jsonl').read_text().splitlines()]
for row in logs:
 if row['round']!=59:continue
 if row['site']==i:break
 c[row['site']]=row['new_center']
polys,nb=R.base.geometry(c,P);W,_=R.base.counts(c,pts);gc,gg,D,rad=R.gradients(c,i,P,polys,nb,W)
result={'turn':row['position']+1,'row':row,'weight_at_turn':int(W[i]),'circularity_at_turn':R.circularity(polys[i]),'C_gradient':gc.tolist(),'G_gradient':gg.tolist(),'neighbors_at_turn':{str(j):int(W[j]) for j in nb[i]}}
for name,u in [('down',np.array([0.,-1.])),('gap_direction',-gg/np.linalg.norm(gg))]:
 pc=R.PathCheck(c,i,P,W,u,.05,polys,nb[i]);C,G=pc.evaluate(.05);ok,re=pc.check(.05);result[name]=dict(C0=pc.C0,C1=C,G0=pc.G0,G1=G,accepted=ok)
Path('outputs/voronoi_tradeoff59/tracked_cell.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
