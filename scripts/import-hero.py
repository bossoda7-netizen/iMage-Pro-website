"""Import four languages / two appearances without cropping window shadows."""
from pathlib import Path
from PIL import Image
import json,argparse
W=Path(__file__).resolve().parents[1];O=W/'public/assets/product';O.mkdir(parents=True,exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('source',type=Path);S=a.parse_args().source
names={'zh':'中文','en':'英语','ja':'日语','ko':'韩语'};items=[]
for lang,prefix in names.items():
 for theme,suffix in [('light','白'),('dark','黑')]:
  p=S/(prefix+suffix+'.png');im=Image.open(p).convert('RGBA');items.append((lang,theme,p,im))
if len({im.size for _,_,_,im in items})!=1:raise ValueError('Hero screenshots must share dimensions')
# Low-alpha pixels are the supplied window shadow, not disposable empty margins.
# Retain the full source canvas so every language / appearance keeps its soft edge.
bbox=(0,0,*items[0][3].size)
manifest={'source':S.name,'sharedCrop':bbox,'shadowPreserved':True,'images':{}}
for lang,theme,p,im in items:
 cropped=im.crop(bbox);name=f'app-{lang}-{theme}';cropped.save(O/(name+'.webp'),quality=94)
 manifest['images'][name]={'source':p.name,'size':list(cropped.size)}
(W/'content/hero-layout.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False,indent=2))
