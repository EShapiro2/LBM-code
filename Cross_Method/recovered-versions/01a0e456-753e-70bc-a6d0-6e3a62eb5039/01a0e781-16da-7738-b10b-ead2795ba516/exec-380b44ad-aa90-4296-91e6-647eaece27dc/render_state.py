import json,sys,datetime
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import shape,Polygon,MultiPolygon
s=json.load(open(sys.argv[1]));a=json.load(open(sys.argv[2]));out=sys.argv[3]
p=Path('work/median100');d=json.load(open(p/'input.json'));D=shape(json.load(open('work/verified38/main_island_km.geojson')));V=list(zip(s['verticesX'],s['verticesY']))
fig,ax=plt.subplots(figsize=(6.2,11.5),dpi=150)
for i,c in enumerate(d['cells']):
 g=Polygon([V[j] for j in c]).intersection(D)
 for part in (list(g.geoms) if isinstance(g,MultiPolygon) else [g]):
  if not part.is_empty:ax.add_patch(Patch(list(part.exterior.coords),facecolor=plt.cm.tab20(i%20),edgecolor='#354052',linewidth=.45,alpha=.65))
 cen=g.representative_point();ax.text(cen.x,cen.y,str(a['counts'][i]),ha='center',va='center',fontsize=5,color='#111')
for ring in [D.exterior,*D.interiors]:
 x,y=zip(*ring.coords);ax.plot(x,y,color='black',lw=.7)
ax.set_aspect('equal');ax.set_xlim(D.bounds[0]-.25,D.bounds[2]+.25);ax.set_ylim(D.bounds[1]-.25,D.bounds[3]+.25)
status=sys.argv[4] if len(sys.argv)>4 else 'intermediate, unfinished'
ax.set_title(f'100 cells, {status}, completed round {a["round"]}\nM={a["M"]:.3f}%; empty={a["counts"].count(0)}; {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}',fontsize=9)
ax.set_xlabel('x (km)');ax.set_ylabel('y (km)');fig.tight_layout();fig.savefig(out);plt.close(fig)
