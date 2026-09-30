'use strict';
const fs=require('fs'),crypto=require('crypto'),assert=require('assert');
const source='Manhattan_Pickups_2015-01-15_0800-0815.json',bytes=fs.readFileSync(source),hash=crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(hash,'eabfaa334493582b9f407956134e408fb066ba9d0ee3ca8c78bb737b6dc77f77');
const points=JSON.parse(bytes).points,retained=JSON.parse(fs.readFileSync('Manhattan_Vertex_Only_Full_Outputs.json')).runs.map(r=>r.result);
assert.equal(points.length,5986);
function rng(seed){return ()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296}}
function dist(a,b){return (a[0]-b[0])**2+(a[1]-b[1])**2}
function nearest(d,ps,ids){let bi=-1,bd=Infinity;for(let i of ids){let dd=dist(d,ps[i]);if(dd<bd-1e-14||(Math.abs(dd-bd)<=1e-14&&i<bi)){bd=dd;bi=i}}return bi}
function metrics(ds,ps,own){const n=ps.length,loads=Array(n).fill(0),sums=ps.map(()=>[0,0]);let ss=0;for(let k=0;k<ds.length;k++){const o=own[k];loads[o]++;sums[o][0]+=ds[k][0];sums[o][1]+=ds[k][1];ss+=dist(ds[k],ps[o]);}const centers=sums.map((p,i)=>loads[i]?p.map(x=>x/loads[i]):p);let css=0;for(let k=0;k<ds.length;k++)css+=dist(ds[k],centers[own[k]]);const mean=ds.length/n,variance=loads.reduce((s,w)=>s+(w-mean)**2,0)/n;return {K:n,cv:Math.sqrt(variance)/mean,populationVariance:variance,min:Math.min(...loads),max:Math.max(...loads),empty:loads.filter(x=>!x).length,rmsOperationalKm:Math.sqrt(ss/ds.length),rmsCentroidKm:Math.sqrt(css/ds.length),loads}}
function run(ds,base,seed){
 const original=base.initialPositions,adj=base.adjacency,n=original.length,all=original.map((_,i)=>i),movable=all.filter(i=>adj[i].length===3),fixed=all.filter(i=>adj[i].length!==3);
 assert.equal(n,100);assert.equal(movable.length,68);assert.equal(fixed.length,32);
 let ps=original.map(p=>p.slice()),own=ds.map(d=>nearest(d,ps,all)),r=rng(seed+999),history=[{sweep:0,...metrics(ds,ps,own)}],steps=0,stableSweeps=0,termination='sweep cap',lastSweep=0,maxWeightError=0,skipped=0;
 const edgeUnit=Math.sqrt(dist(original[movable[0]],original[adj[movable[0]][0]]));
 for(let it=1;it<=320;it++){
  let maxMovement=0,ownershipChanges=0;lastSweep=it;let groups=Array.from({length:n},()=>[]);own.forEach((o,k)=>groups[o].push(k));let order=movable.slice();
  for(let k=order.length-1;k>0;k--){let j=Math.floor(r()*(k+1));[order[k],order[j]]=[order[j],order[k]]}
  for(let v of order){
   let ids=[v,...adj[v]].sort((a,b)=>a-b),pool=ids.flatMap(i=>groups[i]);if(!pool.length){skipped++;continue}
   let previous=pool.map(k=>own[k]),beforeWeights=adj[v].map(j=>groups[j].length),added=adj[v].map(()=>0);
   for(let k of groups[v]){let j=nearest(ds[k],ps,adj[v]);added[adj[v].indexOf(j)]++;groups[j].push(k);own[k]=j}groups[v]=[];
   const weights=adj[v].map((j,i)=>{assert.equal(groups[j].length,beforeWeights[i]+added[i]);return groups[j].length});assert.equal(weights.reduce((a,b)=>a+b,0),pool.length);
   let q=[0,0];for(let j of adj[v]){q[0]+=groups[j].length*ps[j][0]/pool.length;q[1]+=groups[j].length*ps[j][1]/pool.length}
   const auditQ=[0,1].map(d=>adj[v].reduce((s,j,i)=>s+weights[i]*ps[j][d],0)/pool.length);maxWeightError=Math.max(maxWeightError,Math.sqrt(dist(q,auditQ)));assert(Math.sqrt(dist(q,auditQ))<1e-12);
   steps++;maxMovement=Math.max(maxMovement,Math.sqrt(dist(ps[v],q)));ps[v]=q;
   for(let j of adj[v]){let remain=[];for(let k of groups[j]){let best=nearest(ds[k],ps,ids);if(best===v){own[k]=v;groups[v].push(k)}else remain.push(k)}groups[j]=remain}
   ownershipChanges+=pool.filter((k,i)=>own[k]!==previous[i]).length;
   assert.equal(ids.reduce((s,j)=>s+groups[j].length,0),pool.length);
  }
  const seen=new Uint8Array(ds.length);for(let j=0;j<n;j++)for(let k of groups[j]){assert.equal(own[k],j);assert.equal(seen[k],0);seen[k]=1}assert(seen.every(x=>x===1));
  for(let i of fixed)assert.deepStrictEqual(ps[i],original[i]);
  stableSweeps=ownershipChanges===0&&maxMovement<1e-6*edgeUnit?stableSweeps+1:0;const done=stableSweeps>=5;
  if([1,5,10,20,40,80,160,320].includes(it)||done)history.push({sweep:it,maxMovement,ownershipChanges,...metrics(ds,ps,own)});
  if(done){termination='stabilized';break}
 }
 return {method:'rule2_remove_redistribute_weighted_position_reclaim',seed,count:ds.length,termination,lastSweep,stableSweeps,final:metrics(ds,ps,own),verification:{ownershipConserved:true,fixedVerticesUnchanged:true,postRemovalWeightsVerified:true,maxWeightError,checkedUpdates:steps,skippedEmptyPools:skipped,movable:68,fixed:32,edgeUnit},history,ps,own}
}
const checks=[],expected=[1.1101801655587258,1.0647769719523428,.9280355596635292];for(const [i,seed] of [11,22,33].entries()){const r=run(points.slice(0,400),retained.find(r=>r.count===400),seed);assert(Math.abs(r.final.cv-expected[i])<1e-14);assert.equal(r.lastSweep,320);checks.push(r);console.log(JSON.stringify({crosscheck400:seed,cv:r.final.cv,matched:true}))}
const base=retained.find(r=>r.count===5986),results=[];for(const seed of [11,22,33]){const r=run(points,base,seed);results.push(r);console.log(JSON.stringify({seed,termination:r.termination,lastSweep:r.lastSweep,...r.final,loads:undefined,verification:r.verification}))}
const prior=base.results.filter(r=>r.method==='local').map(r=>({method:'rule3_pooled_dot_centroid',seed:r.seed,termination:r.termination,lastSweep:r.lastSweep,final:metrics(points,r.ps,r.own)}));
const l=JSON.parse(fs.readFileSync('work/four_compare/lloyd.json'));assert.deepStrictEqual(l.initialPositions,base.initialPositions);prior.push({method:'Lloyd_all_centers_farthest_reseed',seed:null,termination:l.termination,lastSweep:l.lastSweep,final:metrics(points,l.ps,l.own)});
const historical=JSON.parse(fs.readFileSync('work/four_compare/results.json')).solutions.slice(0,2);
const output={inputSha256:hash,count:points.length,coordinateUnits:'km',initialPositions:base.initialPositions,adjacency:base.adjacency,mesh:base.mesh,results,crosschecks400:checks,prior,historical,stopping:'Five consecutive sweeps with sum of net ownership changes per full vertex update = 0 and maximum movement < 1e-6 initial edge length; cap 320.',runtime:process.version};
fs.writeFileSync('work/rule2/full_outputs.json',JSON.stringify(output));
const compact={...output};delete compact.initialPositions;delete compact.adjacency;compact.results=results.map(({ps,own,history,...r})=>({...r,final:{...r.final,loads:undefined}}));compact.crosschecks400=checks.map(r=>({seed:r.seed,cv:r.final.cv,termination:r.termination,lastSweep:r.lastSweep}));compact.prior=prior.map(r=>({...r,final:{...r.final,loads:undefined}}));compact.historical=historical.map(({loads,...r})=>r);fs.writeFileSync('work/rule2/metrics.json',JSON.stringify(compact,null,2));
