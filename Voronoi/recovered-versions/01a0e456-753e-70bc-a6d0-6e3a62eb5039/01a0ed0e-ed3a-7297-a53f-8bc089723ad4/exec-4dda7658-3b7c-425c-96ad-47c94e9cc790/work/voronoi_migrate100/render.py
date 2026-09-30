import json,sys,hashlib,zipfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.animation import FFMpegWriter
from shapely.geometry import Polygon
import run as R
O=R.O
rows=[json.load(open(p)) for p in sorted((O/'turns').glob('*.json'))];start=json.load(open(O/'initial.json'));end=json.load(open(O/'final.json'));assert len(rows)==100 and end['completed']==100
assert rows[0]['before_centers']==start['centers'] and rows[-1]['after_centers']==end['centers']
for a,b in zip(rows,rows[1:]):assert a['after_centers']==b['before_centers']
rel=[r for r in rows if r['kind']=='depart-insert'];moved=[r for r in rows if r['status']=='moved'];skipped=[r for r in rows if r['status']=='skipped']
summary=dict(status='completed_100_selections_not_convergence',timestamp=end['timestamp'],start_checkpoint='end of round 59, before weighted selection',turns=100,distinct_selected=len(set(r['site'] for r in rows)),depart_insert=len(rel),ordinary_moved=len(moved),ordinary_skipped=len(skipped),initial=start['summary'],final=end['summary'],final_audit=end['audit'],max_equal_area_relative_error=max(r['departure']['split']['relative_area_error'] for r in rel),max_relocation_weight_conservation_error=max(abs(r['departure']['weight_sum_before']-r['departure']['weight_sum_after']) for r in rel),route_hops=sum(len(r['departure']['route'])-1 for r in rel),max_route_hops=max(len(r['departure']['route'])-1 for r in rel))
R.base.save(O/'summary.json',summary)
R.draw(start,O/'initial_map.png','Before: saved round 59 · 100 centers')
R.draw(end,O/'final_map.png','After 100 selections · departure + geometric insertion')
# Full precision logs retained separately. Browser frames round geometry only for display.
frames=[]
for r in rows:
 f={k:r[k] for k in ['turn','site','kind','status','departure','weights_before','weights_after_modeled','badness_before','badness_after_modeled']}
 for k in ['before_centers','after_centers','before_cells','after_cells']:f[k]=r[k]
 f['reason']=r.get('reason','');frames.append(f)
