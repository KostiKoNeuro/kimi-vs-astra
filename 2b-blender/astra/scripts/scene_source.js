import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { Reflector } from 'three/addons/objects/Reflector.js';

/* SHENZHEN, AFTER THE RAIN
 * Art direction: a dense, handmade city fragment; midnight jade, dusty concrete,
 * vermilion lanterns, apricot kitchens and occasional electric turquoise.
 * All visible scene geometry uses BoxGeometry. Text is sampled from a local
 * system font into real cube geometry, never applied as an image or texture.
 * Scene assets: original procedural geometry. Renderer: Three.js, MIT license.
 */
const TAU = Math.PI * 2, clamp = THREE.MathUtils.clamp;
let seed = 78291;
const random = () => { seed = (Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296; };
const range = (a,b)=>a+(b-a)*random(), pick=a=>a[Math.floor(random()*a.length)];
const canvas = document.querySelector('canvas');
const scene = new THREE.Scene();
scene.background = new THREE.Color('#101d28');
scene.fog = new THREE.FogExp2('#101d28', .0105);
const renderer = new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.35));
renderer.setSize(innerWidth,innerHeight);
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.12;
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate=false;
const camera=new THREE.PerspectiveCamera(42,innerWidth/innerHeight,.2,180);
const controls=new OrbitControls(camera,canvas);
controls.enableDamping=true;controls.dampingFactor=.065;
controls.minDistance=7;controls.maxDistance=85;
controls.maxPolarAngle=Math.PI*.485;controls.minPolarAngle=.14;
controls.enabled=false;controls.target.set(0,5,0);
const hemi=new THREE.HemisphereLight('#97c9dc','#3c2a38',1.25);scene.add(hemi);
const moon=new THREE.DirectionalLight('#acdaef',2.3);moon.position.set(-18,33,19);
moon.castShadow=true;moon.shadow.mapSize.set(2048,2048);
Object.assign(moon.shadow.camera,{left:-25,right:25,top:30,bottom:-24,near:1,far:85});
moon.shadow.bias=-.0003;moon.shadow.normalBias=.06;scene.add(moon);
const rim=new THREE.DirectionalLight('#459cb0',1.1);rim.position.set(15,10,-18);scene.add(rim);
const glowSources=[];
function light(x,y,z,color,intensity=45,distance=15){const l=new THREE.PointLight(color,intensity,distance,2);l.position.set(x,y,z);scene.add(l);glowSources.push(l);return l;}
light(-8,3.1,4,'#ff983f',55,16);light(8,3,3,'#ffa553',50,16);
light(-3,3,-5,'#ffb361',50,14);light(5,3,-5,'#ff507a',40,13);
light(-8,3,9,'#ff9438',50,15);light(7,3,9,'#58c9bb',35,13);
light(12,9,-2,'#29cec7',65,15);light(-13,7,-2,'#e65a75',40,12);

const cube=new THREE.BoxGeometry(1,1,1);
const mats={
 stone:new THREE.MeshStandardMaterial({roughness:.88,metalness:.03}),
 metal:new THREE.MeshStandardMaterial({roughness:.39,metalness:.56}),
 glazed:new THREE.MeshStandardMaterial({roughness:.3,metalness:.15}),
 glow:new THREE.MeshBasicMaterial({toneMapped:false}),
 soft:new THREE.MeshBasicMaterial({toneMapped:false})
};
const batches={stone:[],metal:[],glazed:[],glow:[],soft:[]};
const dummy=new THREE.Object3D(),color=new THREE.Color();
const gray='#31434b', charcoal='#15252f', warm='#ffab55', jade='#296b68';
let totalBoxes=0;
function box(x,y,z,w,h,d,c,mat='stone',ry=0){batches[mat].push({x,y,z,w,h,d,c,ry});totalBoxes++;}
function glowBox(x,y,z,w,h,d,c,power=2.5,ry=0){box(x,y,z,w,h,d,new THREE.Color(c).multiplyScalar(power),'glow',ry);}
function localBox(origin,x,y,z,w,h,d,c,mat='stone'){
 const co=Math.cos(origin.r||0),si=Math.sin(origin.r||0);
 box(origin.x+x*co+z*si,origin.y+y,origin.z-x*si+z*co,w,h,d,c,mat,origin.r||0);
}
function vline(a,b,c,width=.065,step=.15,mat='stone'){
 const n=Math.ceil(a.distanceTo(b)/step);for(let i=0;i<=n;i++){const p=a.clone().lerp(b,i/n);box(p.x,p.y,p.z,width,width,width,c,mat);}
}
function wire(a,b,sag=.7,c='#101e26',width=.055){
 const n=Math.ceil(a.distanceTo(b)/(width*.85));for(let i=0;i<=n;i++){const t=i/n;box(THREE.MathUtils.lerp(a.x,b.x,t),THREE.MathUtils.lerp(a.y,b.y,t)-Math.sin(t*Math.PI)*sag,THREE.MathUtils.lerp(a.z,b.z,t),width,width,width,c);}
}
function potPlant(x,y,z,size=1){
 box(x,y+.22*size,z,.48*size,.44*size,.48*size,'#8d6050');
 box(x,y+.46*size,z,.56*size,.1*size,.56*size,'#b48261');
 for(let j=0;j<12;j++)box(x+range(-.27,.27)*size,y+range(.5,1.1)*size,z+range(-.27,.27)*size,.22*size,.22*size,.22*size,pick(['#37634d','#4a8563','#79925e']));
}
// Tiny cubes form glyphs. The canvas is only a transient procedural sampler.
const glyphCache=new Map();
function glyph(ch){
 if(glyphCache.has(ch))return glyphCache.get(ch);
 const cv=document.createElement('canvas');cv.width=cv.height=24;
 const cx=cv.getContext('2d',{willReadFrequently:true});cx.fillStyle='#fff';
 cx.font='bold 22px "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif';cx.textAlign='center';cx.textBaseline='middle';cx.fillText(ch,12,12);
 const pixels=cx.getImageData(0,0,24,24).data,pts=[];
 for(let y=0;y<24;y++)for(let x=0;x<24;x++)if(pixels[(y*24+x)*4+3]>115)pts.push([x-11.5,11.5-y]);
 glyphCache.set(ch,pts);return pts;
}
function lettering(text,x,y,z,size,c,ry=0,vertical=false,power=2.7){
 const step=size/24, co=Math.cos(ry),si=Math.sin(ry),chars=Array.from(text);
 chars.forEach((ch,i)=>{
  const off=(i-(chars.length-1)/2)*size*1.13;
  for(const p of glyph(ch)){
   const lx=p[0]*step+(vertical?0:off),ly=p[1]*step-(vertical?off:0);
   glowBox(x+lx*co,y+ly,z-lx*si,step*.94,step*.94,step*.72,c,power,ry);
  }
 });
}
function sign(text,x,y,z,w,h,c,ry=0,vertical=false){
 box(x,y,z,w,h,.19,'#182c36','metal',ry);
 const o={x,y,z,r:ry};
 localBox(o,0,h/2,0,w+.12,.08,.26,c,'glazed');localBox(o,0,-h/2,0,w+.12,.08,.26,c,'glazed');
 localBox(o,-w/2,0,0,.08,h,.26,c,'glazed');localBox(o,w/2,0,0,.08,h,.26,c,'glazed');
 const charSize=vertical?Math.min(w*.71,h/(text.length*1.2)):Math.min(h*.67,w/(text.length*1.2));
 lettering(text,x+Math.sin(ry)*.13,y,z+Math.cos(ry)*.13,charSize,c,ry,vertical);
}

