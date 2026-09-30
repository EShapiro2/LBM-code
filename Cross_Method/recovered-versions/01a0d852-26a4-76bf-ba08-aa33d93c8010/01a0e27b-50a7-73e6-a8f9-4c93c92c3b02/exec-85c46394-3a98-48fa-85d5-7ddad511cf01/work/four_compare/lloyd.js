const fs=require('fs');const D=JSON.parse(fs.readFileSync('Manhattan_Pickups_2015-01-15_0800-0815.json')).points;const old=JSON.parse(fs.readFileSync('Manhattan_Vertex_Only_Full_Outputs.json')).runs.find(r=>r.result.count===5986).result;const initial=old.initialPositions;let ps=initial.map(p=>p.slice());
function dist(a,b){return (a[0]-b[0])**2+(a[1]-b[1])**2}
function assign(){return D.map(p=>{let bi=-1,bd=Infinity;for(let i=0;i<ps.length;i++){let dd=dist(p,ps[i]);if(dd<bd-1e-14||(Math.abs(dd-bd)<=1e-14&&i<bi)){bi=i;bd=dd}}return bi})}
function metrics(own){let loads=Array(100).fill(0),ss=0;own.forEach((o,k)=>{loads[o]++;ss+=dist(D[k],ps[o])});let mean=D.length/100,variance=loads.reduce((a,n)=>a+(n-mean)**2,0)/100;return {cv:Math.sqrt(variance)/mean,variance,rms:Math.sqrt(ss/D.length),empty:loads.filter(n=>n===0).length,min:Math.min(...loads),max:Math.max(...loads),wrong:0,loads}}
let own=assign(),history=[{sweep:0,...metrics(own)}],reseedLog=[],stable=0,lastSweep=0,termination='sweep cap';let v=old.adjacency.findIndex(a=>a.length===3),edgeUnit=Math.sqrt(dist(initial[v],initial[old.adjacency[v][0]]));
for(let it=1;it<=320;it++){
 let before=ps.map(p=>p.slice()),prior=own.slice(),sums=ps.map(()=>[0,0,0]);own.forEach((o,k)=>{sums[o][0]+=D[k][0];sums[o][1]+=D[k][1];sums[o][2]++});for(let i=0;i<100;i++)if(sums[i][2])ps[i]=[sums[i][0]/sums[i][2],sums[i][1]/sums[i][2]];own=assign();
 for(let guard=0;guard<100;guard++){
  let counts=Array(100).fill(0);for(let o of own)counts[o]++;let empty=counts.indexOf(0);if(empty<0)break;
  let far=-1,fd=-1;for(let k=0;k<D.length;k++){let dd=dist(D[k],ps[own[k]]);if(dd>fd){fd=dd;far=k}}
  ps[empty]=D[far].slice();reseedLog.push({sweep:it,center:empty,point:far,squaredDistance:fd});own=assign();
 }
 const maxMovement=Math.max(...ps.map((p,i)=>Math.sqrt(dist(p,before[i])))),ownershipChanges=own.filter((o,k)=>o!==prior[k]).length;
 stable=ownershipChanges===0&&maxMovement<1e-6*edgeUnit?stable+1:0;lastSweep=it;
 if([1,5,10,20,40,80,160,320].includes(it)||stable>=5)history.push({sweep:it,maxMovement,ownershipChanges,...metrics(own)});
 if(stable>=5){termination='stabilized';break}
}
let result={method:'Lloyd_all_centers_farthest_reseed',seed:null,termination,lastSweep,stableSweeps:stable,reseedCount:reseedLog.length,reseedLog,initialPositions:initial,ps,own,history,final:metrics(own),reseedProcedure:'Each sweep: update nonempty centroids; globally reassign. Repeatedly select the lowest-index empty center and move it to the input point with greatest squared distance from its current assigned center (exact ties: lowest original point index); globally reassign after each reseed. At most 100 reseeds per sweep. Nearest-center ties use the supplied 1e-14 tolerance and lowest center index. Stability uses net end-of-sweep movement < 1e-6 times initial edge length and zero ownership changes for five consecutive sweeps; cap 320.'};fs.writeFileSync('work/four_compare/lloyd.json',JSON.stringify(result));console.log(JSON.stringify({termination,lastSweep,reseedCount:reseedLog.length,final:result.final}));
