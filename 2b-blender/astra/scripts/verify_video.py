"""Decode every final frame and make a contact sheet for visual quality review.
Requires Pillow and imageio-ffmpeg (verification only; Blender renders without them).
"""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageStat,ImageChops
import imageio_ffmpeg
root=Path(__file__).resolve().parent.parent
reader=imageio_ffmpeg.read_frames(str(root/'render/flythrough.mp4'),pix_fmt='rgb24')
meta=next(reader);assert tuple(meta['size'])==(1920,1080)
assert abs(meta['fps']-24)<.001
sheet=Image.new('RGB',(1920,900),'#08151c');draw=ImageDraw.Draw(sheet)
try:font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
except OSError:font=ImageFont.load_default()
selected=set([1,22,43,64,85,106,127,148,169,190,211,240])
count=0;prev=None;means=[];changes=[];slot=0
for raw in reader:
    count+=1;im=Image.frombytes('RGB',meta['size'],raw);thumb=im.resize((96,54))
    means.append(sum(ImageStat.Stat(thumb).mean)/3)
    if prev is not None:changes.append(sum(ImageStat.Stat(ImageChops.difference(thumb,prev)).mean)/3)
    prev=thumb
    if count in selected:
        x=(slot%4)*480;y=(slot//4)*300
        sheet.paste(im.resize((480,270),Image.Resampling.LANCZOS),(x,y))
        draw.text((x+12,y+276),f'FRAME {count:03d}  /  {(count-1)/24:.2f} s',font=font,fill='#d7c3a6');slot+=1
assert count==240,count
assert min(means)>3,'Unexpected black frame'
sheet.save(root/'render/tests/final_contact_sheet.png')
digest=hashlib.sha256((root.parent/'index.html').read_bytes()).hexdigest().upper()
assert digest=='0CE231279BB9B11A27C1CE0AE6D446A0E7C8AD2D4216F2918B0721AA4CC718FC'
report={'decoded_frames':count,'fps':meta['fps'],'size':meta['size'],'duration_seconds':count/meta['fps'],'codec':meta.get('codec',meta.get('video_codec','unknown')),'minimum_frame_mean_luma':round(min(means),2),'max_adjacent_frame_mean_difference':round(max(changes),2),'browser_index_unchanged':True,'browser_sha256':digest,'ffmpeg_metadata':meta}
(root/'render/video_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

