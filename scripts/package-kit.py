"""Package the reviewed source and public assets outside the app repository."""
from pathlib import Path
import zipfile,os
W=Path(__file__).resolve().parents[1];E=W.parent.parent/'iMage Pro 官网筹备';E.mkdir(exist_ok=True)
target=E/'iMage-Pro-官网素材.zip';temporary=E/'iMage-Pro-官网素材.next.zip'
with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(W.rglob('*')):
  rel=p.relative_to(W)
  if not p.is_file() or any(a.startswith('.') or a=='__pycache__' for a in rel.parts) or p.suffix=='.blend1' or p.name.startswith('_appearance'):continue
  z.write(p,Path('website')/rel)
with zipfile.ZipFile(temporary) as z:
 bad=z.testzip()
 if bad:raise RuntimeError('Corrupt packaged file: '+bad)
 count=len(z.namelist())
os.replace(temporary,target)
print('Packaged',count,'files;',round(target.stat().st_size/1024/1024,1),'MiB;',target)
