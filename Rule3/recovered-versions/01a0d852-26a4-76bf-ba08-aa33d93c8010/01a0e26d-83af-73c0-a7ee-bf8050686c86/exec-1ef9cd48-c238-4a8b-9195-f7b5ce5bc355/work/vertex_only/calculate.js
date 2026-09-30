function calculate(data){
function rng(seed){return ()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296}}
let original=[];
for(let i=0;i<4;i++)for(let j=0;j<12+(i<2?1:0);j++)for(let b=0;b<2;b++)original.push([1.5*i+b,Math.sqrt(3)*(j+.5*(i%2))]);
const n=original.length, adj=original.map((p,i)=>original.flatMap((q,j)=>i!==j&&Math.abs(dist(p,q)-1)<1e-8?[j]:[]));
const movable=adj.flatMap((a,i)=>a.length===3?[i]:[]);
function dist(a,b){return (a[0]-b[0])**2+(a[1]-b[1])**2}
function cross(a,b,c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])}
function project(q,t){let [a,b,c]=t,sg=[cross(a,b,q),cross(b,c,q),cross(c,a,q)];
if(Math.abs(cross(a,b,c))>1e-14&&(sg.every(x=>x>=-1e-12)||sg.every(x=>x<=1e-12)))return q;
let best=null,bd=Infinity;for(let k=0;k<3;k++){let a=t[k],b=t[(k+1)%3],den=dist(a,b),u=den?Math.max(0,Math.min(1,((q[0]-a[0])*(b[0]-a[0])+(q[1]-a[1])*(b[1]-a[1]))/den)):0;
let p=[a[0]+u*(b[0]-a[0]),a[1]+u*(b[1]-a[1])],d=dist(p,q);if(d<bd){bd=d;best=p}}return best}
function nearest(d,ps,ids){let bi=-1,bd=Infinity;for(let i of ids){let dd=dist(d,ps[i]);if(dd<bd-1e-14||(Math.abs(dd-bd)<=1e-14&&i<bi)){bd=dd;bi=i}}return bi}
const all=original.map((_,i)=>i);
function sample(kind,seed,N){let r=rng(seed),ds=[];function gauss(){return Math.sqrt(-2*Math.log(Math.max(1e-12,r())))*Math.cos(2*Math.PI*r())}
while(ds.length<N){let p;if(kind==="uniform"||r()<.2)p=[r()*5.5,r()*21.65];else{let h=r(),c=h<.55?[1.5,5]:h<.85?[3.7,12]:[2.4,19];p=[c[0]+gauss()*.65,c[1]+gauss()*1.25]}
if(p[0]>=0&&p[0]<=5.5&&p[1]>=0&&p[1]<=21.65)ds.push(p)}return ds}
function metrics(ds,ps,own){let loads=Array(n).fill(0),ss=0,wrong=0;for(let k=0;k<ds.length;k++){loads[own[k]]++;let d=dist(ds[k],ps[own[k]]);ss+=d;let nn=nearest(ds[k],ps,all);if(d>dist(ds[k],ps[nn])+1e-10)wrong++}
let mean=ds.length/n;return {cv:Math.sqrt(loads.reduce((s,w)=>s+(w-mean)**2,0)/n)/mean,rms:Math.sqrt(ss/ds.length),empty:loads.filter(x=>!x).length,min:Math.min(...loads),max:Math.max(...loads),wrong:wrong/ds.length}}
function run(ds,method,seed,sweeps){let ps=original.map(p=>p.slice()),own=ds.map(d=>nearest(d,ps,all)),r=rng(seed+999),history=[{sweep:0,...metrics(ds,ps,own)}], clipped=0,steps=0,stableSweeps=0,termination='sweep cap',lastSweep=0;
for(let it=1;it<=sweeps;it++){let maxMovement=0,ownershipChanges=0;lastSweep=it;if(method==="local"){let groups=Array.from({length:n},()=>[]);own.forEach((o,k)=>groups[o].push(k));let order=movable.slice();for(let k=order.length-1;k>0;k--){let j=Math.floor(r()*(k+1));[order[k],order[j]]=[order[j],order[k]]}
for(let v of order){let ids=[v,...adj[v]].sort((a,b)=>a-b),pool=ids.flatMap(i=>groups[i]);if(!pool.length)continue;let q=[0,0];for(let k of pool){q[0]+=ds[k][0]/pool.length;q[1]+=ds[k][1]/pool.length}let p=project(q,adj[v].map(i=>ps[i]));if(dist(p,q)>1e-15)clipped++;steps++;maxMovement=Math.max(maxMovement,Math.sqrt(dist(ps[v],p)));ps[v]=p;for(let i of ids)groups[i]=[];for(let k of pool){let j=nearest(ds[k],ps,ids);if(own[k]!==j)ownershipChanges++;own[k]=j;groups[j].push(k)}}
}else{let sums=Array.from({length:n},()=>[0,0,0]);own.forEach((o,k)=>{sums[o][0]+=ds[k][0];sums[o][1]+=ds[k][1];sums[o][2]++});for(let i of (method==="kmeansFree"?all:movable))if(sums[i][2]){let p=[sums[i][0]/sums[i][2],sums[i][1]/sums[i][2]];maxMovement=Math.max(maxMovement,Math.sqrt(dist(ps[i],p)));ps[i]=p;}let newOwn=ds.map(d=>nearest(d,ps,all));ownershipChanges=newOwn.filter((v,k)=>v!==own[k]).length;own=newOwn}
let edgeUnit=Math.sqrt(dist(original[movable[0]],original[adj[movable[0]][0]]));stableSweeps=ownershipChanges===0&&maxMovement<1e-6*edgeUnit?stableSweeps+1:0;let done=stableSweeps>=5;if([1,5,10,20,40,80,160].includes(it)||it===sweeps||done)history.push({sweep:it,maxMovement,ownershipChanges,...metrics(ds,ps,own)});if(done){termination='stabilized';break}}
return {method,history,termination,lastSweep,stableSweeps,clipRate:clipped/Math.max(1,steps),ps,own}}

