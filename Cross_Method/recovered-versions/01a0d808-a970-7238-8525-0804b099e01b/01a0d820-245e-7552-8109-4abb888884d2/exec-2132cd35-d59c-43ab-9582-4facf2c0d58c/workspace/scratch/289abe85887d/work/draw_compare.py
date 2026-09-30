import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.path import Path
from matplotlib.patches import PathPatch

d=json.load(open('work/compare_data.json'))
fig,axes=plt.subplots(1,2,figsize=(13.8,12),constrained_layout=True)
palette=['#8cc7b5','#e9ac93','#b4addd','#efce85','#91b5d9','#c7d99a','#deaac4','#a8ccce']
shore=np.array(d['outline']);path=Path(np.vstack([shore,shore[0]]))
pts=np.array(d['pts'])
for ax,items,title in zip(axes,[d['merged'],d['cells']],['K-means + merging',f"Local hexagon rule · {d['rounds']} rounds"]):
    clip=PathPatch(path,transform=ax.transData)
    for k,g in enumerate(items):
        for poly in (g['polys'] if 'polys' in g else [g['poly']]):
            if len(poly)<3:continue
            patch=Polygon(poly,closed=True,facecolor=palette[k%len(palette)],edgecolor='none',alpha=.78)
            patch.set_clip_path(clip)
            ax.add_patch(patch)
    ax.scatter(pts[:,0],pts[:,1],s=.45,c='#28323e',alpha=.27,rasterized=True,zorder=3)
    for g in items:
        if g['label'] is not None:
            ax.text(*g['label'],str(g['size']),ha='center',va='center',fontsize=6.5,
                    color='#172735',weight='bold',zorder=5,bbox=dict(facecolor='white',alpha=.65,edgecolor='none',pad=.5))
    ax.plot(*shore.T,color='#253d50',lw=1.2)
    ax.plot([shore[-1,0],shore[0,0]],[shore[-1,1],shore[0,1]],color='#253d50',lw=1.2)
    ax.set(xlim=(-.35,d['W']+.5),ylim=(-.3,d['H']+1.35),aspect='equal',title=title)
    ax.set_axis_off()
fig.suptitle(f"Manhattan taxi pickups, 8:00–8:15 · {len(pts):,} pickups · {len(d['cells'])} regions",fontsize=17,weight='bold')
fig.text(.5,.03,f"Population variance: merging {d['variance']['merge']:,.0f}  ·  hexagons {d['variance']['hex']:,.0f}     |     Lowest hexagon shape score: {d['shape']:.3f}",ha='center',fontsize=11)
fig.savefig('Manhattan_Taxi_Regions_Local_Rule_Comparison.png',dpi=200,facecolor='#f8fafb')
