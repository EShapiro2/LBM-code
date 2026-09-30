import json,math,hashlib,datetime,re,base64,struct,zipfile
from pathlib import Path
import numpy as np
from shapely.geometry import shape,Point,Polygon,mapping
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch,PathPatch
from matplotlib.path import Path as MPath
p=Path('work/verified38');a=json.load(open(p/'assessment.json'));m=shape(json.load(open(p/'main_island_km.geojson')));cells=a['reclippedHistorical']['cells'];P=np.array(json.load(open('Manhattan_Pickups_2015-01-15_0800-0815.json'))['points']);norm=matplotlib.colors.Normalize(0,200);cmap=plt.get_cmap('viridis')
# Reverify all hour matches against original quantized records and seconds.
z=zipfile.ZipFile('downloads/Manhattan_Taxi_Regions.zip');html=z.read(next(n for n in z.namelist() if n.endswith('.html'))).decode();embedded=json.loads(re.search(r'const MAN = (\{.*?\});',html).group(1));q=np.array(list(struct.iter_unpack('<HHH',base64.b64decode(embedded['b64']))));rides=json.load(open(p/'Full_Rides/matched_manhattan_hour.json'));ll=np.array([[float(r['pickup_longitude']),float(r['pickup_latitude'])] for r in rides]);A=np.array(json.load(open(p/'Full_Rides/matching_report.json'))['affine_lonlat_to_quantized_xy']);res=ll*A[:,0]+A[:,1]-q[:,:2];assert len(rides)==24101 and max(abs(res).ravel())<.51;assert [r['original_pickup_index'] for r in rides]==list(range(24101));assert [r['pickup_seconds_after_0800'] for r in rides]==q[:,2].tolist();assert len(set(r['source_row_index'] for r in rides))==24101
meta=json.load(open(p/'boundary_metadata.json'));a['provenance']={'boundaryVersion':'26b','boundaryUpdatedUTC':datetime.datetime.fromtimestamp(meta['rowsUpdatedAt'],datetime.timezone.utc).isoformat(),'retrievedDate':'2026-09-27','provider':'NYC Department of City Planning','scope':'water-excluded borough boundary; main island selected as largest polygon, other 35 components excluded; one hole retained','historicalCaveat':'2026 boundary applied to 2015 pickups, not a reconstructed 2015 shoreline','fullHourMatchingVerified':24101,'maxQuantizationUnitResidualByAxis':abs(res).max(axis=0).tolist(),'maxMatchingErrorKmByAxis':(abs(res).max(axis=0)*[8.8103/65535,18.8542/65535]).tolist(),'matchedRowsUnique':True,'inputSha256':hashlib.sha256(Path('Manhattan_Pickups_2015-01-15_0800-0815.json').read_bytes()).hexdigest(),'sourceTripURL':(p/'Full_Rides/source_url.txt').read_text().strip(),'noRecordsRemoved':True}
# The north tip is a vertex of the full-resolution official polygon; identify exact lonlat.
klon=(a['certificate']['p'][0]-a['affineLonlatToKm'][0][1])/a['affineLonlatToKm'][0][0];klat=(a['certificate']['p'][1]-a['affineLonlatToKm'][1][1])/a['affineLonlatToKm'][1][0];a['certificate']['pLonlat']=[klon,klat]
simple=m.simplify(.005,preserve_topology=True);a['displaySimplification']={'toleranceKm':.005,'hausdorffKm':m.hausdorff_distance(simple),'preserveTopology':True,'holesRetained':len(simple.interiors),'usedForAnalysis':False};json.dump(a,open(p/'assessment.json','w'),indent=2)
# Full-resolution PNG/PDF, retaining holes through explicit polygon paths.
def pp(poly):
 rings=[poly.exterior,*poly.interiors];vs=[];cs=[]
 from shapely.geometry.polygon import orient
 poly=orient(poly,sign=1);rings=[poly.exterior,*poly.interiors]
 for r in rings:
  vs.extend(r.coords);cs.extend([MPath.MOVETO]+[MPath.LINETO]*(len(r.coords)-2)+[MPath.CLOSEPOLY])
 return MPath(vs,cs)