function fitMesh(ds){
 let mx=0,my=0;for(let p of ds){mx+=p[0]/ds.length;my+=p[1]/ds.length}
 let xx=0,yy=0,xy=0;for(let p of ds){xx+=(p[0]-mx)**2;yy+=(p[1]-my)**2;xy+=(p[0]-mx)*(p[1]-my)}
 let angle=.5*Math.atan2(2*xy,xx-yy),long=[Math.cos(angle),Math.sin(angle)],short=[-long[1],long[0]];
 let lo=[Infinity,Infinity],hi=[-Infinity,-Infinity];
 for(let p of ds){let z=[p[0]*short[0]+p[1]*short[1],p[0]*long[0]+p[1]*long[1]];for(let k=0;k<2;k++){lo[k]=Math.min(lo[k],z[k]);hi[k]=Math.max(hi[k],z[k])}}
 let meshLo=[Math.min(...original.map(p=>p[0])),Math.min(...original.map(p=>p[1]))],meshHi=[Math.max(...original.map(p=>p[0])),Math.max(...original.map(p=>p[1]))];
 let scale=Math.max(...[0,1].map(k=>(hi[k]-lo[k])/(meshHi[k]-meshLo[k])));
 original=original.map(p=>{let z=p.map((v,k)=>(v-(meshLo[k]+meshHi[k])/2)*scale+(lo[k]+hi[k])/2);return [z[0]*short[0]+z[1]*long[0],z[0]*short[1]+z[1]*long[1]]});
 return {scale,angle,domainExtents:lo.map((v,k)=>hi[k]-v)}
}
if(!data.length||!data.every(p=>p.length===2&&p.every(Number.isFinite)))throw Error("Invalid coordinates");
const mesh=fitMesh(data),results=[];
for(let seed of [11,22,33])results.push({seed,...run(data,"local",seed,320)});
for(let method of ["kmeansFixed","kmeansFree"])results.push({seed:11,...run(data,method,11,320)});
return {count:data.length,mesh,initialPositions:original,adjacency:adj,results};
}
module.exports = calculate;
