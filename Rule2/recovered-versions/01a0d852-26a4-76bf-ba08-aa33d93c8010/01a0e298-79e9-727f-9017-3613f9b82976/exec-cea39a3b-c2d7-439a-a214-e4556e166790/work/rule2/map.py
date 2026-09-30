import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
x=json.load(open('work/rule2/full_outputs.json'));base=json.load(open('Manhattan_Vertex_Only_Full_Outputs.json'))['runs'][-1]['result'];l=json.load(open('work/four_compare/lloyd.json'));p=np.array(json.load(open('Manhattan_Pickups_2015-01-15_0800-0815.json'))['points']);outline=json.load(open('work/compare_data.json'))['outline'];sample=p[[i*len(p)//300 for i in range(300)]]
r3=next(r for r in base['results'] if r['method']=='local' and r['seed']==11);runs=[x['results'][0],r3,l];titles=['Rule 2 · seed 11 · cap 320','Rule 3 · seed 11 · stable 73','Lloyd + reseeding · stable 27'];fig,axs=plt.subplots(1,3,figsize=(10,8),layout='constrained');colors=['#f1f1f1','#d9e9f4','#91bfdb','#4b9b83','#f0aa54','#cb5145']
for j,(ax,r) in enumerate(zip(axs,runs)):
 ps=np.array(r['ps']);loads=np.bincount(r['own'],minlength=100);ratio=loads/(len(p)/100);bins=[0 if z==0 else 1 if z<.5 else 2 if z<1 else 3 if z<1.5 else 4 if z<2 else 5 for z in ratio];ax.add_patch(Polygon(outline,facecolor='#f6f8fa',edgecolor='#9aa6af',lw=.7))
 if j<2:
  for a,nei in enumerate(base['adjacency']):
   for b in nei:
    if a<b:ax.plot(ps[[a,b],0],ps[[a,b],1],color='#596574',lw=.5)
 ax.scatter(ps[:,0],ps[:,1],c=[colors[b] for b in bins],s=28,zorder=3)
 if j<2:
  fixed=[i for i,a in enumerate(base['adjacency']) if len(a)!=3];ax.scatter(ps[fixed,0],ps[fixed,1],s=3,c='black',zorder=4)
 ax.scatter(sample[:,0],sample[:,1],s=2,c='black',alpha=.5,zorder=5);ax.set_xlim(-1.5,11);ax.set_ylim(-1,20.4);ax.set_aspect('equal');ax.set_title(titles[j],fontsize=11);ax.axis('off')
fig.suptitle('Full Manhattan data: 5,986 pickups · K=100 in every panel\nSame initial centers; 68 movable / 32 fixed for rules 2 and 3; all movable for Lloyd',fontsize=11)
fig.supxlabel('North up · same scale · same deterministic 300-point background sample\nColors: empty, <0.5, <1, <1.5, <2, ≥2 times mean load\nEdges show graph topology, not ownership boundaries; black cores mark fixed vertices.',fontsize=9)
fig.savefig('work/rule2/comparison.png',dpi=170);fig.savefig('work/rule2/comparison.svg')
