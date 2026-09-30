import json,csv,collections
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
O=Path('outputs/voronoi25');D=json.load(open('work/voronoi25/input.json'));P=np.array(D['P']);pts=np.array(D['points'])
states=[json.load(open(p)) for p in sorted(O.glob('checkpoint_*.json'))]
keys=['max_Gmax','max_Gavg','max_Gmed','median_Gmax','median_Gavg','median_Gmed']
rows=[dict(round=x['round'],timestamp=x['timestamp'],**x['metrics']) for x in states]
(O/'measures.json').write_text(json.dumps(rows,indent=2))
with (O/'measures.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['round','timestamp']+keys);w.writeheader();w.writerows(rows)

def draw(ax,x,title,vmax):
 polys=[np.array(p) for p in x['cells']];c=np.array(x['centers']);W=x['counts']
 pc=PolyCollection(polys,array=np.array(W),cmap='YlOrRd',edgecolors='#48535a',linewidths=.5,clim=(0,vmax));ax.add_collection(pc)
 ax.scatter(c[:,0],c[:,1],s=6,c='#08668a',zorder=3)
 for co,poly,w in zip(c,polys,W):
  # labels at actual site, with small offset to leave marker visible
  ax.annotate(str(w),co,xytext=(2,2),textcoords='offset points',fontsize=5.7,color='black',zorder=4,bbox=dict(facecolor='white',alpha=.65,pad=.1,edgecolor='none'))
 ax.plot(P[:,0],P[:,1],color='black',lw=1);ax.set(xlim=(P[:,0].min()-.3,P[:,0].max()+.3),ylim=(P[:,1].min()-.3,P[:,1].max()+.3),xlabel='x (km)',ylabel='y (km)',title=title);ax.set_aspect('equal');return pc
x=states[-1];fig,ax=plt.subplots(figsize=(7,12));pc=draw(ax,x,f"Voronoi cells — round {x['round']}\n{len(pts):,} pickups; labels = dot counts",max(x['counts']));fig.colorbar(pc,ax=ax,fraction=.035,pad=.02,label='Dot count');fig.tight_layout();fig.savefig(O/'latest_map.png',dpi=170);plt.close(fig)
if x['round']==0:
 import shutil;shutil.copy2(O/'latest_map.png',O/'initial_map.png')
if x['round']==25:
 fig,axs=plt.subplots(1,2,figsize=(12,13),sharex=True,sharey=True);vmax=max(max(z['counts']) for z in [states[0],x])
 for ax,z,t in zip(axs,[states[0],x],['Initial regular lattice','After exactly 25 rounds (not convergence)']):pc=draw(ax,z,t,vmax)
 fig.colorbar(pc,ax=axs,fraction=.025,pad=.025,label='Dot count');fig.savefig(O/'before_after.png',dpi=180,bbox_inches='tight');plt.close(fig)
 fig,axs=plt.subplots(2,3,figsize=(12,6.5),sharex=True)
 for ax,k in zip(axs.flat,keys):
  ax.plot([v['round'] for v in rows],[v[k] for v in rows],marker='o',ms=3);ax.set_title(k.replace('_',' '));ax.set_ylabel('Dots');ax.set_xlabel('Completed round');ax.grid(alpha=.3);ax.set_xlim(0,25)
 fig.tight_layout();fig.savefig(O/'six_measures.png',dpi=180);plt.close(fig)
