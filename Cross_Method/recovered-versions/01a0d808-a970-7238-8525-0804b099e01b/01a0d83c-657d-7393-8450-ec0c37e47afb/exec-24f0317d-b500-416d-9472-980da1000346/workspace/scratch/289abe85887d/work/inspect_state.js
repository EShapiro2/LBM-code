const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('work/Manhattan_Taxi_Regions/Manhattan_Taxi_Regions.html','utf8');
const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
const first=scripts.find(x=>x.includes('const MAN = ')),hex=scripts.find(x=>x.includes('Hexagon: the corner rule'));
const ctx=vm.createContext({atob,Uint8Array,Uint16Array,Float64Array,Int32Array,Map,Set,Math});
vm.runInContext(first.slice(0,first.indexOf('document.querySelectorAll')),ctx);
vm.runInContext(hex.slice(hex.indexOf('const W = '),hex.indexOf('function makeWorld(){'))+'\nglobalThis.H={buildNet,refresh,locate,inIsle,area,perim,convex};globalThis.D={MAN,MAN_PTS}',ctx);
const {H,D}=ctx,N=H.buildNet(38),snap=JSON.parse(fs.readFileSync(process.argv[2]||'work/last_movable_rim.json'));
N.VX.set(snap.verticesX);N.VY.set(snap.verticesY);
N.world={alive:new Uint8Array(D.MAN_PTS.n),owner:new Int32Array(D.MAN_PTS.n).fill(-1)};
for(let i=0;i<D.MAN_PTS.n;i++)if(D.MAN_PTS.t[i]<900)N.world.alive[i]=1;
H.refresh(N);
const gaps=[];let inland=0;
for(let y=0;y<D.MAN.H;y+=.1)for(let x=0;x<D.MAN.W;x+=.1){if(!H.inIsle(x,y))continue;inland++;if(H.locate(N,x,y,-1)<0)gaps.push([x,y])}
const cells=N.cells.map((ring,c)=>({c,n:N.count[c],poly:ring.map(v=>[N.VX[v],N.VY[v]]),iso:4*Math.PI*H.area(N,c)/H.perim(N,c)**2,centroidY:ring.reduce((a,v)=>a+N.VY[v],0)/6}));
const out={round:snap.round,cells,outline:D.MAN.outline,gaps,inland,pickups:[...N.world.alive].reduce((a,b)=>a+b,0),unowned:[...N.world.owner].filter((v,i)=>N.world.alive[i]&&v<0).length};
fs.writeFileSync('work/inspected_state.json',JSON.stringify(out));
console.log({round:snap.round,inland,gaps:gaps.length,unowned:out.unowned,north:cells.sort((a,b)=>b.centroidY-a.centroidY).slice(0,12).map(({c,n,iso})=>({c,n,iso:iso.toFixed(3)}))});
