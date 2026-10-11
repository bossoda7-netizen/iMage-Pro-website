"""Rebuild raised UI glyphs in four languages, retaining geometry and animation.
Run after build-blender.py with Blender --background --python this_file.
"""
import bpy, json, math, runpy, tempfile, os
from pathlib import Path
W=Path(__file__).resolve().parents[1];BASE=W/'public/assets/3d';BASE.mkdir(parents=True,exist_ok=True)
translations=json.loads((W/'content/model-translations.json').read_text())
FONT=Path(os.environ.get('IMAGEPRO_FONT_PATH',str(W.parent/'iMage-Pro/Sources/ImagePro/Resources/Fonts/SourceHanSansSC-Regular.otf')))
report={}
def text_width(ob):
 xs=[v.co.x for v in ob.data.vertices]
 return max(xs)-min(xs) if xs else 0

def budget(ob):
 name=ob.name;parent=ob.parent;old=text_width(ob)
 fixed={'Titlebar.Settings':.46,'Titlebar.Projects':.47,'Titlebar.Extensions':.56,'Titlebar.About':.37,'Inspector.button.label':.40,'Export.label':.37,'Pro.label':.23,'Smart.label':.29,'StartPage.label':1.7,'ProjectName':.44,'Layers.button.label':.44,'Effects.button.label':.57,'ToolPicker.label':.78,'Toolbar.heading':2.5,'Toolbar.hint':3.4}
 if name in fixed:return fixed[name]
 if name.startswith('Tools'):return 2.2 if 'hint.' in name else 2.1 if name.endswith('.heading') else 1.65
 if name.startswith('EffectsPage.'):return 1.45
 if name.startswith('Switcher.') and name.endswith('.label'):return .45
 if '.category' in name and name.startswith('Effects'):return .73
 if name.startswith('Effects.effect'):
  return 1.38 if name.endswith('.name') else 1.35
 if name.endswith('BlendMode.label'):return .64
 if name.startswith('BasicInspector.') and name.endswith('.label'):
  if '.center' in name:return .79
  if name.split('.')[-2] in ['X','Y','W','H']:return .2
 if parent and parent.get('panelWidth'):
  w=parent['panelWidth'];left=parent['menuCenter'][0]-w/2-parent.location.x
  if ob.get('uiTextAlign')=='LEFT':return max(.25,left+w-.17-ob.location.x)
 return max(old*1.1,.2)

def rebuild(lang):
 bpy.ops.wm.open_mainfile(filepath=str(W/'models/image-pro.blend'))
 font=bpy.data.fonts.load(str(FONT));items=[]
 for ob in list(bpy.data.objects):
  source=ob.get('uiText')
  if source is None:continue
  body='Untitled' if ob.name=='ProjectName' else translations[lang][source]
  curve=bpy.data.curves.new(ob.name+'.localized','FONT');curve.body=body;curve.font=font;curve.size=ob['uiTextSize']*2.6;curve.align_x=ob['uiTextAlign'];curve.align_y='CENTER';curve.extrude=.0018;curve.bevel_depth=.00045;curve.bevel_resolution=0;curve.resolution_u=2
  temp=bpy.data.objects.new('__localized_glyph',curve);bpy.context.scene.collection.objects.link(temp)
  for mat in ob.data.materials:curve.materials.append(mat)
  bpy.ops.object.select_all(action='DESELECT');temp.select_set(True);bpy.context.view_layer.objects.active=temp;bpy.ops.object.convert(target='MESH')
  mesh=temp.data;allowed=budget(ob);width=text_width(temp);fit=min(1,allowed/width) if width else 1
  for v in mesh.vertices:v.co.x*=fit;v.co.y*=fit
  old=ob.data;ob.data=mesh;bpy.data.objects.remove(temp,do_unlink=True)
  if old.users==0:bpy.data.meshes.remove(old)
  ob['uiText']=body;ob['uiLanguage']=lang;ob['uiTextSource']=source;ob['uiTextFit']=fit
  items.append({'name':ob.name,'source':source,'text':body,'fit':round(fit,4),'width':round(text_width(ob),4),'budget':round(allowed,4)})
 root=bpy.data.objects['iMagePro'];root['uiLanguage']=lang;s=bpy.context.scene;s.frame_set(1);root.rotation_euler=(0,0,0)
 def descendants(o):
  yield o
  for child in o.children:yield from descendants(child)
 actions=[];bpy.ops.object.select_all(action='DESELECT')
 for ob in descendants(root):
  if ob.animation_data:actions.append((ob,ob.animation_data.action));ob.animation_data.action=None
  ob.scale=(1,1,1);ob.select_set(True)
 bpy.context.view_layer.objects.active=root
 O=BASE/lang;O.mkdir(exist_ok=True)
 bpy.ops.export_scene.gltf(filepath=str(O/'image-pro.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_yup=True,export_apply=True)
 for ob,action in actions:ob.animation_data.action=action
 root.rotation_euler=(math.radians(7),math.radians(-9),0);s.frame_set(1)
 temporary=tempfile.TemporaryDirectory(prefix='imagepro-localized-');scene_source=Path(temporary.name)/'image-pro.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(scene_source))
 for name,frame in [('product',1),('tools',120),('inspector',238),('order',290),('layers',400),('effects',540)]:
  s.frame_set(frame);s.render.filepath=str(O/(name+'-poster.png'));bpy.ops.render.render(write_still=True)
 # Dark script always reopens the saved light scene, so tightening is applied once.
 runpy.run_path(str(W/'scripts/render-dark-posters.py'),init_globals={'MODEL_DIRECTORY':O,'SOURCE_SCENE':scene_source})
 temporary.cleanup()
 report[lang]={'textObjects':len(items),'items':items,'appearances':['light','dark']}
 print('LOCALIZED_MODEL_READY',lang,len(items),flush=True)
for lang in ['zh','en','ja','ko']:rebuild(lang)
(W/'content/model-localization-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
p=W/'content/model-report.json';r=json.loads(p.read_text());r['localization']={'languages':list(report),'textObjectsPerLanguage':185,'projectNames':'Creator content is preserved','geometryTextures':0};r['appearanceLoading']='Only current language/current appearance GLB is requested initially; opposite appearance is loaded on change';p.write_text(json.dumps(r,ensure_ascii=False,indent=2))