fig,ax=plt.subplots(figsize=(8,11),layout='constrained');ax.add_patch(PathPatch(pp(m),facecolor='#fafafa',edgecolor='#111',lw=.9))
for c in cells:
 g=shape(c['clipped']);parts=[g] if g.geom_type=='Polygon' else list(g.geoms)
 for poly in parts:ax.add_patch(PathPatch(pp(poly),facecolor=cmap(norm(c['count'])),edgecolor='#424242',lw=.5))
 r=g.representative_point();ax.text(r.x,r.y,str(c['id']),fontsize=7,ha='center',va='center',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none','pad':.2})
out=np.array([o['xy'] for o in a['outliers']]);ax.scatter(out[:,0],out[:,1],marker='x',s=42,c='#e31a1c',lw=1.6,zorder=8)
for o in a['outliers']:ax.annotate(str(o['index']),(o['xy'][0],o['xy'][1]),xytext=(7,-4),textcoords='offset points',fontsize=7,color='#c40000')
missing=m.difference(unary_union([shape(c['clipped']) for c in cells]));parts=list(missing.geoms) if missing.geom_type=='MultiPolygon' else [missing]
for poly in parts:
 if poly.geom_type=='Polygon':ax.add_patch(PathPatch(pp(poly),facecolor='red',edgecolor='red',lw=.4))
ax.plot([.3,2.3],[-.7,-.7],color='black',lw=3);ax.text(1.3,-1,'2 km',ha='center',fontsize=9);ax.annotate('N',xy=(8.8,18),xytext=(8.8,16.5),arrowprops={'arrowstyle':'->'},ha='center');ax.set_xlim(-.4,10);ax.set_ylim(-1.3,20.2);ax.set_aspect('equal');ax.set_xlabel('km east in recovered simulator frame');ax.set_ylabel('km north');ax.set_title('Verified NYC main-island boundary (DCP 26b)\nHistorical hexagons re-clipped: diagnostic, NOT a feasible solution',fontsize=12);fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,shrink=.6,label='Pickup count per clipped region');fig.text(.55,.12,'Cell ID : pickup count\n'+'\n'.join('   '.join(f'{j:02}: {cells[j]["count"]:3}' for j in range(i,min(i+3,38))) for i in range(0,38,3)),fontsize=8,family='monospace',bbox={'facecolor':'white','edgecolor':'#aaa'});fig.savefig(p/'verified_map.png',dpi=180);fig.savefig(p/'verified_map.pdf')
# Compact transferable SVG; projection is north-up and uniformly scaled.
scale=30;xy=lambda v:(35+v[0]*scale,660-v[1]*scale)
f=lambda x:('%0.1f'%x).rstrip('0').rstrip('.')
def path(coords):return 'M'+' '.join(','.join(map(f,xy(v))) for v in coords)+'Z'
land=''.join(path(r.coords) for r in [simple.exterior,*simple.interiors]);s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 770 755"><style>text{font:12px sans-serif;fill:#17212b}.t{font-size:17px;font-weight:bold}.c{font-size:9px;paint-order:stroke;stroke:white;stroke-width:2px;stroke-linejoin:round}</style><defs><path id="land" fill-rule="evenodd" clip-rule="evenodd" d="'+land+'"/><clipPath id="island"><use href="#land"/></clipPath></defs><path fill="white" d="M0 0H770V755H0Z"/><text x="20" y="25" class="t">Verified Manhattan main island · NYC DCP 26b</text><text x="20" y="45">Historical hexagons re-clipped; NOT a newly optimized or feasible solution</text><use href="#land" fill="#eee" stroke="#111" stroke-width=".8"/><g clip-path="url(#island)" stroke="#444" stroke-width=".55">']
for c in cells:s.append('<path fill="'+matplotlib.colors.to_hex(cmap(norm(c['count'])))+'" d="'+path(c['underlying'])+'"/>')
s.append('</g>')
for c in cells:
 r=shape(c['clipped']).representative_point();xx,yy=xy([r.x,r.y]);s.append(f'<text x="{f(xx)}" y="{f(yy)}" text-anchor="middle" class="c">{c["id"]}</text>')
for o in a['outliers']:
 xx,yy=xy(o['xy']);s.append(f'<path d="M{f(xx-3)},{f(yy-3)}l6 6m-6 0l6-6" stroke="#e31a1c" stroke-width="2"/><text x="{f(xx+6)}" y="{f(yy)}" fill="red">{o["index"]}</text>')
s.extend(['<path d="M44 699h60m-60-3v6m60-6v6" stroke="black" stroke-width="2"/><text x="74" y="719" text-anchor="middle">2 km</text><path d="M310 135v-35l-4 8m4-8 4 8" stroke="black" fill="none"/><text x="306" y="92">N</text>'])
textlines=['Source: NYC DCP water-excluded boroughs','Version 26b; updated 26 May 2026','Retrieved 27 September 2026','Largest Manhattan polygon; one hole retained','35 other borough components excluded','','5,986 original pickups; none deleted','5,983 inside; 3 outside (red crosses)','Labels on map: zero-based cell IDs','Uncovered island area: 0.017135 km²','Worst re-clipped width ratio: 2.233110','','Color: pickup count']
for k,line in enumerate(textlines):s.append(f'<text x="385" y="{85+k*18}">{line}</text>')
for k,nc in enumerate([0,50,100,150,200]):s.append(f'<path fill="{matplotlib.colors.to_hex(cmap(norm(nc)))}" d="M{385+65*k}310h20v14h-20Z"/><text x="{385+65*k}" y="340">{nc}</text>')
s.append('<text x="385" y="375">Cell ID : pickup count</text>')
for k,c in enumerate(cells):s.append(f'<text x="{385+110*(k//13)}" y="{397+18*(k%13)}">{c["id"]}: {c["count"]}</text>')
s.extend(['<text x="385" y="659">Red crosses: records 309, 4705, 5212</text><text x="385" y="681">Boundary display simplified ≤5 m;</text><text x="385" y="699">all checks use full-resolution geometry.</text><text x="20" y="743">2026 shoreline applied to 2015 pickups. Counts exclude the three marked outside records from cell ownership.</text></svg>']);svg=''.join(s);(p/'verified_map.svg').write_text(svg);print('SVG chars',len(svg))
