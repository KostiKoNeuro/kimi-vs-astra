import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, '../..');
const outputDir = path.resolve(scriptDir, '../source');
const workDir = path.resolve(scriptDir, '../work');
fs.mkdirSync(outputDir, { recursive: true });
fs.mkdirSync(workDir, { recursive: true });
const original = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const sourceHash = crypto.createHash('sha256').update(original).digest('hex');

function functionRange(source, name) {
  const start = source.indexOf(`function ${name}(`);
  if (start < 0) throw new Error(`Cannot find ${name}`);
  let cursor = start;
  let depth = 0;
  let quote = null;
  while (cursor < source.length) {
    const c = source[cursor];
    if (quote) {
      if (c === '\\') cursor++;
      else if (c === quote) quote = null;
    } else if (c === "'" || c === '"' || c === '`') quote = c;
    else if (c === '(') depth++;
    else if (c === ')') {
      depth--;
      if (depth === 0) break;
    }
    cursor++;
  }
  const open = source.indexOf('{', cursor);
  depth = 1;
  cursor = open + 1;
  quote = null;
  while (cursor < source.length && depth) {
    const c = source[cursor];
    const next = source[cursor + 1];
    if (quote) {
      if (c === '\\') cursor++;
      else if (c === quote) quote = null;
    } else if (c === "'" || c === '"' || c === '`') quote = c;
    else if (c === '/' && next === '/') {
      cursor = source.indexOf('\n', cursor + 2);
      if (cursor < 0) throw new Error('Unterminated comment');
    } else if (c === '/' && next === '*') cursor = source.indexOf('*/', cursor + 2) + 1;
    else if (c === '{') depth++;
    else if (c === '}') depth--;
    cursor++;
  }
  return { open, close: cursor - 1 };
}

function wrapFunction(source, name, section, assembly = null) {
  const { open, close } = functionRange(source, name);
  let prefix = `\n      const __previousSection = currentSection;\n      currentSection = ${JSON.stringify(section)};\n`;
  let suffix = '\n    } finally { currentSection = __previousSection; ';
  if (assembly) {
    prefix += `      const __previousAssembly = currentAssembly;\n      currentAssembly = ${assembly};\n`;
    suffix += 'currentAssembly = __previousAssembly; ';
  }
  if (name === 'lantern') prefix += '      lanternPlacements.push({ x, y, z, scale });\n';
  prefix += '      try {';
  suffix += '}';
  return source.slice(0, open + 1) + prefix + source.slice(open + 1, close) + suffix + source.slice(close);
}

let instrumented = original;
instrumented = instrumented.replace(
  '      const buckets = new Map();',
  "      let currentSection = '03 | Market & street details';\n      let currentAssembly = 'Street furniture & details';\n      let buildingCount = 0;\n      const lanternPlacements = [];\n      const buckets = new Map();"
);
instrumented = instrumented.replace(
  '{ x, y, z, sx, sy, sz, tint, rotation }',
  '{ x, y, z, sx, sy, sz, tint, rotation, section: currentSection, assembly: currentAssembly }'
);
instrumented = instrumented.replace(
  '      box(0, -0.64, 0,',
  "      currentSection = '01 | Foundation & wet streets';\n      currentAssembly = 'Floating city block & paving';\n      box(0, -0.64, 0,"
);
instrumented = instrumented.replace(
  '      for (const side of [-1, 1]) {\n        const x = side * 12.25, z = 7.0;',
  "      currentSection = '05 | Lanterns & overhead wires';\n      currentAssembly = 'Cables, utility poles & lantern strings';\n      for (const side of [-1, 1]) {\n        const x = side * 12.25, z = 7.0;"
);
for (const [name, section, assembly] of [
  ['building', '02 | Towers & shophouses', "'Building ' + String(++buildingCount).padStart(2, '0')"],
  ['sign', '04 | Pixel neon & wayfinding', null],
  ['verticalSign', '04 | Pixel neon & wayfinding', null],
  ['lantern', '05 | Lanterns & overhead wires', null],
  ['stall', '03 | Market & street details', "'Stall ' + String(index + 1).padStart(2, '0') + ' - ' + style.name"],
  ['diningTable', '03 | Market & street details', "'Outdoor dining'"]
]) instrumented = wrapFunction(instrumented, name, section, assembly);

