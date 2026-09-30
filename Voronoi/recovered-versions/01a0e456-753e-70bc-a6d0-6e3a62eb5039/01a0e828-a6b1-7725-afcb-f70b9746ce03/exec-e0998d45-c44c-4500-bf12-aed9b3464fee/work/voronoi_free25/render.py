import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from shapely.geometry import Polygon
O=Path('outputs/voronoi_free25');x=json.load(open(O/'initial.json'));y=json.load(open(O/'final.json'));d=json.load(open('work/voronoi25/input.json'));P=np.array(d['P'])
fig,axs=plt.subplots(1,2,figsize=(12,13),sharex=True,sharey=True);vmax=max(max(z['counts']) for z in [x,y])
for ax,z,title in zip(axs,[x,y],['Before — saved round 50','After 25 single-center steps\nNew neighbors allowed']):
 polys=[np.array(p) for p in z['cells']];c=np.array(z['centers']);pc=PolyCollection(polys,array=np.array(z['counts']),cmap='YlOrRd',edgecolors='#48535a',linewidths=.5,clim=(0,vmax));ax.add_collection(pc);ax.scatter(c[:,0],c[:,1],s=7,c='#08668a',zorder=3)
 for poly,w in zip(polys,z['counts']):
  q=np.array(Polygon(poly).centroid.coords)[0];ax.annotate(str(w),q,fontsize=6,ha='center',va='center',zorder=4,bbox=dict(facecolor='white',alpha=.7,pad=.1,edgecolor='none'))
 ax.plot(P[:,0],P[:,1],c='black',lw=1);ax.set(xlim=(P[:,0].min()-.3,P[:,0].max()+.3),ylim=(P[:,1].min()-.3,P[:,1].max()+.3),xlabel='x (km)',ylabel='y (km)',title=title);ax.set_aspect('equal')
fig.colorbar(pc,ax=axs,fraction=.025,pad=.025,label='Dot count');fig.savefig(O/'Voronoi_Free25Steps_maps.png',dpi=180,bbox_inches='tight');plt.close(fig)
states=[x]+[json.load(open(O/f'step_{i:02d}.json')) for i in range(1,26)];keys=['max_Gmax','max_Gavg','max_Gmed','median_Gmax','median_Gavg','median_Gmed'];fig,axs=plt.subplots(2,3,figsize=(12,6.5),sharex=True)
for ax,k in zip(axs.flat,keys):
 ax.plot(range(26),[z['metrics'][k] for z in states],marker='o',ms=3);ax.set_title(k.replace('_',' '));ax.set_ylabel('Dots');ax.set_xlabel('Single-center steps');ax.grid(alpha=.3);ax.set_xlim(0,25)
fig.suptitle('New neighbors allowed — 25 steps from saved round 50');fig.tight_layout();fig.savefig(O/'Voronoi_Free25Steps_measures.png',dpi=180);plt.close(fig)
