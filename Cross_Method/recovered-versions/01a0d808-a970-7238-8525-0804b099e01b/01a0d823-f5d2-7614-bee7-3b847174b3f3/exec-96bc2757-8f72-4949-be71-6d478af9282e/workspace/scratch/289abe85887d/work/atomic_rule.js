const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('work/Manhattan_Taxi_Regions/Manhattan_Taxi_Regions.html','utf8');
const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
const first=scripts.find(x=>x.includes('const MAN = '));
const hex=scripts.find(x=>x.includes('Hexagon: the corner rule'));
const context=vm.createContext({atob,console,Uint8Array,Uint16Array,Float64Array,Int32Array,Math,Map,Set});
vm.runInContext(first.slice(0,first.indexOf('document.querySelectorAll')),context);
let hb=hex.slice(hex.indexOf('const W = '),hex.indexOf('function makeWorld(){'));
const atom=`function activateVertex(N, v, eta){
  // The agent proposes a joint move of the central vertex and its interior edge-neighbours.
  // Every touched cell participates in the acceptance test, so the variance proof survives.
  const adjacent = new Set();
  for(const c of N.vcells[v]){
    const r=N.cells[c],k=r.indexOf(v);
    adjacent.add(r[(k+5)%6]);adjacent.add(r[(k+1)%6]);
  }
  const near=[...adjacent].filter(u=>N.interior[u]);
  const verts=[v,...near], weights=[1,...near.map(()=>0.55)];
  const touched=[...new Set(verts.flatMap(u=>N.vcells[u]))];
  const pts=[];for(const c of touched)for(const i of N.members[c])pts.push(i);
  const old=touched.map(c=>N.count[c]);
  const base=old.reduce((sum,n)=>sum+n*n,0);
  const xx=verts.map(u=>N.VX[u]),yy=verts.map(u=>N.VY[u]);
  const counts=new Int32Array(touched.length);
  let best=base,bx=xx.slice(),by=yy.slice();
  for(const scale of [1,2,4,8,16]){
    const d=eta*scale;
    if(d>0.45*N.s)break;
    for(let a=0;a<12;a++){
      const angle=a*Math.PI/6,dx=d*Math.cos(angle),dy=d*Math.sin(angle);
      for(let j=0;j<verts.length;j++){N.VX[verts[j]]=xx[j]+weights[j]*dx;N.VY[verts[j]]=yy[j]+weights[j]*dy}
      N.attempts++;
      if(!valid(N,touched)){N.rejected++;continue}
      counts.fill(0);let covered=true;
      for(const i of pts){let j=0;for(;j<touched.length;j++)if(inCell(N,touched[j],MAN_PTS.x[i],MAN_PTS.y[i]))break;
        if(j===touched.length){covered=false;break}counts[j]++}
      if(!covered)continue;
      const score=counts.reduce((sum,n)=>sum+n*n,0);
      if(score<best){best=score;bx=verts.map(u=>N.VX[u]);by=verts.map(u=>N.VY[u])}
    }
  }
  for(let j=0;j<verts.length;j++){N.VX[verts[j]]=bx[j];N.VY[verts[j]]=by[j]}
  if(best<base){N.moves++;N.travel+=Math.hypot(bx[0]-xx[0],by[0]-yy[0]);
    // Rebuild ownership after a joint move, including cells in the extended neighbourhood.
    relocateLocal(N,touched)}
}`;
hb=hb.slice(0,hb.indexOf('function activateVertex('))+atom+'\n';
hb+='\n'+hex.slice(hex.indexOf('function sweepNet('),hex.indexOf('function doSweep(){'));
vm.runInContext(hb+'\nglobalThis.H={buildNet,refresh,sweepNet,area,perim,convex};globalThis.D={MAN_PTS};',context);
const {H,D}=context,N=H.buildNet(38),ids=[];
N.floor=.02;N.world={alive:new Uint8Array(D.MAN_PTS.n),owner:new Int32Array(D.MAN_PTS.n).fill(-1)};
for(let i=0;i<D.MAN_PTS.n;i++)if(D.MAN_PTS.t[i]<900){N.world.alive[i]=1;ids.push(i)}
H.refresh(N);
let rounds=0,last=0;
for(;rounds<100;rounds++){
  const before=[...N.count].reduce((a,b)=>a+b*b,0);
  H.sweepNet(N,.02);
  const after=[...N.count].reduce((a,b)=>a+b*b,0);
  if(after>before)throw Error('imbalance increased');
  if((rounds+1)%10===0)console.log('round',rounds+1,'variance',after/N.m-(ids.length/N.m)**2,'moves',N.moves);
  if(before===after){last++;if(last>=2){rounds++;break}}
  else last=0;
}
const avg=ids.length/N.m,counts=[...N.count];
console.log('FINAL',JSON.stringify({rounds,moves:N.moves,variance:counts.reduce((a,x)=>a+(x-avg)**2,0)/N.m,min:Math.min(...counts),max:Math.max(...counts),shape:Math.min(...N.cells.map((_,c)=>4*Math.PI*H.area(N,c)/H.perim(N,c)**2)),nonconvex:N.cells.filter((_,c)=>!H.convex(N,c)).length}));
