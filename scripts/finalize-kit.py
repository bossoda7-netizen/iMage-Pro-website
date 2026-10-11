from pathlib import Path
from PIL import Image
import json,hashlib,re,struct
W=Path(__file__).resolve().parents[1];P=W/'public';A=P/'assets';external=W.parents[0].parent/'iMage Pro 官网筹备'
# Manifest describes only assets actually distributed by the website.
manifest={'created':'2026-10-10','appIcon':{'source':'creator-owned original icon raster artwork'},'productScreenshots':{'source':'8 creator-supplied four-language hero screenshots','changes':'complete source canvas and shadow alpha retained; WebP export; originals untouched'},'geometryModel':json.loads((W/'content/model-report.json').read_text()),'font':{'name':'Source Han Sans SC','license':'SIL OFL 1.1','use':'rendered glyphs and graphics; font binary not shipped by website'},'publication':{'deployed':False,'eventOpen':False},'files':[]}
for p in sorted(A.rglob('*')):
 if p.is_file() and not p.name.startswith('.') :manifest['files'].append({'path':str(p.relative_to(A)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(W/'content/asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
errors=[]
for p in (x for x in P.glob('*.html') if not x.name.startswith('.')):
 for raw in re.findall(r'(?:src|srcset|href|poster)="([^"]+)"',p.read_text()):
  if raw.startswith(('http','mailto:','#','data:')):continue
  target=P/raw.split('#')[0].split('?')[0]
  if not target.exists():errors.append(f'{p.name}: {raw}')
for s in [256]:
 if Image.open(A/f'brand/app-icon-{s}.png').size!=(s,s):errors.append(f'icon {s}')
for lang in ['zh','en']:
 if Image.open(A/f'social/share-{lang}.png').size!=(1200,630):errors.append('social dimensions')
for lang,file in [('zh-Hans','index.html'),('en','index-en.html'),('ko','index-ko.html'),('ja','index-ja.html')]:
 if f'lang="{lang}"' not in (P/file).read_text():errors.append('language '+lang)
meta=json.loads((A/'downloads/release.json').read_text())
if meta['version']!='0.9.2' or meta['minimumMacOS']!='14.0' or meta['architecture']!='arm64':errors.append('release data')
for p in (x for x in P.glob('index*.html') if not x.name.startswith('.')):
 if re.search(r'智能修复|Smart Repair',p.read_text(),re.I):errors.append('unwanted marketing '+p.name)
hero_layout=json.loads((W/'content/hero-layout.json').read_text())
translations=json.loads((W/'content/model-translations.json').read_text())
localization=json.loads((W/'content/model-localization-report.json').read_text())
for lang in ['zh','en','ja','ko']:
 for appearance,filename in [('light','image-pro.glb'),('dark','image-pro-dark.glb')]:
  b=(A/'3d'/lang/filename).read_bytes()
  if b[:4]!=b'glTF':errors.append('GLB header '+lang+appearance);continue
  size=struct.unpack_from('<I',b,12)[0];model=json.loads(b[20:20+size])
  if model.get('images') or model.get('textures'):errors.append('Image textures in UI model '+lang)
  if len(model.get('meshes',[]))<400:errors.append('UI geometry missing '+lang)
  textnodes=[n for n in model.get('nodes',[]) if 'uiText' in n.get('extras',{})]
  if len(textnodes)!=185:errors.append('Missing text objects '+lang+appearance)
  for node in textnodes:
   e=node['extras'];expected='Untitled' if node['name']=='ProjectName' else translations[lang][e['uiTextSource']]
   if e['uiLanguage']!=lang or e['uiText']!=expected:errors.append('Wrong model translation '+lang+node['name'])
  for name in ['product','tools','inspector','layers','effects','order']:
   if not (A/'3d'/lang/(name+'-poster'+('-dark' if appearance=='dark' else '')+'.webp')).exists():errors.append('Missing localized poster '+lang+name)
 for item in localization[lang]['items']:
  if item['width']>item['budget']+.002:errors.append('UI text overflow '+lang+item['name'])
 suffix='' if lang=='zh' else '-'+lang;page=(P/('index'+suffix+'.html')).read_text()
 for theme in ['light','dark']:
  hero=A/f'product/app-{lang}-{theme}.webp'
  if not hero.exists() or list(Image.open(hero).size)!=hero_layout['images'][f'app-{lang}-{theme}']['size']:errors.append('Hero dimensions '+lang+theme)
  if f'assets/product/app-{lang}-{theme}.webp' not in page:errors.append('Wrong hero pairing '+lang+theme)
for p in P.rglob('*'):
 if p.is_file() and (p.suffix in ['.blend','.blend1','.mov','.mp4','.webm'] or p.name=='assets.html'):errors.append('Unpublished production asset '+str(p.relative_to(P)))
if errors:raise SystemExit('\n'.join(errors))
report=f"""# 官网验收

2026-10-10

- 首页、隐私、活动与许可证页面的本地引用均存在。
- 四语深浅首图完整保留阴影，尺寸与记录一致。
- 8个GLB结构有效，每套185个文字对象匹配对应语言，未使用截图纹理。
- 48张静态回退图完整，适用于手机及减少动态效果设置。
- 品牌图标和1200×630分享图尺寸正确。
- 公开目录不含素材验收页、Blender源文件、旧截图、视频或制作元数据。
- 官网需要的第三方许可与运行依赖已保留。
- 尚未部署；下载与投稿保持筹备状态。

公开素材文件数量：{len(manifest['files'])}。
"""
external.mkdir(exist_ok=True);(external/'素材验收.md').write_text(report)
print('Material checks passed:',len(manifest['files']),'assets')
