"""Render dark geometry fallbacks while preserving the approved light scene."""
import bpy,math,json,struct
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=Path(globals()['MODEL_DIRECTORY'])
bpy.ops.wm.open_mainfile(filepath=str(globals()['SOURCE_SCENE']))
# Tighten the dark model's contour and cross-section, keeping the light mesh untouched.
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 bevel=ob.modifiers.get('Continuous rounded lens edge')
 if not bevel or not any(m and m.name.startswith('Liquid glass') for m in ob.data.materials):continue
 verts=ob.data.vertices;n=len(verts)//2
 if n==100 and len(verts)==200:
  w=max(v.co.x for v in verts)*2;h=max(v.co.y for v in verts)*2
  radius=h/2-verts[0].co.y;radius*=.65
  points=[]
  for cx,cy,ang in [(w/2-radius,h/2-radius,0),(-w/2+radius,h/2-radius,90),(-w/2+radius,-h/2+radius,180),(w/2-radius,-h/2+radius,270)]:
   for i in range(25):
    a=math.radians(ang+i*90/24);points.append((cx+radius*math.cos(a),cy+radius*math.sin(a)))
  for i,v in enumerate(verts):v.co.x,v.co.y=points[i%n]
  ob.data.update()
 bevel.width*=.42;bevel.segments=8
# Export geometry in the same coordinate system and node hierarchy as the light GLB.
s=bpy.context.scene;s.frame_set(1);root=bpy.data.objects['iMagePro'];root.rotation_euler=(0,0,0)
def descendants(o):
 yield o
 for child in o.children:yield from descendants(child)
bpy.ops.object.select_all(action='DESELECT');actions=[]
for ob in descendants(root):
 if ob.animation_data:actions.append((ob,ob.animation_data.action));ob.animation_data.action=None
 ob.scale=(1,1,1);ob.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(O/'image-pro-dark.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_yup=True,export_apply=True)
for ob,action in actions:ob.animation_data.action=action
root.rotation_euler=(math.radians(7),math.radians(-9),0);s.frame_set(1)
palette={'Window · satin ceramic':'30343b','Workspace · porcelain':'191c22','Liquid glass · regular':'7c8088','Liquid glass · clear':'92969e','Glass · polished lip':'aab1ba','Type · graphite':'f1f3f6','Secondary · slate':'bec7d2','Separators · mist':'555f6d','Input · frosted inset':'303640','Selection · pale blue':'294d60','Accent · azure':'74c9ff','Control · ivory':'e8edf3'}
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for m in bpy.data.materials:
 if m.name not in palette or not m.use_nodes:continue
 n=m.node_tree.nodes.get('Principled BSDF')
 if not n:continue
 h=palette[m.name];c=tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
 n.inputs['Base Color'].default_value=c
 if n.inputs['Emission Strength'].default_value>0:n.inputs['Emission Color'].default_value=c
s=bpy.context.scene;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.18,1)
for o in s.objects:
 if o.type=='LIGHT':o.data.energy*=.78
s.frame_set(1)
for name,frame in [('product',1),('tools',120),('inspector',238),('order',290),('layers',400),('effects',540)]:
 s.frame_set(frame);s.render.filepath=str(O/(name+'-poster-dark.png'));bpy.ops.render.render(write_still=True)
print('DARK_POSTERS_READY')
