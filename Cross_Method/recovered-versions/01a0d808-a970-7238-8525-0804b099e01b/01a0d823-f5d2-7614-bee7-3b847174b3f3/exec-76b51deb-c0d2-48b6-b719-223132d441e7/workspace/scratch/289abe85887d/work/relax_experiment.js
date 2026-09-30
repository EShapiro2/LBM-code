const fs=require('fs'),vm=require('vm');
let html=fs.readFileSync('work/Manhattan_Taxi_Regions/Manhattan_Taxi_Regions.html','utf8');
const threshold=Number(process.argv[2]);
const radius=Number(process.argv[3]||.45);
const convexity=process.argv[4]!=='simple';
html=html.replace('4 * Math.PI * a / (p * p) < 0.35',`4 * Math.PI * a / (p * p) < ${threshold}`)
         .replaceAll('0.45 * N.s',`${radius} * N.s`);
if(!convexity) html=html.replace('!convex(N, c) ||','!simple(N, c) ||');
const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
const first=scripts.find(x=>x.includes('const MAN = '));
const hex=scripts.find(x=>x.includes('Hexagon: the corner rule'));
const context=vm.createContext({atob,console,Uint8Array,Uint16Array,Float64Array,Int32Array,Math,Map,Set});
vm.runInContext(first.slice(0,first.indexOf('document.querySelectorAll')),context);
const hb=hex.slice(hex.indexOf('const W = '),hex.indexOf('function makeWorld(){'))+'\n'+hex.slice(hex.indexOf('function sweepNet('),hex.indexOf('function doSweep(){'));
vm.runInContext(hb+'\nglobalThis.H={buildNet,refresh,sweepNet,area,perim,convex,simple};globalThis.D={MAN_PTS};',context);
const {H,D}=context,N=H.buildNet(38),ids=[];
N.floor=.02;N.world={alive:new Uint8Array(D.MAN_PTS.n),owner:new Int32Array(D.MAN_PTS.n).fill(-1)};
for(let i=0;i<D.MAN_PTS.n;i++)if(D.MAN_PTS.t[i]<900){N.world.alive[i]=1;ids.push(i)}
H.refresh(N);
const initial=[...N.count].reduce((a,b)=>a+b*b,0);
let rounds=0,last=0;
for(;rounds<500;rounds++){
  const before=[...N.count].reduce((a,b)=>a+b*b,0);
  H.sweepNet(N,.02);
  const after=[...N.count].reduce((a,b)=>a+b*b,0);
  if(after>before)throw Error('imbalance increased');
  if(before===after){last++;if(last>=2){rounds++;break}}
  else last=0;
}
const n=ids.length,avg=n/N.m;
const shapes=N.cells.map((_,c)=>4*Math.PI*H.area(N,c)/H.perim(N,c)**2);
const counts=[...N.count];
console.log(JSON.stringify({threshold,radius,convexity,rounds,moves:N.moves,variance:counts.reduce((a,x)=>a+(x-avg)**2,0)/N.m,min:Math.min(...counts),max:Math.max(...counts),shape:Math.min(...shapes),nonconvex:N.cells.filter((_,c)=>!H.convex(N,c)).length,initial:initial/N.m-avg*avg}));