data=json.dumps(dict(frames=frames,summary=summary),separators=(',',':'))
html=r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>100 turns — departure, migration, insertion</title><style>
body{font:15px system-ui;margin:0;color:#182334;background:#f3f5f7}header{padding:14px 22px;background:white;border-bottom:1px solid #ddd}h1{font-size:21px;margin:0 0 8px}button,select{font:inherit;padding:6px 12px}nav{display:flex;align-items:center;gap:12px;flex-wrap:wrap}main{display:flex;gap:12px;padding:12px;justify-content:center}.panel{background:white;border-radius:10px;padding:8px;width:46%;max-width:550px}.panel h2{text-align:center;font-size:16px;margin:0}svg{width:100%;height:min(76vh,850px)}#detail{padding:8px 22px;min-height:44px}small{color:#475569}.legend{display:inline-block;width:95px;height:10px;background:linear-gradient(90deg,#ffffcc,#fd8d3c,#800026)}input[type=range]{width:170px}#seek{width:min(450px,45vw)}
</style></head><body><header><h1>100 selections · departure, migration, geometric insertion</h1><nav><button id="play">▶ Play</button><button id="prev">←</button><button id="next">→</button><input id="seek" type="range" min="1" max="100" value="1"><b id="turn"></b><label>Pause <input id="speed" type="range" min="0.1" max="1" step="0.1" value="0.5"><span id="delay">0.5 s</span></label><label>Labels <select id="labels"><option value="weight">Modeled weight</option><option value="id">Center ID</option><option value="grade">Badness</option></select></label></nav><p><span class="legend"></span> Badness: 0 → 3+ (lower is better). Blue dots: centers. Cyan outlines: selected cell and insertion host.</p><small>One depart–migrate–insert transaction is one turn. Selection is with replacement. Before weights are refreshed counts; after weights use frozen-density geometry. The next turn refreshes counts. No numerical optimization is used for insertion.</small></header><div id="detail"></div><main><section class="panel"><h2>Before this turn</h2><svg id="before" viewBox="0 0 430 870"></svg></section><section class="panel"><h2>After this turn</h2><svg id="after" viewBox="0 0 430 870"></svg></section></main><script>
const DATA=__DATA__;let n=0,timer=null;const $=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){const x=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))x.setAttribute(k,v);parent.appendChild(x);return x}
function xy(p){return [16+(p[0]+.2)*40,850-(p[1]+.3)*40]}
function color(v){const stops=[[255,255,204],[254,217,118],[253,141,60],[227,26,28],[128,0,38]],z=Math.min(3,Math.max(0,v))/3*4,i=Math.min(3,Math.floor(z)),f=z-i;return `rgb(${stops[i].map((x,j)=>Math.round(x+(stops[i+1][j]-x)*f)).join(',')})`}
function center(v){let A=0,x=0,y=0;for(let i=0;i<v.length-1;i++){const a=v[i],b=v[i+1],s=a[0]*b[1]-b[0]*a[1];A+=s;x+=(a[0]+b[0])*s;y+=(a[1]+b[1])*s}return [x/(3*A),y/(3*A)]}
function panel(id,f,after){const svg=$(id);svg.innerHTML='';const polys=f[after?'after_cells':'before_cells'],cs=f[after?'after_centers':'before_centers'],w=f[after?'weights_after_modeled':'weights_before'],bad=f[after?'badness_after_modeled':'badness_before'];for(let i=0;i<100;i++){const selected=i===f.site||i===f.departure.host;const p=el('polygon',{points:polys[i].map(v=>xy(v).join(',')).join(' '),fill:color(bad[i]),stroke:selected?'#06b6d4':'#64748b','stroke-width':selected?2.4:.6},svg);el('title',{},p).textContent=`Center ${i+1}; weight ${w[i].toFixed(3)}; badness ${bad[i].toFixed(3)}`}
if(!after&&f.kind==='depart-insert'){const ids=[f.site,...f.departure.route];el('polyline',{points:ids.map(i=>xy(cs[i]).join(',')).join(' '),fill:'none',stroke:'#0284c7','stroke-width':2,'stroke-dasharray':'4 3'},svg)}
for(let i=0;i<100;i++){const [x,y]=xy(cs[i]);el('circle',{cx:x,cy:y,r:i===f.site?3.5:2.1,fill:i===f.site?'#7c3aed':'#0369a1'},svg);const [tx,ty]=xy(center(polys[i]));let label=$('labels').value==='id'?String(i+1):$('labels').value==='grade'?bad[i].toFixed(2):w[i].toFixed(after?1:0);const text=el('text',{x:tx,y:ty,'font-size':8,'text-anchor':'middle','dominant-baseline':'middle',fill:'#111827','paint-order':'stroke',stroke:'#fff','stroke-width':1.5,'stroke-opacity':.65},svg);text.textContent=label}}
function show(){const f=DATA.frames[n];$('turn').textContent=`${n+1} / 100`;$('seek').value=n+1;panel('before',f,false);panel('after',f,true);const d=f.departure;$('detail').textContent=f.kind==='depart-insert'?`Turn ${n+1}: center ${f.site+1} departs (weight ${d.weight}, threshold ${d.threshold.toFixed(2)}). Hosts: ${d.route.map(i=>i+1).join(' → ')}. Geometric insertion at host ${d.host+1}; one complete turn.`:`Turn ${n+1}: center ${f.site+1}, ${f.kind} move — ${f.status}${f.reason?' ('+f.reason.replaceAll('_',' ')+')':''}. Departure condition was not met.`}
function pause(){clearTimeout(timer);timer=null;$('play').textContent='▶ Play'}function tick(){if(n>=99){pause();return}n++;show();timer=setTimeout(tick,1000*Number($('speed').value))}
$('play').onclick=()=>{if(timer)pause();else{if(n===99)n=0;show();$('play').textContent='⏸ Pause';timer=setTimeout(tick,1000*Number($('speed').value))}};$('prev').onclick=()=>{pause();n=Math.max(0,n-1);show()};$('next').onclick=()=>{pause();n=Math.min(99,n+1);show()};$('seek').oninput=()=>{pause();n=Number($('seek').value)-1;show()};$('speed').oninput=()=>{$('delay').textContent=Number($('speed').value).toFixed(1)+' s'};$('labels').onchange=show;show();
</script></body></html>'''
(O/'animation.html').write_text(html.replace('__DATA__',data))
# Shareable native video, each frame shows a complete before/after turn.
fig,axes=plt.subplots(1,2,figsize=(9,9),sharex=True,sharey=True);fig.subplots_adjust(top=.91,bottom=.07,wspace=.03)
pcs=[];dots=[];texts=[]
for ax in axes:
 pc=PolyCollection([],cmap='YlOrRd',clim=(0,3),edgecolors='#64748b',linewidths=.4);ax.add_collection(pc);pcs.append(pc);dots.append(ax.scatter([],[],s=7,c='#0369a1'));texts.append([ax.text(0,0,'',fontsize=5.5,ha='center',va='center') for _ in range(100)]);ax.set(xlim=(-.2,9.5),ylim=(-.3,19.95),aspect='equal');ax.set_xticks([]);ax.set_yticks([])
caption=fig.suptitle('',fontsize=11);axes[0].set_title('Before',fontsize=10);axes[1].set_title('After · frozen-density modeled weights',fontsize=10)
fig.text(.5,.015,'Color = balance + circularity badness (lower is better) · Labels = weight · 1 selection per frame',ha='center',fontsize=8)
writer=FFMpegWriter(fps=2,bitrate=1800)
with writer.saving(fig,str(O/'animation.mp4'),dpi=105):
 for r in rows:
  host=r['departure'].get('host');caption.set_text(f'Turn {r["turn"]}/100 · center {r["site"]+1} · '+(f'depart → insert at host {host+1}' if host is not None else r['kind']+' · '+r['status']))
  for j,after in enumerate([False,True]):
   polys=r['after_cells' if after else 'before_cells'];cs=np.array(r['after_centers' if after else 'before_centers']);w=r['weights_after_modeled' if after else 'weights_before'];B=r['badness_after_modeled' if after else 'badness_before'];pcs[j].set_verts(polys);pcs[j].set_array(np.array(B));pcs[j].set_edgecolors(['#06b6d4' if i in [r['site'],host] else '#64748b' for i in range(100)]);pcs[j].set_linewidths([1.7 if i in [r['site'],host] else .4 for i in range(100)]);dots[j].set_offsets(cs)
   for text,p,v in zip(texts[j],polys,w):text.set_position(Polygon(p).centroid.coords[0]);text.set_text(f'{v:.0f}')
  writer.grab_frame()
plt.close(fig)
print(json.dumps(summary,indent=2),flush=True)
