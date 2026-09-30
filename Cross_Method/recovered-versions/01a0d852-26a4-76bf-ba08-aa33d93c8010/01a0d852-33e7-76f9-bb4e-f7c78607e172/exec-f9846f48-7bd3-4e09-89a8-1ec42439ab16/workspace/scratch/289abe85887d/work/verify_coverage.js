const fs = require('fs'), vm = require('vm');
const html = fs.readFileSync('work/Manhattan_Taxi_Regions/Manhattan_Taxi_Regions.html','utf8');
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
const data=scripts.find(x=>x.includes('const MAN = '));
const geometry=scripts.find(x=>x.includes('Hexagon: the corner rule'));
const ctx=vm.createContext({atob,console,Uint8Array,Uint16Array,Float64Array,Int32Array,Math,Map,Set});
vm.runInContext(data.slice(0,data.indexOf('document.querySelectorAll')),ctx);
vm.runInContext(geometry.slice(geometry.indexOf('const W = '),geometry.indexOf('function makeWorld(){'))+'\nglobalThis.API={buildNet,locate,convex,inCell,area,perim};',ctx);
const N=ctx.API.buildNet(38),snap=JSON.parse(fs.readFileSync(process.argv[2]||'work/best_movable_rim.json','utf8'));
N.VX.set(snap.verticesX);N.VY.set(snap.verticesY);
const outline=vm.runInContext('MAN.outline',ctx), edges=[];
const tally=new Map();
for(const ring of N.cells)for(let i=0;i<6;i++){
  const a=ring[i],b=ring[(i+1)%6],key=a<b?`${a},${b}`:`${b},${a}`;
  const record=tally.get(key)||{a,b,n:0};record.n++;tally.set(key,record);
}
for(const e of tally.values())if(e.n===1)edges.push([[N.VX[e.a],N.VY[e.a]],[N.VX[e.b],N.VY[e.b]]]);
const cross=(a,b)=>a[0]*b[1]-a[1]*b[0],sub=(a,b)=>[a[0]-b[0],a[1]-b[1]];
let outsideLength=0,intersections=0,uncoveredSegments=0;
for(let i=0;i<outline.length;i++){
  const p=outline[i],q=outline[(i+1)%outline.length],r=sub(q,p),ts=[0,1];
  for(const [a,b] of edges){const s=sub(b,a),den=cross(r,s);
    if(Math.abs(den)<1e-12)continue;
    const u=sub(a,p),t=cross(u,s)/den,v=cross(u,r)/den;
    if(t>1e-10&&t<1-1e-10&&v>=-1e-10&&v<=1+1e-10){ts.push(t);intersections++}
  }
  ts.sort((a,b)=>a-b);
  for(let j=0;j<ts.length-1;j++){
    const mid=(ts[j]+ts[j+1])/2;
    if(ctx.API.locate(N,p[0]+mid*r[0],p[1]+mid*r[1],-1)<0){
      outsideLength+=Math.hypot(...r)*(ts[j+1]-ts[j]);uncoveredSegments++;
    }
  }
}
const nonconvex=N.cells.filter((_,c)=>!ctx.API.convex(N,c)).length;
const minshape=Math.min(...N.cells.map((_,c)=>4*Math.PI*ctx.API.area(N,c)/ctx.API.perim(N,c)**2));
const total=(snap.counts||[]).reduce((a,b)=>a+b,0);
console.log(JSON.stringify({snapshot:process.argv[2],round:snap.round,shorelineLengthOutside:outsideLength,uncoveredSegments,shorelineMeshIntersections:intersections,meshBoundaryEdges:edges.length,nonconvex,minshape,total,countRange:[Math.min(...snap.counts),Math.max(...snap.counts)]},null,2));