const exportCode = `
      window.__exportMarket = () => {
        const round = value => Number(value.toFixed(6));
        const vector = value => value.toArray().map(round);
        const rotation = value => [value.x, value.y, value.z].map(round);
        const staticBatches = [...buckets.entries()].map(([kind, items]) => ({
          kind,
          items: items.map(item => ({
            p: [item.x, item.y, item.z].map(round),
            s: [item.sx, item.sy, item.sz].map(round),
            r: (item.rotation || [0, 0, 0]).map(round),
            c: vector(color(item.tint)),
            section: item.section,
            assembly: item.assembly
          }))
        }));
        const rigs = actors.map(actor => ({
          name: actor.name,
          parts: actor.parts.map(part => ({
            p: [part.x, part.y, part.z].map(round), s: [part.sx, part.sy, part.sz].map(round),
            r: part.rotation.map(round), c: part.tint.toArray().map(round), kind: part.kind
          }))
        }));
        const frames = [];
        const flickerFrames = [];
        for (let frame = 0; frame < 240; frame++) {
          const time = frame / 24;
          updateLife(time);
          frames.push(actors.map(actor => ({
            root: { p: vector(actor.group.position), r: rotation(actor.group.rotation), s: vector(actor.group.scale) },
            parts: actor.parts.map(part => ({ p: [part.x, part.y, part.z].map(round), r: part.rotation.map(round) }))
          })));
          flickerFrames.push(flickers.map(flicker => round(flicker.material.color.r / flicker.base.r)));
        }
        const lights = scene.children.filter(object => object.isPointLight).map(light => ({
          p: vector(light.position), c: vector(light.color), intensity: light.intensity, distance: light.distance
        }));
        return {
          metadata: {
            title: 'Shenzhen · After the Rain', seed: 48271, sourceSha256: ${JSON.stringify(sourceHash)},
            source: 'index.html', transfer: 'Unmodified browser generator, instrumented in memory; exact voxel transforms and per-frame actor poses',
            explicitConstraints: ['Same market layout and voxel construction', '240 frames at 24 fps and 1920 × 1080', 'One camera named FlyCam', 'No downloaded assets'],
            inferredDetails: ['Eevee production lighting and procedural wet materials', 'Ten-second entrance-to-aisle camera move', 'Extra local lantern lights, fine rain, and atmospheric scattering'],
            fps: 24, frameCount: 240, staticVoxels: staticVoxelCount, dynamicVoxels: dynamicVoxelCount,
            compareTime: 3.0, compareCamera: cameraAt(3.0)
          },
          staticBatches, rigs, frames, flickerFrames, lights, lanternPlacements,
          steamParticles: steamParticles.map(particle => ({
            source: vector(particle.source), phase: particle.phase, sway: particle.sway,
            seed: particle.seed, smoke: particle.smoke, speed: particle.speed
          })),
          drips,
          obstacles: obstacles.map(box => ({ min: vector(box.min), max: vector(box.max) })),
          paths: {
            walkers: Array.from({ length: 241 }, (_, i) => vector(walkingPath.getPointAt(i / 240))),
            scooters: Array.from({ length: 241 }, (_, i) => vector(scooterPath.getPointAt(i / 240)))
          }
        };
      };
`;
const marker = '      window.__market = Object.freeze({';
if (!instrumented.includes(marker)) throw new Error('Cannot find export insertion point');
instrumented = instrumented.replace(marker, exportCode + marker);
fs.writeFileSync(path.join(workDir, 'instrumented_source.html'), instrumented);

const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url.startsWith('/index.html')) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(instrumented);
  } else {
    res.writeHead(404);
    res.end();
  }
});
await new Promise(resolve => server.listen(8091, '127.0.0.1', resolve));
const chrome = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const child = spawn(chrome, [
  '--headless=new', '--no-sandbox', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=9225',
  '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check', '--ignore-certificate-errors',
  '--disable-dev-shm-usage', '--enable-unsafe-swiftshader', `--user-data-dir=${path.join(workDir, 'browser-profile')}`,
  '--window-size=1920,1080', '--hide-scrollbars', '--force-device-scale-factor=1', 'about:blank'
], { cwd: root, windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] });
let browserLog = '';
child.stderr.on('data', data => { browserLog += data.toString(); });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
try {
  let targets;
  for (let i = 0; i < 100; i++) {
    try {
      targets = await fetch('http://127.0.0.1:9225/json/list').then(response => response.json());
      if (targets.some(target => target.type === 'page')) break;
    } catch {}
    await delay(150);
  }
  const target = targets?.find(item => item.type === 'page');
  if (!target) throw new Error('Chrome debugging target unavailable');
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  let nextId = 0;
  const pending = new Map();
  const errors = [];
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const request = pending.get(message.id);
      if (request) {
        pending.delete(message.id);
        if (message.error) request.reject(new Error(JSON.stringify(message.error)));
        else request.resolve(message.result);
      }
    } else if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
  });
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const response = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
    return response.result.value;
  };
  await call('Page.enable');
  await call('Runtime.enable');
  await call('Emulation.setDeviceMetricsOverride', { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
  await call('Page.navigate', { url: 'http://127.0.0.1:8091/' });
  let ready = false;
  for (let i = 0; i < 240; i++) {
    ready = await evaluate('Boolean(window.__market?.ready && window.__exportMarket)');
    if (ready) break;
    await delay(250);
  }
  if (!ready) throw new Error(`Browser did not become ready: ${JSON.stringify(errors)}`);
  console.log('Exporting exact static geometry and 240 frames of original actor animation...');
  const json = await evaluate('JSON.stringify(window.__exportMarket())');
  const data = JSON.parse(json);
  data.metadata.sourceBytes = Buffer.byteLength(original);
  fs.writeFileSync(path.join(outputDir, 'market.json'), json);
  await evaluate('window.__market.seek(3.0)');
  await delay(500);
  const capture = await call('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
  fs.writeFileSync(path.join(workDir, 'browser_compare.png'), Buffer.from(capture.data, 'base64'));
  console.log(JSON.stringify({ ...data.metadata, rigs: data.rigs.length, lights: data.lights.length, lanterns: data.lanternPlacements.length, errors }, null, 2));
  fs.writeFileSync(path.join(workDir, 'export_browser.log'), browserLog + '\n' + JSON.stringify(errors, null, 2));
  if (errors.length) throw new Error('The browser reported runtime errors');
} finally {
  socket?.close();
  child.kill();
  server.close();
}
