from pathlib import Path
p=Path('outputs/voronoi_migrate600/single_step_from_258.html');s=p.read_text()
s=s.replace('let n=0;','let n=1;')
s=s.replace('Back to 258','Back to 258 → 259').replace('Selection <input','After selection <input')
s=s.replace('min="258" max="500" value="258"','min="259" max="500" value="259"')
s=s.replace('<option value="1">100%</option>','<option value="0.5">50%</option><option value="0.75">75%</option><option value="1" selected>Fit screen</option>')
s=s.replace('Starts paused; no autoplay.','Opens at 258 → 259, paused; no autoplay.')
s=s.replace("n=Math.max(0,Math.min(frames.length-1", "n=Math.max(1,Math.min(frames.length-1")
s=s.replace('if(!Number.isFinite(n))n=0','if(!Number.isFinite(n))n=1')
s=s.replace("$('reset').onclick=()=>go(258)","$('reset').onclick=()=>go(259)")
s=s.replace("$('prev').disabled=n===0","$('prev').disabled=n===1")
s=s.replace("$(id).style.width=(Number(e.target.value)*100)+'%'","$(id).style.width=(Number(e.target.value)*100)+'%';$(id).style.height=(Number(e.target.value)*100)+'%'")
s=s.replace('<svg id="left" viewBox="0 0 510 1040"></svg>','<div class="map"><svg id="left" viewBox="0 0 510 1040"></svg></div>')
s=s.replace('<svg id="right" viewBox="0 0 510 1040"></svg>','<div class="map"><svg id="right" viewBox="0 0 510 1040"></svg></div>')
s=s.replace('</style>','''
html,body{height:100%;height:100dvh;overflow:hidden}body{display:flex;flex-direction:column}header{position:static;flex-shrink:0;padding:8px 14px}header h1{font-size:18px;margin:0 0 6px}header p{margin:5px 0;font-size:13px}header small{font-size:11px}button{padding:5px 9px}#detail{padding:5px 14px;font-size:13px;min-height:18px;flex-shrink:0}main{flex:1;min-height:0;padding:6px;gap:6px;overflow:hidden}.panel{display:flex;flex-direction:column;min-height:0;min-width:0;width:50%;overflow:hidden}.panel h2{font-size:14px;margin:6px;flex-shrink:0}.map{flex:1;min-height:0;overflow:auto;text-align:center}svg{display:block;width:100%;height:100%;min-width:0;min-height:0;margin:auto}#slider{width:min(25vw,320px)}
</style>''')
s=s.replace("`Before · selection ${p.step}`","`BEFORE · selection ${p.step}`").replace("`Current · selection ${f.step} (total ${f.total})`","`AFTER · selection ${f.step} (total ${f.total})`")
s=s.replace("`${f.step} / 500`","`${p.step} → ${f.step}`")
s=s.replace("${f.status}.`","${f.status}.${f.status==='skipped'?' No geometry changed in this turn.':''}`")
p.write_text(s)
# Persist reproducible changes in the existing builder instead of keeping only edited HTML.
b=Path('work/voronoi_migrate600/step_viewer.py');src=b.read_text();start=src.index("html=r'''");end=src.index("'''\npath=",start)
template=s[:s.index('const frames=')+len('const frames=')]+'__DATA__'+s[s.index(';let n=1;'):]
src=src[:start]+"html=r'''"+template+src[end:]
src=src.replace('for(let k=258;k<=500;k++)go(k);go(258);','for(let k=259;k<=500;k++)go(k);go(259);').replace("if(n!==1)throw Error('Next')","if(n!==2)throw Error('Next')").replace("if(n!==0)throw Error('Previous')","if(n!==1)throw Error('Previous')")
b.write_text(src)
