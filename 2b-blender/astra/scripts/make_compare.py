"""Assemble matching full-frame views without cropping, stretching, or retouching either."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
root=Path(__file__).resolve().parent.parent
browser=Image.open(root/'scripts/browser_reference.png').convert('RGB')
blender=Image.open(root/'scripts/blender_reference.png').convert('RGB')
assert browser.size==blender.size==(1920,1080)
out=Image.new('RGB',(1920,1080),'#08151c');d=ImageDraw.Draw(out)
def font(size,bold=False):
    candidates=[Path('C:/Windows/Fonts/seguisb.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    for p in candidates:
        if p.exists():return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)
d.text((56,62),'SHENZHEN  /  AFTER RAIN',font=font(40,True),fill='#e0c6a2')
d.text((56,121),'The same procedural city. A cinematic interpretation.',font=font(22),fill='#8fa6ae')
for x,img,title,subtitle in [(0,browser,'01   BROWSER ORIGINAL','Three.js · original materials and lighting'),(960,blender,'02   BLENDER CINEMATIC','EEVEE · practical lighting, volumes and wet stone')]:
    out.paste(img.resize((960,540),Image.Resampling.LANCZOS),(x,252))
    d.text((x+56,831),title,font=font(26,True),fill='#e5cfb1')
    d.text((x+56,876),subtitle,font=font(20),fill='#98b2b9')
d.line((960,222,960,929),fill='#23404a',width=2)
d.line((56,969,1864,969),fill='#23404a',width=1)
d.text((56,994),'MATCHED CAMERA  ·  position (38, 28, 44)  ·  target (0, 7, -1)  ·  vertical FOV 42°  ·  time 0.000 s',font=font(18),fill='#76949e')
out.save(root/'render/compare.png')
(root/'render/comparison_metadata.json').write_text(json.dumps({'source':'unchanged Part 1 index.html','source_time_seconds':0,'source_position':[38,28,44],'source_target':[0,7,-1],'blender_position':[38,-44,28],'blender_target':[0,1,7],'vertical_fov_degrees':42,'input_resolution':[1920,1080],'output_resolution':[1920,1080],'layout':'full images reduced equally to 960x540; no crop or viewpoint alteration'},indent=2))
print('Saved render/compare.png')

