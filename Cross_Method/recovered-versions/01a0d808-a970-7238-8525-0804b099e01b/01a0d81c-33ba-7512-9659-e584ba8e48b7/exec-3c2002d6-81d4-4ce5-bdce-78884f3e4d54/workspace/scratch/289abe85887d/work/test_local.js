const fs = require('fs'), vm = require('vm');
const html = fs.readFileSync('work/Manhattan_Taxi_Regions/Manhattan_Taxi_Regions.html', 'utf8');
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x => x[1]);
const first = scripts.find(x => x.includes('const MAN = '));
const second = scripts.find(x => x.includes('Hexagon: the corner rule'));
const context = vm.createContext({atob, console, Uint8Array, Uint16Array, Float64Array, Int32Array, Math, Map, Set});
vm.runInContext(first.slice(0, first.indexOf('document.querySelectorAll')), context);
const body = second.slice(second.indexOf('const W = '), second.indexOf('function makeWorld(){'));
vm.runInContext(body + '\n globalThis.API = {buildNet, refresh, sweepNet, area, perim, convex, valid}; globalThis.DATA = {MAN_PTS};', context);
const {API, DATA} = context;
const N = API.buildNet(38);
const owner = new Int32Array(DATA.MAN_PTS.n).fill(-1);
const alive = new Uint8Array(DATA.MAN_PTS.n);
for (let i=0; i<alive.length; i++) alive[i] = +(DATA.MAN_PTS.t[i] >= 0 && DATA.MAN_PTS.t[i] < 900);
N.world = {owner, alive};
API.refresh(N);
const count = () => [...N.count].reduce((sum,n)=>sum+n*n,0);
let old = count(), initial=old;
for(let t=0;t<20;t++){
  API.sweepNet(N,.02);
  let now=count();
  if(now>old) throw Error(`variance increased on round ${t}: ${old} -> ${now}`);
  if([...N.count].reduce((a,b)=>a+b,0)!==5986) throw Error('pickup count changed');
  for(let c=0;c<N.m;c++) if(!API.valid(N,[c])) throw Error('invalid cell '+c);
  old=now;
}
console.log({cells:N.m,initial,final:old,moves:N.moves,rejectedCandidates:N.rejected});
