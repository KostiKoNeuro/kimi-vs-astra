// Instrument a COPY of the original generator. The delivered browser file is never modified.
// npm install three@0.170.0 esbuild@0.24.2, then node make_export.mjs
import {readFile,writeFile} from 'node:fs/promises';
import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
const dir=fileURLToPath(new URL('.',import.meta.url));
let source=await readFile(new URL('scene_source.js',import.meta.url),'utf8');
source=source.replace('let totalBoxes=0;',`let currentGroup='01 Ground/Foundation';const lanternExport=[],signExport=[],buildingExport=[];let buildingNumber=0,stallNumber=0;let totalBoxes=0;`);
source=source.replace('batches[mat].push({x,y,z,w,h,d,c,ry})','batches[mat].push({x,y,z,w,h,d,c,ry,group:currentGroup})');
for(const [fn,body] of Object.entries({
 building:`const prev=currentGroup;currentGroup='02 Buildings/Residential '+String(++buildingNumber).padStart(2,'0');buildingExport.push(args);try{return original_building(...args)}finally{currentGroup=prev}`,
 stall:`const prev=currentGroup;currentGroup='03 Market stalls/Stall '+String(++stallNumber).padStart(2,'0')+' '+args[3];try{return original_stall(...args)}finally{currentGroup=prev}`,
 sign:`const prev=currentGroup;currentGroup='04 Signs/'+args[0]+' '+signExport.length;signExport.push(args);try{return original_sign(...args)}finally{currentGroup=prev}`,
 lantern:`const prev=currentGroup;currentGroup='05 Lanterns/Lantern '+String(lanternExport.length+1).padStart(2,'0');lanternExport.push(args);try{return original_lantern(...args)}finally{currentGroup=prev}`
})){
 source=source.replace('function '+fn+'(', 'function original_'+fn+'(');
 source+=`\nfunction ${fn}(...args){${body}}\n`;
}
source=source.replace('// Dining islands,',"currentGroup='06 Street details/Dining';\n// Dining islands,");
source=source.replace('// Gate and hanging',"currentGroup='07 Wires and frames/Overhead cables';\n// Gate and hanging");
source=source.replace('// Details to discover:',"currentGroup='06 Street details/Crates plants and cat';\n// Details to discover:");
source+=`\nconst exportButton=document.createElement('button');exportButton.textContent='EXPORT ORIGINAL DIORAMA TO BLENDER';exportButton.style='position:fixed;top:12px;left:12px;padding:16px;z-index:99';document.body.append(exportButton);
exportButton.onclick=async()=>{
 exportButton.disabled=true;exportButton.textContent='Exporting exact geometry and motion…';
 const plain={};for(const [m,bs]of Object.entries(batches))plain[m]=bs.map(b=>({...b,c:(b.c instanceof THREE.Color?b.c:new THREE.Color(b.c)).toArray()}));
 const motion=[];for(let f=0;f<240;f++){
  const t=f/24;const people=actors.map(a=>{let x=a.x,z=a.z,h=a.heading;if(a.behavior==='walk'){const u=(a.offset+t*a.speed/62)%1;route.getPointAt(u,pos);route.getTangentAt(u,tangent);x=pos.x+(a.index%3-1)*.4;z=pos.z;h=Math.atan2(tangent.x,tangent.z);}return [x,z,h]});
  const p=new THREE.Vector3(),l=new THREE.Vector3();cinemaPath.getPoint(t/30,p);lookPath.getPoint(t/30,l);motion.push({people,camera:p.toArray(),look:l.toArray(),time:t});
 }
 const payload={schema:1,source:'Part 1 original procedural generator, seed 78291',static:plain,actors,scooters,steamEmitters,steamSeeds,rainSeeds,lanterns:lanternExport,signs:signExport,buildings:buildingExport,lights:glowSources.map(l=>({position:l.position.toArray(),color:l.color.toArray(),intensity:l.intensity})),motion,fov:camera.fov};
 const result=await fetch('/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});exportButton.textContent=result.ok?'EXPORTED — diorama.json':'EXPORT FAILED';exportButton.disabled=false;
};`;
const result=await build({stdin:{contents:source,resolveDir:dir,sourcefile:'instrumented_scene.js',loader:'js'},bundle:true,minify:true,write:false,format:'iife',target:'es2020'});
const original=await readFile(new URL('../../index.html',import.meta.url),'utf8');
const lastStart=original.lastIndexOf('<script>'),lastEnd=original.lastIndexOf('</script>');
const html=original.slice(0,lastStart)+'<script>'+result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script')+'</script>'+original.slice(lastEnd+9);
await writeFile(new URL('export.html',import.meta.url),html);console.log('Export page built');
