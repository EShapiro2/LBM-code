const fs = require('fs'), vm = require('vm');
const html = fs.readFileSync('work/Manhattan_Taxi_Regions/Manhattan_Taxi_Regions.html', 'utf8');
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x => x[1]);
const first = scripts.find(x => x.includes('const MAN = '));
const hex = scripts.find(x => x.includes('Hexagon: the corner rule'));
const merge = scripts.find(x => x.includes('K-means with merging (main.tex'));
const context = vm.createContext({atob, console, Uint8Array, Uint16Array, Float64Array, Int32Array, Math, Map, Set});
vm.runInContext(first.slice(0, first.indexOf('document.querySelectorAll')), context);
const hb = hex.slice(hex.indexOf('const W = '), hex.indexOf('function makeWorld(){')) + '\n' + hex.slice(hex.indexOf('function sweepNet('), hex.indexOf('function doSweep(){'));
vm.runInContext(hb+'\nglobalThis.H = {buildNet,refresh,sweepNet,area,perim,valid}; globalThis.D={MAN,MAN_PTS};',context);
const mb = merge.slice(merge.indexOf('function rng('),merge.indexOf('window.KM ='));
vm.runInContext(mb+'\nglobalThis.M={Run};',context);
const {H,D,M}=context;
const ids=[];
for(let i=0;i<D.MAN_PTS.n;i++) if(D.MAN_PTS.t[i]<900) ids.push(i);
const pts=ids.map(i=>[D.MAN_PTS.x[i],D.MAN_PTS.y[i]]);
const km=new M.Run({T:50,T2:150,k:2,seed:1},pts);
for(let i=0;!km.done && i<50000;i++) km.step();
if(!km.done) throw Error('merging incomplete');
const N=H.buildNet(km.mc.size);
N.floor=.02;N.world={alive:new Uint8Array(D.MAN_PTS.n),owner:new Int32Array(D.MAN_PTS.n).fill(-1)};
for(const i of ids) N.world.alive[i]=1;
H.refresh(N);
let last=0, rounds=0;
for(;rounds<500;rounds++){
  const before=[...N.count].reduce((a,b)=>a+b*b,0);
  H.sweepNet(N,.02);
  const after=[...N.count].reduce((a,b)=>a+b*b,0);
  if(after>before) throw Error('imbalance increased');
  if((rounds+1)%50===0) console.log('round',rounds+1,'imbalance',after,'moves',N.moves);
  if(before===after) { last++; if(last>=5) { rounds++; break; } }
  else last=0;
}
const merged=[...km.mc.values()].map(g=>({size:g.size,polys:g.leaves.map(l=>km.nodes[l].poly),label:km.com(g)}));
const cells=N.cells.map((r,c)=>({size:N.count[c],poly:r.map(v=>[N.VX[v],N.VY[v]]),label:(()=>{const a=N.members[c];if(!a.length)return null;return [a.reduce((z,i)=>z+D.MAN_PTS.x[i],0)/a.length,a.reduce((z,i)=>z+D.MAN_PTS.y[i],0)/a.length]})()}));
const result={outline:D.MAN.outline,W:D.MAN.W,H:D.MAN.H,pts,merged,cells,rounds,moves:N.moves,variance:{merge:merged.reduce((a,x)=>a+(x.size-pts.length/merged.length)**2,0)/merged.length,hex:cells.reduce((a,x)=>a+(x.size-pts.length/cells.length)**2,0)/cells.length},shape:Math.min(...cells.map((x,c)=>4*Math.PI*H.area(N,c)/H.perim(N,c)**2))};
fs.writeFileSync('work/compare_data.json',JSON.stringify(result));
console.log('FINISHED',JSON.stringify({groups:merged.length,cells:cells.length,rounds,moves:N.moves,variance:result.variance,shape:result.shape}));
