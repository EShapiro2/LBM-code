const fs=require('fs'),crypto=require('crypto'),calculate=require('./calculate.js');
const input='Manhattan_Pickups_2015-01-15_0800-0815.json';
const inputBytes=fs.readFileSync(input),data=JSON.parse(inputBytes),points=data.points;
if(points.length!==5986)throw Error('Expected 5986 points');
for(let i=0;i<points.length;i++){
 const [qx,qy]=data.quantized_xy[i];
 if(points[i][0]!==qx/65535*8.8103||points[i][1]!==qy/65535*18.8542)throw Error('Quantized mismatch '+i);
}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const audit={actualExecution:true,runtime:process.version,inputFile:input,inputFileSHA256:sha(inputBytes),coordinateOrder:'original embedded order, filtered to 0 <= seconds_after_0800 < 900',units:'kilometres',angleUnits:'radians',functionSourceSHA256:sha(fs.readFileSync('work/vertex_only/calculate.js'))};
let runs=[];
for(const ds of [points.slice(0,400),points]){
 const start=performance.now();
 const result=calculate(ds);
 runs.push({elapsedSeconds:(performance.now()-start)/1000,result});
 console.error('Completed count '+ds.length+' in '+runs.at(-1).elapsedSeconds.toFixed(3)+' seconds');
}
const full={audit,runs};
fs.writeFileSync('Manhattan_Vertex_Only_Full_Outputs.json',JSON.stringify(full));
const summary={audit,runs:runs.map(({result:r,elapsedSeconds},i)=>{
 const ds=i===0?points.slice(0,400):points;
 return {count:r.count,coordinateRange:{x:[Math.min(...ds.map(p=>p[0])),Math.max(...ds.map(p=>p[0]))],y:[Math.min(...ds.map(p=>p[1])),Math.max(...ds.map(p=>p[1]))]},mesh:r.mesh,vertices:r.initialPositions.length,movable:r.adjacency.filter(a=>a.length===3).length,initial:r.results[0].history[0],results:r.results.map(z=>({method:z.method,seed:z.seed,termination:z.termination,lastSweep:z.lastSweep,final:z.history.at(-1)}))};
})};
fs.writeFileSync('work/vertex_only/summary.json',JSON.stringify(summary));
console.log(JSON.stringify(summary));