// The cutaway city block: basalt foundation, stepped edges, paving and drains.
box(0,-.66,0,36,1.12,30,'#182b36');
box(0,-1.23,0,35.25,.15,29.25,'#0d1d27','metal');
for(let x=-17.75;x<18;x+=.5){box(x,-.12,14.86,.46,.22,.24,'#687b7c');box(x,-.12,-14.86,.46,.22,.24,'#435b65');}
for(let z=-14.5;z<15;z+=.5){box(-17.86,-.12,z,.24,.22,.46,'#536b72');box(17.86,-.12,z,.24,.22,.46,'#536b72');}
for(let i=0;i<100;i++){
 const x=range(-17.6,17.6),z=range(-14.6,14.6);
 box(x,.035,z,range(.2,.9),.02,range(.12,.4),pick(['#233c43','#354a4b','#1c3038']),'metal');
}
for(let x=-16;x<=16;x+=2.1)box(x,.063,13.5,.9,.025,.1,'#bda96b','glazed');
for(let x=-14.6;x<-10.5;x+=.65)box(x,.07,10.8,.33,.03,2.7,'#b1b2a0','glazed');
for(let x of [-16,16])for(let z=-8;z<12;z+=5){box(x,.08,z,.55,.05,1.05,'#17232b','metal');for(let i=0;i<6;i++)box(x,.112,z-.42+i*.16,.45,.015,.04,'#667575','metal');}

