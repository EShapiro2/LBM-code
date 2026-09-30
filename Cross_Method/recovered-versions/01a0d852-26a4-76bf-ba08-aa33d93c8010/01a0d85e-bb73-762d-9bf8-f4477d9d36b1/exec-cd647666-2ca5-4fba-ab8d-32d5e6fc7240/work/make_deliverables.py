import json,math, pathlib, shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,PathPatch
from matplotlib.path import Path
root=pathlib.Path('work/Manhattan_Balanced_Hexagons');root.mkdir(exist_ok=True)
D=json.load(open('work/native_input.json'));S=json.load(open('work/guided020_best.json'));B=json.load(open('work/compare_data.json'));audit=json.load(open('work/verification.json'))
V=list(zip(S['verticesX'],S['verticesY']));C=[[V[v] for v in r] for r in D['cells']];pts=np.array(D['points']);shore=np.array(D['outline']);path=Path(np.vstack([shore,shore[0]]))
def cross(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
labels=[]
for c in C:
 own=[p for p in pts if all(cross(a,b,p)>=-1e-10 for a,b in zip(c,c[1:]+c[:1]))];labels.append(np.mean(own,axis=0).tolist())
palette=['#8cc7b5','#e9ac93','#b4addd','#efce85','#91b5d9','#c7d99a','#deaac4','#a8ccce']
fig,axes=plt.subplots(1,2,figsize=(11.5,11.5),constrained_layout=True)
items=[B['merged'],[dict(poly=c,label=l,size=n) for c,l,n in zip(C,labels,S['counts'])]]
for ax,groups,title in zip(axes,items,['K-means + merging\nVariance 1,374','Local atomic hexagon rule\nVariance 0.2493 — integer optimum']):
 clip=PathPatch(path,transform=ax.transData)
 for k,g in enumerate(groups):
  for poly in g.get('polys',[g.get('poly')]):
   patch=Polygon(poly,closed=True,facecolor=palette[k%len(palette)],edgecolor='#ffffff',linewidth=.65,alpha=.86);patch.set_clip_path(clip);ax.add_patch(patch)
 ax.scatter(pts[:,0],pts[:,1],s=.4,c='#28323e',alpha=.25,rasterized=True,zorder=3)
 for g in groups:
  if g['label'] is not None:ax.text(*g['label'],str(g['size']),ha='center',va='center',fontsize=6.5,color='#172735',weight='bold',zorder=5,bbox=dict(facecolor='white',alpha=.7,edgecolor='none',pad=.5))
 ax.plot(*np.vstack([shore,shore[0]]).T,color='#253d50',lw=1)
 ax.set(xlim=(-.4,9.65),ylim=(-.3,20.2),aspect='equal',title=title);ax.set_axis_off()
fig.suptitle('Same 5,986 Manhattan pickups · 8:00–8:15 · 38 regions',fontsize=16,weight='bold')
fig.supxlabel('Balanced result: 18 hexagons × 157 pickups + 20 hexagons × 158 pickups\nAll hexagons convex; no overlaps; full island coverage. Colours are clipped to the shoreline.',fontsize=10)
fig.savefig('Manhattan_Balanced_Hexagons_Comparison.png',dpi=180,facecolor='#f8fafb');plt.close(fig)
shutil.copy('Manhattan_Balanced_Hexagons_Comparison.png',root/'comparison.png')
for src,dst in [('work/local_anneal.cpp','local_anneal.cpp'),('work/input_020_best.txt','start.txt'),('work/native020_best.json','start.json'),('work/guided020_best.json','balanced.json'),('work/verification.json','verification.json'),('work/native_input.json','geometry.json'),('work/audit_solution.py','audit_solution.py')]:shutil.copy(src,root/dst)
# Adapt independent audit to this self-contained bundle.
s=(root/'audit_solution.py').read_text().replace("'work/native_input.json'","'geometry.json'").replace("'work/guided020_best.json'","'balanced.json'").replace("'work/verification.json'","'verification.json'");(root/'audit_solution.py').write_text(s)
(root/'run.sh').write_text('#!/bin/sh\nset -eu\ncd "$(dirname "$0")"\ng++ -O3 -std=c++17 local_anneal.cpp -o local_anneal\n./local_anneal start.txt reproduced.json 500 0.20 0.005 11\n')
(root/'run.sh').chmod(0o755)
