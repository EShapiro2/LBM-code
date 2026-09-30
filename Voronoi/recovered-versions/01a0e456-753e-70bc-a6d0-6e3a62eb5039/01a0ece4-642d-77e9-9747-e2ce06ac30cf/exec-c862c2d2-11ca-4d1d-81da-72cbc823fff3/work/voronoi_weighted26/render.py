import json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import run as R
O=R.O;d=json.load(open(R.WPATH/'input.json'));P=R.Polygon(d['P']);pts=np.array(d['points']);start=json.load(open(O/'start.json'));rng=np.random.default_rng();initial=R.measure(1,np.array(start['centers']),P,pts,rng)
cp=json.load(open(O/'checkpoint.json'));n=cp['next_position'];current=R.measure(cp['batch'],np.array(cp['centers']),P,pts,rng)
completed=n%100==0;caption=f"Batch {cp['batch']} completed" if completed else f"Batch {cp['batch']} — {n%100}/100 selections"

def draw(ax,s,title,vmax):
 polys=[np.array(x) for x in s['cells']];C=np.array(s['centers']);B=np.array(s['badness_next_selection']);pc=PolyCollection(polys,array=B,cmap='YlOrRd',clim=(0,vmax),edgecolors='#52606b',linewidths=.5);ax.add_collection(pc);ax.scatter(C[:,0],C[:,1],s=7,c='#176289',zorder=3)
 for poly,b in zip(polys,B):
  q=R.Polygon(poly).centroid;ax.text(q.x,q.y,f'{b:.1f}',fontsize=5.7,ha='center',va='center',bbox=dict(facecolor='white',alpha=.6,edgecolor='none',pad=.1))
 ax.set(xlim=(-.25,9.05),ylim=(-.25,19.1),xlabel='x (km)',ylabel='y (km)',title=title);ax.set_aspect('equal');return pc
vmax=max(2,max(initial['badness_next_selection']),max(current['badness_next_selection']))
fig,ax=plt.subplots(figsize=(6,11));pc=draw(ax,current,caption+'\nBadness: lower is better; refreshed densities',vmax);fig.colorbar(pc,ax=ax,fraction=.04,pad=.02,label='Badness');fig.tight_layout();fig.savefig(O/'latest_map.png',dpi=140);fig.savefig(O/f'snapshot_{n:04d}.png',dpi=140);plt.close(fig)
states=[initial]+[json.load(open(p)) for p in sorted(O.glob('batch_*.json'))];rows=[dict(batch=s['batch'],timestamp=s['timestamp'],**s['score_summary']) for s in states]
with (O/'measures.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(O/'measures.json').write_text(json.dumps(rows,indent=2))
if n==2500:
 fig,axs=plt.subplots(1,2,figsize=(12,12),sharex=True,sharey=True)
 for ax,s,title in zip(axs,[initial,current],['Before: after weighted batch 1','After: weighted batch 26']):pc=draw(ax,s,title,vmax)
 fig.colorbar(pc,ax=axs,fraction=.025,pad=.025,label='Badness (lower is better)');fig.savefig(O/'before_after.png',dpi=170,bbox_inches='tight');plt.close(fig)
 fig,axs=plt.subplots(1,3,figsize=(12,3.8))
 for ax,k,label in zip(axs,['mean_badness','mean_circularity','mean_gap'],['Mean badness ↓','Mean circularity ↑','Mean neighbor-weight gap ↓']):
  ax.plot([r['batch'] for r in rows],[r[k] for r in rows],marker='o',ms=3);ax.set(title=label,xlabel='Completed batch');ax.grid(alpha=.3)
 fig.tight_layout();fig.savefig(O/'scores.png',dpi=180);plt.close(fig)
print('MAP',n,cp['timestamp'],current['score_summary'],flush=True)