// A cube-thin layer of rainwater, with actual planar reflections and procedural
// stone joints, broken puddles and very restrained rain ripples.
const reflectionShader={
 uniforms:{color:{value:new THREE.Color('#1e3742')},tDiffuse:{value:null},textureMatrix:{value:null},time:{value:0}},
 vertexShader:`uniform mat4 textureMatrix; varying vec4 vMirror; varying vec2 vGround;
 void main(){vMirror=textureMatrix*vec4(position,1.0);vGround=position.xy;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
 fragmentShader:`uniform sampler2D tDiffuse;uniform float time;varying vec4 vMirror;varying vec2 vGround;
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 void main(){
 vec2 p=vGround;vec2 uv=vMirror.xy/vMirror.w;
 float ripple=sin(p.x*13.0+p.y*7.0-time*2.1)*sin(p.y*11.0-time*1.7);
 uv+=vec2(ripple*.00075,sin(p.x*6.0+time)*.0005);
 vec3 reflection=texture2D(tDiffuse,uv).rgb;
 vec2 cell=floor(p*1.9);float grain=hash(cell);
 vec2 joint=abs(fract(p*1.9)-.5);float mortar=smoothstep(.455,.495,max(joint.x,joint.y));
 float puddle=.5+.5*sin(p.x*.67+sin(p.y*.4))*cos(p.y*.51);
 vec3 stone=mix(vec3(.026,.042,.048),vec3(.06,.081,.083),grain);
 stone*=1.0-mortar*.38;
 vec3 col=mix(stone,reflection,.28+puddle*.37);
 col+=vec3(.14,.055,.012)*exp(-dot(p-vec2(-8.,-7.),p-vec2(-8.,-7.))*.045);
 col+=vec3(.015,.055,.05)*exp(-dot(p-vec2(9.,-6.),p-vec2(9.,-6.))*.04);
 gl_FragColor=vec4(col,1.0);
 }`
};
const water=new Reflector(new THREE.BoxGeometry(35.7,29.7,.008),{textureWidth:1024,textureHeight:1024,clipBias:.003,shader:reflectionShader,multisample:0});
water.rotation.x=-Math.PI/2;water.position.y=.045;scene.add(water);

const buildingPalette=['#58686b','#566c70','#667574','#536568','#63716c'];
function building(x,z,w,d,h,index){
 const c=buildingPalette[index%buildingPalette.length];
 box(x,h/2+.25,z,w,h,d,c);
 // Regular facade seams, concrete ribs, floor bands and roof coping read as voxels.
 for(let y=.8;y<h;y+=1.75){
  box(x,y,z+d/2+.07,w+.16,.12,.18,'#354c56');
  box(x+w/2+.07,y,z,.18,.12,d,'#3f5961');
  box(x-w/2-.07,y,z,.18,.12,d,'#3f5961');
 }
 for(let xx=x-w/2+.15;xx<x+w/2;xx+=1.45)box(xx,h/2,z+d/2+.12,.12,h,.24,'#748280');
 for(let yy=2;yy<h-1;yy+=1.8){
  for(let xx=x-w/2+.8;xx<x+w/2-.4;xx+=1.45){
   const lit=random()>.32;
   box(xx,yy,z+d/2+.16,.94,1.2,.13,'#20343d','metal');
   const cc=pick(['#ffe0a1','#ffc67d','#e7d8ad','#89bec0']);
   if(lit)glowBox(xx,yy,z+d/2+.24,.73,1.03,.06,cc,range(.8,1.6));
   else box(xx,yy,z+d/2+.24,.73,1.03,.06,'#263f4b','glazed');
   box(xx,yy,z+d/2+.3,.045,1.12,.06,'#344b51');box(xx,yy-.08,z+d/2+.3,.84,.045,.06,'#344b51');
   if(lit&&random()>.58)box(xx+.14,yy,z+d/2+.285,.24,1.04,.025,'#956f55');
   if(random()>.57){box(xx+.57,yy-.47,z+d/2+.42,.42,.36,.46,'#8f9c96');for(let q=0;q<3;q++)box(xx+.57,yy-.55+q*.08,z+d/2+.66,.32,.025,.04,'#4b6469');}
   if(random()>.72){box(xx,yy-.72,z+d/2+.48,1.13,.12,.68,'#4c646b');for(let q=0;q<5;q++)box(xx-.48+q*.24,yy-.44,z+d/2+.79,.045,.5,.045,'#93a5a0','metal');}
  }
  for(const side of [-1,1])for(let zz=z-d/2+.8;zz<z+d/2-.5;zz+=1.45){
   box(x+side*(w/2+.05),yy,zz,.14,1.12,.82,'#213741');
   if(random()>.35)glowBox(x+side*(w/2+.13),yy,zz,.05,.94,.66,pick(['#ffd18e','#9bc9c6','#f6dcaf']),range(.7,1.3));
   box(x+side*(w/2+.17),yy,zz,.06,.04,.76,'#38515a');
  }
 }
 box(x,h+.32,z,w+.4,.28,d+.4,'#7c8c87');
 for(let k=0;k<3;k++){
  const xx=x-w*.28+k*w*.27;
  box(xx,h+.7,z-.6,1.05,.65,1.1,'#66807f','metal');
  for(let a=0;a<4;a++)box(xx-.34+a*.22,h+1.04,z-.6,.11,.035,.84,'#243e47','metal');
 }
 // Rooftop tank, pipes, a red aircraft beacon, aerial and washing lines.
 box(x-w*.25,h+1.2,z+d*.2,1.65,1.6,1.5,'#7d8e88','metal');
 box(x-w*.25,h+2.05,z+d*.2,1.85,.14,1.7,'#a1a89a','metal');
 box(x+w*.31,h+1.4,z,.07,2.2,.07,'#6c8a8e','metal');
 box(x+w*.31,h+2.3,z,.9,.06,.06,'#6c8a8e','metal');
 glowBox(x+w*.31,h+2.53,z,.11,.11,.11,'#ff504c',1.5);
 if(index%2===0){wire(new THREE.Vector3(x-w*.4,h+.7,z+d*.3),new THREE.Vector3(x+w*.4,h+.7,z+d*.3),.2);for(let n=0;n<5;n++)box(x-w*.28+n*.65,h+.36,z+d*.3,.43,.54,.07,pick(['#ae9a87','#618f99','#b68383','#e0c5a1']));}
 for(let k=0;k<2;k++)potPlant(x+w*.25,h+.46,z+d*.2-k*.8,.6);
}
building(-11.6,-10.2,5.9,6.4,17.3,0);
building(-4.5,-11.7,6.1,4.6,24.1,1);
building(2.5,-11.3,6,5.5,20.6,2);
building(9.5,-10.2,6.3,6.7,18.6,3);
building(14.25,-8.1,3.5,5.5,12.5,4);
building(-14,-3.1,5.1,6.2,7.1,2);
building(14.1,-2.1,4.5,6.1,7.4,0);
// Brick infill, electrical cabinets and drain pipes on the low street facades.
for(let side of [-1,1]){
 const wall=side<0?-11.42:11.82, front=side<0?-.15:.78;
 for(let y=.5;y<6.8;y+=.52)for(let z=-4.8;z<front;z+=.58)box(wall,y,z,.12,.45,.5,pick(['#546b6e','#4c6268','#6c7b77']));
 box(wall-side*.15,3.5,front,.14,6.8,.14,'#a07e64','metal');
 box(wall-side*.22,1.5,front-.65,.24,1.15,.82,'#7d8a7f','metal');
 for(let q=0;q<3;q++)box(wall-side*.37,1.7-q*.19,front-.65,.04,.07,.6,'#425b5d','metal');
}
sign('夜市',-16.65,6.5,.18,1.5,4.4,'#fa775e',0,true);
sign('深圳',12.15,10,-3.85,1.65,5.2,'#58ded1',0,true);
sign('旅馆',-8.5,12,-6.85,1.4,3.3,'#ff79a8',0,true);
sign('便利店',14.2,4.5,1.06,4.0,.9,'#a4d6af');
sign('公寓',2.7,21.1,-8.4,2.6,1,'#a2cbd0');

const steamEmitters=[],actors=[],scooters=[];
function bowl(x,y,z,scale=1,food='#d4ad68'){
 box(x,y,z,.38*scale,.13*scale,.38*scale,'#cec4a7','glazed');
 box(x,y+.07*scale,z,.29*scale,.035*scale,.29*scale,food);
 for(const s of [-1,1]){box(x+s*.18*scale,y+.09*scale,z,.06*scale,.15*scale,.38*scale,'#e7dac0','glazed');box(x,y+.09*scale,z+s*.18*scale,.38*scale,.15*scale,.06*scale,'#e7dac0','glazed');}
 box(x+.04*scale,y+.19*scale,z,.025*scale,.025*scale,.55*scale,'#c4945b');
}
function crate(x,y,z,c='#587c73',filled=true){
 box(x,y+.2,z,.77,.37,.64,c);
 for(let s of [-1,1])for(let k=0;k<4;k++)box(x-.28+k*.18,y+.21,z+s*.33,.10,.15,.025,'#203b3c');
 if(filled)for(let i=0;i<12;i++)box(x+range(-.27,.27),y+.43,z+range(-.22,.22),.16,.16,.16,pick(['#a6b75f','#638a47','#d59252','#cf6852']));
}
function stool(x,z,c='#bd5442',y=0){
 box(x,y+.48,z,.57,.13,.57,c,'glazed');
 for(let dx of [-.2,.2])for(let dz of [-.2,.2])box(x+dx,y+.23,z+dz,.09,.46,.09,c);
}
function table(x,z,style=0){
 box(x,1,z,1.65,.14,1.18,style?'#6a9990':'#d1a779','glazed');
 for(let dx of [-.65,.65])for(let dz of [-.43,.43])box(x+dx,.5,z+dz,.1,1,.1,'#536b65','metal');
 for(let s of [-1,1]){stool(x+s*1.12,z);bowl(x+s*.4,1.13,z,.85);}
 box(x,1.18,z-.33,.13,.27,.13,'#9f2e2a','glazed');box(x+.18,1.15,z-.33,.12,.22,.12,'#d4bd78','glazed');
}
function lantern(x,y,z,scale=1,c='#ff703c'){
 const widths=[.3,.49,.6,.64,.6,.49,.3];
 widths.forEach((w,i)=>glowBox(x,y+(i-3)*.12*scale,z,w*scale,.115*scale,w*scale,c,1.65));
 for(let s of [-1,1]){box(x+s*.24*scale,y,z,.035*scale,.68*scale,.39*scale,'#d77a39');box(x,y,z+s*.24*scale,.39*scale,.68*scale,.035*scale,'#ce6a2f');}
 box(x,y+.46*scale,z,.3*scale,.1*scale,.3*scale,'#b99449','metal');box(x,y-.46*scale,z,.27*scale,.1*scale,.27*scale,'#a36c36');
 box(x,y-.66*scale,z,.06*scale,.36*scale,.06*scale,'#c44630');box(x,y+.7*scale,z,.028,.4*scale,.028,'#34443b');
}
function umbrella(x,y,z,r=1,c='#577e79'){
 box(x,y/2,z,.06,y,.06,'#aab4a1','metal');
 for(let dx=-5;dx<=5;dx++)for(let dz=-5;dz<=5;dz++){
  const rr=Math.max(Math.abs(dx),Math.abs(dz));if(dx*dx+dz*dz>30)continue;
  box(x+dx*r*.19,y+.28-rr*.11,z+dz*r*.19,r*.205,.14,r*.205,Math.abs(dx+dz)%4<2?c:'#bdaf8a','glazed');
 }
 box(x,y+.39,z,.14,.21,.14,'#b5a98c','metal');
}

function stall(x,z,r,label,roof,kind,index){
 const o={x,y:.16,z,r};const lb=(a,b,c,w,h,d,col,mat)=>localBox(o,a,b,c,w,h,d,col,mat);
 lb(0,.1,0,4.45,.2,2.85,'#304248');
 lb(0,1,-1.25,4.2,1.9,.13,'#45605e');
 for(let dx of [-2,2])for(let dz of [-1.23,1.23])lb(dx,1.6,dz,.12,3.2,.12,'#9b9d83','metal');
 lb(0,1.03,.65,4.1,.88,1.0,'#678b84');lb(0,1.52,.65,4.3,.14,1.13,'#c4bca2','metal');
 // Stepped corrugated awning with alternating fabric panels and scalloped fringe.
 for(let k=0;k<19;k++){
  const xx=-2.18+k*.24,shade=k%4<2?roof:'#b6ae91';
  for(let q=0;q<6;q++)lb(xx,3.22-q*.075,-1.35+q*.53,.235,.14,.56,shade,'glazed');
  lb(xx,2.69,1.43,.235,.24,.12,shade);
 }
 const co=Math.cos(r),si=Math.sin(r),toWorld=(xx,yy,zz)=>new THREE.Vector3(x+xx*co+zz*si,yy+.16,z-xx*si+zz*co);
 const board=toWorld(0,2.42,1.25);sign(label,board.x,board.y,board.z,3.25,.64,index%2?'#ffb36a':'#aad6bc',r);
 for(let dx of [-1.6,1.6]){const p=toWorld(dx,2.29,1.3);lantern(p.x,p.y,p.z,.6,index%3?'#ff7445':'#ffa25e');}
 lb(0,2.69,.15,3.5,.055,.09,'#ffe1a0','soft');
 for(let i=0;i<5;i++){lb(-1.6+i*.7,1.91,-1.17,.5,.055,.5,'#a89c7c');for(let j=0;j<3;j++)lb(-1.77+i*.7+j*.17,2.08,-1.14,.095,.28,.095,pick(['#d7aa62','#719f76','#b9533b']),'glazed');}
 lb(-1.34,1.66,.67,.52,.18,.44,'#323e42','metal');
 lb(-1.34,1.78,.67,.4,.06,.33,'#171d24','metal');
 const cooking=toWorld(-1.34,1.9,.67);steamEmitters.push({x:cooking.x,y:cooking.y,z:cooking.z,p:index});
 if(kind==='noodles'){
  lb(.15,1.8,.6,.73,.54,.73,'#929c91','metal');lb(.15,2.07,.6,.62,.045,.62,'#dcb37b');
  const p=toWorld(.15,2.16,.6);steamEmitters.push({x:p.x,y:p.y,z:p.z,p:index+2});
  for(let k=0;k<5;k++)lb(.15+range(-.24,.24),2.11,.6+range(-.23,.23),.13,.04,.14,'#ead5a0');
 }else if(kind==='grill'){
  lb(.28,1.7,.6,1.25,.18,.65,'#243134','metal');
  for(let k=0;k<8;k++){lb(-.2+k*.14,1.82,.6,.055,.045,.8,'#d3b580','metal');lb(-.2+k*.14,1.87,.6,.13,.12,.36,'#bd7848');}
  const p=toWorld(.3,1.75,.6);glowBox(p.x,p.y,p.z,.8,.03,.42,'#ff7435',2.4,r);steamEmitters.push({x:p.x,y:p.y+.3,z:p.z,p:index+4});
 }else{
  for(let k=0;k<3;k++)for(let j=0;j<3;j++)lb(.12+k*.24,1.7,.37+j*.24,.17,.17,.17,pick(['#d99958','#85a868','#db6453']),'glazed');
 }
 lb(1.45,1.68,.6,.3,.2,.31,'#ddd4b7','glazed');lb(1.6,1.9,.6,.03,.4,.03,'#e0b96c');
 const vendor=toWorld(0,0,-.15);makePerson(vendor.x,.15,vendor.z,r,'cook',index);
 const cr=toWorld(-2.7,0,.2);crate(cr.x,.07,cr.z,index%2?'#467379':'#b78b50');
 crate(cr.x,.46,cr.z,'#536e68',false);
 const pp=toWorld(2.4,0,-.9);potPlant(pp.x,.05,pp.z,.65);
}

// Articulated voxel residents. Parts share two instanced batches for the crowd.
const skins=['#c79975','#dfb590','#b48366','#e4bd98'];
const shirts=['#b9584c','#d3bb87','#448d8b','#6484a2','#af8977','#65716b','#b68b55','#c7cbb7'];
function makePerson(x,y,z,heading=0,behavior='idle',index=0){
 const parts=[],skin=pick(skins),shirt=behavior==='cook'?'#d6cfaf':pick(shirts),trousers=pick(['#273b4a','#3b444b','#4c4c45','#394f57']);
 const add=(x,y,z,w,h,d,c,joint='body')=>parts.push({x,y,z,w,h,d,c,joint});
 add(0,1.02,0,.43,.58,.29,shirt);add(0,1.42,.01,.34,.36,.33,skin);
 add(0,1.64,-.025,.36,.1,.36,'#273034');add(0,1.46,-.15,.36,.28,.07,'#253137');
 add(-.095,1.45,.181,.043,.038,.025,'#263136');add(.095,1.45,.181,.043,.038,.025,'#263136');
 add(0,1.36,.185,.085,.035,.03,'#9b6955');
 for(let side of [-1,1]){
  add(side*.125,.43,0,.16,.65,.19,trousers,side<0?'legL':'legR');
  add(side*.125,.1,.045,.2,.14,.31,'#1b2a34',side<0?'legL':'legR');
  add(side*.29,1.04,0,.14,.48,.16,shirt,side<0?'armL':'armR');
  add(side*.29,.76,.015,.135,.14,.14,skin,side<0?'armL':'armR');
 }
 if(behavior==='cook'){add(0,1.7,0,.4,.16,.36,'#f2e7cc');add(0,.92,.165,.33,.59,.04,'#e2d1ab');add(.29,.72,.37,.045,.045,.52,'#ae9b70','armR');}
 else if(behavior==='eat'){add(.29,1.12,.28,.25,.13,.25,'#d7c49b','armR');add(-.29,1.25,.32,.025,.025,.38,'#c5a773','armL');}
 else if(index%4===0){add(0,1.02,-.23,.34,.42,.22,pick(['#b68153','#8b5e60','#57746c']));}
 if(index%7===0&&behavior!=='cook'){
  add(0,1.67,0,.41,.12,.38,'#b2a37b');add(0,1.65,.2,.47,.055,.2,'#b2a37b');
 }
 if(behavior==='eat'){
  for(const p of parts){if(p.joint.startsWith('leg')){if(p.h>.2){p.h=.31;p.y=.35;p.z=.27;}else{p.y=.11;p.z=.33;}}else p.y-=.18;}
  for(let side of [-1,1])add(side*.125,.59,.12,.17,.18,.43,trousers);
 }
 const actor={x,y,z,heading,behavior,index,parts,phase:range(0,TAU),speed:range(.65,1.15),offset:random(),scale:range(.88,1.08),indices:[]};actors.push(actor);return actor;
}

stall(-7.6,-4.25,0,'潮汕牛肉面','#647e67','noodles',0);
stall(-2.5,-4.3,0,'烧烤','#ae6650','grill',1);
stall(2.65,-4.2,0,'糖水铺','#547e86','fruit',2);
stall(7.8,-4.1,0,'煲仔饭','#ba8d56','noodles',3);
stall(-9.65,1.3,Math.PI/2,'海鲜','#8e665a','grill',4);
stall(9.65,1.4,-Math.PI/2,'奶茶','#6b978a','fruit',5);
stall(-9.3,6.25,Math.PI/2,'肠粉','#bc8b59','noodles',6);
stall(9.1,6.4,-Math.PI/2,'小炒','#548b83','grill',7);
stall(-6.8,8.15,0,'生煎包','#a55f4d','fruit',8);
stall(6.7,8.15,0,'柠檬茶','#5c8c6c','fruit',9);

// Dining islands, bottles, bowls, improvised stools, and diners.
for(const [x,z,i] of [[-4.6,2.3,0],[4.7,2.5,1],[-4.3,5.6,2],[4.3,5.8,3]]){
 table(x,z,i%2);makePerson(x-1.12,.08,z,Math.PI/2,'eat',i+12);makePerson(x+1.12,.08,z,-Math.PI/2,'eat',i+18);
 if(i===1||i===2)umbrella(x,3.35,z,1.3,i===1?'#6b8f87':'#ab7456');
}
for(let i=0;i<20;i++)makePerson(0,.08,0,0,'walk',i+24);
for(const [x,z,h] of [[-7,-1.9,Math.PI],[-2.7,-1.9,Math.PI],[2.5,-1.7,Math.PI],[7.8,-1.6,Math.PI],[-7,4,Math.PI/2],[6.8,4,-Math.PI/2],[-5.7,9.8,Math.PI],[5.8,9.8,Math.PI],[-1.2,8.5,1],[1.5,3.8,-1]])makePerson(x,.08,z,h,'talk',actors.length);

// Gate and hanging lanterns. Each sagging wire is a chain of discrete cubes.
for(let x of [-3.5,3.5]){box(x,2.7,-6.5,.19,5.4,.19,'#396365','metal');box(x,.28,-6.5,.51,.55,.5,'#76847b');}
box(0,5.3,-6.5,7.8,.17,.23,'#a98358','metal');sign('深圳夜市',0,5.91,-6.47,7.7,1.23,'#ffb974');
for(let x of [-3.6,3.6])lantern(x,4.8,-6.5,1.05,'#ff6b39');
for(let row=0;row<4;row++){
 const z=-1+row*3.6,y=6.8+Math.sin(row)*.4;
 wire(new THREE.Vector3(-11,y,z),new THREE.Vector3(11,y+.4,z-.6),1.35);
 for(let k=0;k<9;k++){const t=(k+.5)/9;const xx=-11+t*22,yy=y+.4*t-Math.sin(t*Math.PI)*1.35;lantern(xx,yy-.62,z-t*.6,.78,k%4===0?'#ffc16c':'#ff693c');}
}
for(let i=0;i<7;i++)wire(new THREE.Vector3(-14,9+range(0,2),range(-4,1)),new THREE.Vector3(14,10+range(0,2),range(-3,3)),range(1.4,3),'#172a30',.045);
for(let x of [-16,16]){
 box(x,4.8,7,.12,9.5,.12,'#4c6468','metal');
 for(let z=-6;z<10;z+=1.7)box(x,7,z,.045,.045,.045,'#46676e');
 wire(new THREE.Vector3(x,9.4,7),new THREE.Vector3(x,12,-10),1.1,'#243b43');
}

// Details to discover: crates, bins, delivery parcels, plants and a sleeping cat.
for(let i=0;i<13;i++){
 const side=i%2?1:-1,x=side*range(12.2,16.3),z=range(5,10);
 crate(x,.08,z,pick(['#6b8b7b','#956e48','#587e8e']),i%3===0);
 if(i%3===1)crate(x,.47,z,'#8c7756',false);
}
for(let side of [-1,1]){
 box(side*15.4,.61,10,1.1,1.15,.9,'#3b6c64');box(side*15.4,1.22,10,1.22,.12,1,'#527d70');
 for(let j=0;j<3;j++)box(side*15.4+range(-.4,.4),.38,11.1+j*.44,.55,.7,.5,'#ae9065');
 potPlant(side*16.6,.07,5.4,1.2);potPlant(side*12.3,.07,8,1);
}
box(-13.9,.34,9.5,.74,.33,.42,'#d5ad7b');box(-13.49,.54,9.5,.31,.3,.31,'#d5ad7b');
box(-13.49,.72,9.4,.1,.17,.1,'#b58864');box(-13.49,.72,9.62,.1,.17,.1,'#b58864');
box(-14.37,.4,9.5,.38,.1,.1,'#c3956d');
for(let i=0;i<7;i++){const x=range(-15,15),z=range(10.2,14);box(x,.075,z,.15,.025,.23,'#afad92','stone',range(0,TAU));}
// Bright refrigerator behind the tea stall, with voxel bottles on four shelves.
box(11.2,1.4,5.4,.8,2.7,1.3,'#c4c5ad','metal');box(10.75,1.47,5.4,.06,2.4,1.1,'#416a6b','glazed');
for(let row=0;row<4;row++)for(let col=0;col<5;col++)glowBox(10.7,.55+row*.52,5+col*.2,.07,.3,.12,pick(['#ddaa6d','#8cc9a6','#d88875']),.65);
glowBox(10.66,2.65,5.4,.08,.06,1.1,'#b7e4d5',2);

function scooter(index){
 const parts=[],paint=['#c26e54','#4d9a98','#c9b27a'][index];
 const add=(x,y,z,w,h,d,c,emissive=false)=>parts.push({x,y,z,w,h,d,c,emissive});
 for(let zz of [-.62,.62])for(let k=0;k<12;k++){
  const a=k/12*TAU;add(0,.29+Math.sin(a)*.22,zz+Math.cos(a)*.22,.19,.13,.13,'#182832');
 }
 add(0,.4,0,.35,.18,1.2,paint);add(0,.62,-.4,.48,.4,.48,paint);
 add(0,.86,-.36,.52,.13,.68,'#253337');add(0,.87,.52,.32,.75,.2,paint);
 add(0,1.16,.48,.76,.07,.11,'#a6b6aa');add(0,1.05,.65,.21,.16,.08,'#ffdfa1',true);
 add(0,.68,-.7,.25,.1,.06,'#ff7048',true);add(0,.59,.1,.24,.25,.32,'#3e4d54');
 add(0,1.26,-.18,.42,.59,.29,index===0?'#d29448':'#658e86');
 add(0,1.7,-.08,.4,.4,.4,'#c4a88b');add(0,1.86,-.09,.45,.17,.45,index===1?'#dbc38d':'#576e77');
 add(0,1.72,.14,.37,.14,.04,'#354e55');
 for(let side of [-1,1]){add(side*.25,1.2,.09,.14,.17,.51,'#be9b7f');add(side*.22,.76,-.03,.17,.34,.42,'#2f424e');add(side*.23,.55,.19,.19,.12,.32,'#2c373e');}
 if(index===0){add(0,1.11,-.78,.7,.58,.58,'#d3a344');add(0,1.12,-1.08,.36,.25,.03,'#d8d2aa');}
 scooters.push({parts,index,indices:[],offset:index/3});
}
for(let i=0;i<3;i++)scooter(i);

// Build one instanced draw per material, rather than one object per voxel.
const staticMeshes={};
for(const [name,list] of Object.entries(batches)){
 if(!list.length)continue;
 const mesh=new THREE.InstancedMesh(cube,mats[name],list.length);
 list.forEach((b,i)=>{dummy.position.set(b.x,b.y,b.z);dummy.rotation.set(0,b.ry,0);dummy.scale.set(b.w,b.h,b.d);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);mesh.setColorAt(i,b.c instanceof THREE.Color?b.c:color.set(b.c));});
 mesh.castShadow=name==='stone'||name==='metal';mesh.receiveShadow=name!=='glow';mesh.computeBoundingSphere();scene.add(mesh);staticMeshes[name]=mesh;
}
const dynParts=actors.reduce((n,a)=>n+a.parts.length,0)+scooters.reduce((n,s)=>n+s.parts.filter(p=>!p.emissive).length,0);
const crowd=new THREE.InstancedMesh(cube,mats.stone,dynParts);crowd.instanceMatrix.setUsage(THREE.DynamicDrawUsage);crowd.frustumCulled=false;crowd.receiveShadow=true;scene.add(crowd);
const lamps=new THREE.InstancedMesh(cube,mats.glow,6);lamps.instanceMatrix.setUsage(THREE.DynamicDrawUsage);lamps.frustumCulled=false;scene.add(lamps);
const shadows=new THREE.InstancedMesh(cube,new THREE.MeshBasicMaterial({color:'#071b24',transparent:true,opacity:.23,depthWrite:false}),actors.length+3);shadows.frustumCulled=false;scene.add(shadows);
let partIndex=0,lampIndex=0;
for(const a of actors)for(const p of a.parts){a.indices.push(partIndex);crowd.setColorAt(partIndex++,color.set(p.c));}
for(const s of scooters)for(const p of s.parts){if(p.emissive){p.slot=lampIndex++;lamps.setColorAt(p.slot,color.set(p.c).multiplyScalar(3));}else{p.slot=partIndex++;crowd.setColorAt(p.slot,color.set(p.c));}}
const steamCount=steamEmitters.length*15;
const steam=new THREE.InstancedMesh(cube,new THREE.MeshBasicMaterial({color:'#c9cbbf',transparent:true,opacity:.105,depthWrite:false}),steamCount);steam.frustumCulled=false;scene.add(steam);
const steamSeeds=Array.from({length:steamCount},()=>({phase:random(),dx:range(-.25,.25),dz:range(-.25,.25),speed:range(.14,.24),size:range(.15,.29)}));
const rainCount=330;
const rain=new THREE.InstancedMesh(cube,new THREE.MeshBasicMaterial({color:'#9cbac8',transparent:true,opacity:.16,depthWrite:false}),rainCount);rain.frustumCulled=false;scene.add(rain);
const rainSeeds=Array.from({length:rainCount},()=>({x:range(-18,18),z:range(-15,15),phase:random(),speed:range(.2,.35)}));
const tempMatrix=new THREE.Matrix4(),worldMatrix=new THREE.Matrix4(),zero=new THREE.Vector3(),one=new THREE.Vector3(1,1,1),q=new THREE.Quaternion(),axis=new THREE.Vector3(0,1,0);
function actorMatrix(x,y,z,heading,scale=1){q.setFromAxisAngle(axis,heading);zero.set(x,y,z);one.setScalar(scale);worldMatrix.compose(zero,q,one);}
function dynamicBox(mesh,slot,p,x=p.x,y=p.y,z=p.z,rx=0){dummy.position.set(x,y,z);dummy.scale.set(p.w,p.h,p.d);dummy.rotation.set(rx,0,0);dummy.updateMatrix();tempMatrix.multiplyMatrices(worldMatrix,dummy.matrix);mesh.setMatrixAt(slot,tempMatrix);}
const route=new THREE.CatmullRomCurve3([new THREE.Vector3(-2.4,0,8.7),new THREE.Vector3(-2.7,0,3.6),new THREE.Vector3(-3.3,0,-1.1),new THREE.Vector3(0,0,-1.9),new THREE.Vector3(3.15,0,-.7),new THREE.Vector3(2.45,0,4),new THREE.Vector3(2.15,0,9.2),new THREE.Vector3(0,0,10)],true,'catmullrom',.35);
const pos=new THREE.Vector3(),tangent=new THREE.Vector3();
function animateWorld(t){
 let shadowIndex=0;
 for(const a of actors){
  let x=a.x,z=a.z,heading=a.heading;
  const walking=a.behavior==='walk',cycle=t*a.speed*5+a.phase;
  if(walking){const u=(a.offset+t*a.speed/62)%1;route.getPointAt(u,pos);route.getTangentAt(u,tangent);x=pos.x+(a.index%3-1)*.4;z=pos.z;heading=Math.atan2(tangent.x,tangent.z);}
  const bob=walking?Math.abs(Math.sin(cycle))*.035:Math.sin(t*1.1+a.phase)*.012;
  actorMatrix(x,a.y+bob,z,heading,a.scale);
  a.parts.forEach((p,i)=>{
   let yy=p.y,zz=p.z,rx=0;
   if(walking){const side=p.joint.endsWith('L')?1:-1;if(p.joint.startsWith('leg')){rx=Math.sin(cycle)*.39*side;zz+=Math.sin(cycle)*.15*side;yy+=Math.max(0,Math.sin(cycle)*side)*.065;}else if(p.joint.startsWith('arm')){rx=-Math.sin(cycle)*.33*side;zz-=Math.sin(cycle)*.12*side;}}
   else if(a.behavior==='cook'&&p.joint==='armR'){zz+=.19+Math.sin(t*2.4+a.phase)*.14;yy+=.15;rx=-.6;}
   else if(a.behavior==='eat'&&p.joint.startsWith('arm')){zz+=.19;yy+=.13+Math.sin(t*1.7+a.phase)*.06;rx=-.8;}
   else if(a.behavior==='talk'&&p.joint==='armR'){rx=-.35-Math.sin(t*1.3+a.phase)*.28;zz+=.14;}
   dynamicBox(crowd,a.indices[i],p,p.x,yy,zz,rx);
  });
  actorMatrix(x,.073,z,heading);dynamicBox(shadows,shadowIndex++,{x:0,y:0,z:0,w:.73,h:.012,d:.54});
 }
 for(const s of scooters){
  const a=t*.095+s.offset*TAU,xx=Math.sin(a)*14.4,zz=11.55+Math.cos(a)*1.32,heading=Math.atan2(Math.cos(a)*14.4,-Math.sin(a)*1.32);
  actorMatrix(xx,.06,zz,heading);
  for(const p of s.parts)dynamicBox(p.emissive?lamps:crowd,p.slot,p);
  actorMatrix(xx,.078,zz,heading);dynamicBox(shadows,shadowIndex++,{x:0,y:0,z:0,w:.7,h:.014,d:1.9});
 }
 crowd.instanceMatrix.needsUpdate=true;lamps.instanceMatrix.needsUpdate=true;shadows.instanceMatrix.needsUpdate=true;
 for(let i=0;i<steamCount;i++){
  const e=steamEmitters[Math.floor(i/15)],s=steamSeeds[i],f=(s.phase+t*s.speed)%1;
  const size=s.size*(.35+Math.sin(f*Math.PI)*1.65);
  dummy.position.set(e.x+s.dx+Math.sin(t*.55+f*5+e.p)*f*.42,e.y+f*3.0,e.z+s.dz+Math.cos(t*.47+f*4)*f*.3);
  dummy.scale.setScalar(size);dummy.rotation.set(0,0,0);dummy.updateMatrix();steam.setMatrixAt(i,dummy.matrix);
 }steam.instanceMatrix.needsUpdate=true;
 for(let i=0;i<rainCount;i++){
  const s=rainSeeds[i],f=(s.phase+t*s.speed)%1;
  dummy.position.set(s.x+f*.65,.15+(1-f)*25,s.z+f*.4);dummy.scale.set(.017,.12,.017);dummy.updateMatrix();rain.setMatrixAt(i,dummy.matrix);
 }rain.instanceMatrix.needsUpdate=true;
 staticMeshes.glow.material.color.setScalar(.96+.035*Math.sin(t*9)+.015*Math.sin(t*27));
 glowSources[3].intensity=38+Math.sin(t*7)*2;
 water.material.uniforms.time.value=t;
}

const composer=new EffectComposer(renderer);
composer.addPass(new RenderPass(scene,camera));
const bloom=new UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),.48,.38,1.15);composer.addPass(bloom);composer.addPass(new OutputPass());
const cinemaPath=new THREE.CatmullRomCurve3([
 new THREE.Vector3(38,28,44),new THREE.Vector3(27,18,25),
 new THREE.Vector3(0,4.3,9.8),new THREE.Vector3(-13,14,30),
 new THREE.Vector3(-31,23,31),new THREE.Vector3(-9,31,49)
],true,'catmullrom',.45);
const lookPath=new THREE.CatmullRomCurve3([
 new THREE.Vector3(0,7,-1),new THREE.Vector3(1,5,0),
 new THREE.Vector3(0,2.7,-2),new THREE.Vector3(-1,5,-1),
 new THREE.Vector3(0,6,-1),new THREE.Vector3(0,7,-1)
],true,'catmullrom',.35);
let cinematic=true,paused=false,time=0,last=performance.now(),transition=0;
const targetPos=new THREE.Vector3(),targetLook=new THREE.Vector3(),previousPos=new THREE.Vector3(),previousLook=new THREE.Vector3(),viewLook=new THREE.Vector3();
function cameraAt(t,position,look){
 const u=((t%30)+30)%30/30;cinemaPath.getPoint(u,position);lookPath.getPoint(u,look);
 const fit=Math.max(1,1.3/camera.aspect);position.sub(look).multiplyScalar(fit).add(look);
}
cameraAt(0,camera.position,viewLook);camera.lookAt(viewLook);
const hud=document.getElementById('orbit');
function toggleCamera(){
 cinematic=!cinematic;controls.enabled=!cinematic;hud.hidden=cinematic;
 if(!cinematic){controls.target.copy(viewLook);controls.update();}
 else {previousPos.copy(camera.position);previousLook.copy(controls.target);transition=1.3;}
 canvas.dataset.mode=cinematic?'cinematic':'orbit';
}
document.addEventListener('keydown',e=>{
 if(e.repeat)return;
 if(e.code==='KeyC'){e.preventDefault();toggleCamera();}
 if(e.code==='Space'){e.preventDefault();paused=!paused;document.getElementById('motion').textContent=paused?'TIME PAUSED':'LIVING DIORAMA';}
 if(e.code==='KeyF'){if(!document.fullscreenElement)document.documentElement.requestFullscreen().catch(()=>{});else document.exitFullscreen().catch(()=>{});}
});
document.addEventListener('visibilitychange',()=>{last=performance.now();});
function resize(){
 camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);
 bloom.setSize(innerWidth*renderer.getPixelRatio()*.7,innerHeight*renderer.getPixelRatio()*.7);
}window.addEventListener('resize',resize);resize();
let frames=0,measureTime=0,cpuSum=0,frameSum=0,frameCount=0;
canvas.dataset.mode='cinematic';canvas.dataset.voxels=String(totalBoxes+dynParts+steamCount+rainCount);
canvas.dataset.geometry='BoxGeometry only';
const qa=new URLSearchParams(location.search);const seek=qa.has('time')?Number(qa.get('time')):null;
if(seek!==null&&Number.isFinite(seek))time=seek;
if(qa.get('still')==='1')paused=true;
animateWorld(time);renderer.shadowMap.needsUpdate=true;
function frame(now){
 const dt=Math.min((now-last)/1000,.15);last=now;const begin=performance.now();
 if(!paused&&!document.hidden)time+=dt;
 animateWorld(time);
 if(cinematic){cameraAt(time,targetPos,targetLook);
  if(transition>0){transition=Math.max(0,transition-dt);let a=1-transition/1.3;a=a*a*(3-2*a);camera.position.lerpVectors(previousPos,targetPos,a);viewLook.lerpVectors(previousLook,targetLook,a);}
  else{camera.position.copy(targetPos);viewLook.copy(targetLook);}
  camera.lookAt(viewLook);
 }else{controls.update();viewLook.copy(controls.target);}
 renderer.info.autoReset=false;renderer.info.reset();composer.render();
 cpuSum+=performance.now()-begin;frameSum+=dt;frameCount++;measureTime+=dt;frames++;
 if(measureTime>=1){
  canvas.dataset.phase=(time%30).toFixed(3);canvas.dataset.elapsed=time.toFixed(3);
  canvas.dataset.fps=(frameCount/frameSum).toFixed(1);canvas.dataset.cpuMs=(cpuSum/frameCount).toFixed(2);
  canvas.dataset.calls=String(renderer.info.render.calls);canvas.dataset.triangles=String(renderer.info.render.triangles);
  canvas.dataset.camera=camera.position.toArray().map(n=>n.toFixed(2)).join(',');
  canvas.dataset.paused=String(paused);measureTime=0;cpuSum=0;frameSum=0;frameCount=0;
 }
 requestAnimationFrame(frame);
}
document.getElementById('loading').remove();document.body.classList.add('ready');requestAnimationFrame(frame);
// Testable invariants for the closed curve, without exposing scene internals.
const seamPosA=new THREE.Vector3(),seamPosB=new THREE.Vector3(),seamLookA=new THREE.Vector3(),seamLookB=new THREE.Vector3();
cameraAt(0,seamPosA,seamLookA);cameraAt(30,seamPosB,seamLookB);
canvas.dataset.seamError=String(seamPosA.distanceTo(seamPosB)+seamLookA.distanceTo(seamLookB));
