"""Convert mobile poster fallbacks to pixel-exact lossless WebP."""
from pathlib import Path
from PIL import Image, ImageChops
import shutil
W=Path(__file__).resolve().parents[1]
source=W/'public/assets/3d'
backup=W.parent.parent/'iMage Pro 官网筹备/制作备份/原始静态海报'
before=after=count=0
for p in sorted(source.glob('*/*-poster*.png')):
 if p.name.startswith('.'):continue
 im=Image.open(p).convert('RGBA');out=p.with_suffix('.webp')
 im.save(out,lossless=True,quality=75,method=4,exact=True)
 decoded=Image.open(out).convert('RGBA')
 if im.tobytes()!=decoded.tobytes():
  raise RuntimeError('Poster pixels changed: '+str(p))
 before+=p.stat().st_size;after+=out.stat().st_size;count+=1
 dest=backup/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.move(str(p),str(dest))
print('Pixel-exact posters:',count,'bytes:',before,'→',after)
