"""Build real, editable UI geometry. Screenshots are layout references only.
Run with Blender --background --factory-startup --python this_file.
All UI text, symbols, controls and thumbnails are meshes; no image textures.
"""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector, Matrix
W=Path(__file__).resolve().parents[1]; O=W/'models'; O.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.name='iMage Pro · Geometry UI';s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=48;s.eevee.use_raytracing=True
s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.film_transparent=True
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.82,.88,.94,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.5
font=bpy.data.fonts.load(os.environ.get('IMAGEPRO_FONT_PATH',str(W.parent/'iMage-Pro/Sources/ImagePro/Resources/Fonts/SourceHanSansSC-Regular.otf')))
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def rgba(h):return tuple(srgb(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def mat(name,h,rough=.35,metal=0,glass=0,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');c=rgba(h)
 b.inputs['Base Color'].default_value=c;b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;b.inputs['IOR'].default_value=1.38
 b.inputs['Transmission Weight'].default_value=glass;b.inputs['Coat Weight'].default_value=.06 if glass else .08
 b.inputs['Coat Roughness'].default_value=.07
 if glass:
  m.use_raytrace_refraction=True
  m['glassRole']='regular' if glass<.9 else 'clear'
 if emission:b.inputs['Emission Color'].default_value=c;b.inputs['Emission Strength'].default_value=emission
 return m
M={
 'shell':mat('Window · satin ceramic','E8EEF2',.26,.12),'paper':mat('Workspace · porcelain','F9FBFD',.5,emission=.1),
 'glass':mat('Liquid glass · regular','FFFFFF',.52,0,.995), 'clear':mat('Liquid glass · clear','FFFFFF',.38,0,.998), 'rim':mat('Glass · polished lip','FFFFFF',.065,0,.998),
 'ink':mat('Type · graphite','25313D',.32,emission=.15),'muted':mat('Secondary · slate','657A86',.4,emission=.15),
 'line':mat('Separators · mist','BDCED4',.45),'field':mat('Input · frosted inset','E5EBF2',.3,glass=.14),
 'selected':mat('Selection · pale blue','C2E6F2',.32),'accent':mat('Accent · azure','158FE8',.25,emission=.2),
 'white':mat('Control · ivory','FFFFFF',.28),'dark':mat('Current color','0D1626',.3),
 'red':mat('Close · coral','FF5F57'),'yellow':mat('Minimize · gold','FEBC2E'),'green':mat('Zoom · green','28C840')}
root=bpy.data.objects.new('iMagePro',None);s.collection.objects.link(root);root['construction']='Geometry only: no screenshot planes, no image textures'
def link(name,mesh,parent):
 ob=bpy.data.objects.new(name,mesh);s.collection.objects.link(ob);ob.parent=parent;return ob
def group(name,parent=root,location=(0,0,0)):
 ob=link(name,None,parent);ob.location=location;return ob
def box(name,x,y,w,h,z=.02,d=.035,r=.08,m='glass',p=root):
 # A beveled rounded extrusion with independent front and rim surfaces.
 r=min(r,w/2,h/2);pts=[];is_glass=m in ['glass','clear','rim'];corner_steps=25 if is_glass else 7
 for cx,cy,ang in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for i in range(corner_steps):
   a=math.radians(ang+i*90/(corner_steps-1));pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
 n=len(pts);verts=[(a,b,-d/2) for a,b in pts]+[(a,b,d/2) for a,b in pts]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(M[m] if isinstance(m,str) else m)
 ob=link(name,mesh,p);ob.location=(x,y,z)
 be=ob.modifiers.new('Continuous rounded lens edge','BEVEL');be.width=min(.055,d*.46) if is_glass else min(.009,d*.16);be.segments=12 if is_glass else 2
 if is_glass:
  mesh.materials.append(M['rim']);be.material=1;be.harden_normals=True
  for face in mesh.polygons:face.use_smooth=len(face.vertices)==4
  normals=ob.modifiers.new('Stable face and curved edge normals','WEIGHTED_NORMAL');normals.keep_sharp=True
 return ob
def glass_rim(name,x,y,w,h,z=.017,d=.12,r=.16,border=.018,p=root):
 # Open rounded ring: no opaque second panel behind the refractive face.
 def perimeter(w,h,r):
  pts=[]
  for cx,cy,ang in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
   for i in range(7):
    a=math.radians(ang+i*90/6);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
  return pts
 outer=perimeter(w,h,r);inner=perimeter(w-border*2,h-border*2,r-border);n=len(outer)
 verts=[(a,b,depth) for depth in [-d/2,d/2] for contour in [outer,inner] for a,b in contour];faces=[]
 for i in range(n):
  j=(i+1)%n
  faces.extend([(i,j,2*n+j,2*n+i),(n+j,n+i,3*n+i,3*n+j),(i,n+i,n+j,j),(2*n+j,3*n+j,3*n+i,2*n+i)])
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(M['rim'])
 ob=link(name,mesh,p);ob.location=(x,y,z);be=ob.modifiers.new('Rounded glass lip','BEVEL');be.width=.006;be.segments=3;return ob

def txt(name,body,x,y,size=.105,z=.11,p=root,m='ink',align='LEFT'):
 c=bpy.data.curves.new(name,'FONT');c.body=body;c.font=font;c.size=size*2.6;c.align_x=align;c.align_y='CENTER';c.extrude=.0018;c.bevel_depth=.00045;c.bevel_resolution=0;c.resolution_u=2
 ob=link(name,c,p);ob.location=(x,y,z);ob['uiText']=body;ob['uiTextSize']=size;ob['uiTextAlign']=align;ob.data.materials.append(M[m]);bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);return ob

def line(name,pts,width=.012,z=.12,p=root,m='ink',closed=False):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=width/2;c.bevel_resolution=2
 sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for v,(x,y) in zip(sp.points,pts):v.co=(x,y,0,1)
 sp.use_cyclic_u=closed;ob=link(name,c,p);ob.location.z=z;ob.data.materials.append(M[m]);bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);return ob

def disc(name,x,y,r,z=.1,p=root,m='white'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=.026,location=(x,y,z));o=bpy.context.object;o.name=name;o.parent=p;o.data.materials.append(M[m] if isinstance(m,str) else m)
 be=o.modifiers.new('Rounded edge','BEVEL');be.width=.011 if m=='clear' else .006;be.segments=10 if m=='clear' else 2
 if m=='clear':
  for face in o.data.polygons:face.use_smooth=len(face.vertices)==4
  normals=o.modifiers.new('Smooth circular glass rim','WEIGHTED_NORMAL');normals.keep_sharp=True
 o.select_set(False);return o

def icon(name,kind,x,y,size=.16,p=root,m='ink',z=.13):
 # Original vector constructions: solid/outlined geometry, never icon screenshots.
 g=group(name,p,(x,y,z));h=size/2
 def stroke(a,cl=False,w=.012):return line(name+'.stroke',[(xx*h,yy*h) for xx,yy in a],w,z=0,p=g,m=m,closed=cl)
 def circle(cx=0,cy=0,r=.8):return stroke([(cx+r*math.cos(i*math.tau/28),cy+r*math.sin(i*math.tau/28)) for i in range(28)],True)
 if kind in ['plus','close','chevron','check','minus']:
  if kind=='plus':stroke([(-.75,0),(.75,0)]);stroke([(0,-.75),(0,.75)])
  elif kind=='close':stroke([(-.6,-.6),(.6,.6)]);stroke([(-.6,.6),(.6,-.6)])
  elif kind=='chevron':stroke([(-.75,.3),(0,-.4),(.75,.3)])
  elif kind=='check':stroke([(-.7,0),(-.1,-.5),(.8,.7)])
  else:stroke([(-.7,0),(.7,0)])
 elif kind in ['search','zoom','eye']:
  if kind=='eye':stroke([(-1,0),(-.65,.48),(0,.65),(.65,.48),(1,0),(.65,-.48),(0,-.65),(-.65,-.48)],True);circle(r=.25)
  else:circle(-.15,.15,.65);stroke([(.35,-.35),(.9,-.9)])
 elif kind=='move':stroke([(-.5,.9),(-.5,-.6),(0,-.15),(.3,-.9),(.6,-.75),(.25,-.05),(.85,-.05)],True,w=.015)
 elif kind=='crop':stroke([(-.7,1),(-.7,-.7),(1,-.7)]);stroke([(-1,.7),(.7,.7),(.7,-1)])
 elif kind in ['canvas','folder','shape']:
  if kind=='folder':stroke([(-1,-.7),(1,-.7),(1,.5),(.1,.5),(-.1,.8),(-1,.8)],True)
  else:stroke([(-.75,-.7),(.9,-.7),(.9,.55),(-.75,.55)],True);stroke([(-.95,-.35),(-.95,.9),(.4,.9)])
 elif kind=='selection':
  for a,b in [((-1,-1),(-.4,-1)),((.4,-1),(1,-1)),((1,-1),(1,-.4)),((1,.4),(1,1)),((1,1),(.4,1)),((-.4,1),(-1,1)),((-1,1),(-1,.4)),((-1,-.4),(-1,-1))]:stroke([a,b])
 elif kind=='layers':
  for yy in [.45,0,-.45]:stroke([(-1,yy),(0,yy+.5),(1,yy),(0,yy-.5)],True)
 elif kind in ['sliders','basic']:
  for yy,cx in [(.7,-.4),(0,.4),(-.7,-.2)]:stroke([(-1,yy),(1,yy)]);circle(cx,yy,.16)
 elif kind in ['pen','curves']:
  stroke([(-.85,.8),(-.65,.1),(-.25,-.05),(.4,-.15),(.8,-.8)])
  circle(-.85,.8,.17);circle(.8,-.8,.17)
 elif kind in ['brush','eyedropper']:
  stroke([(-.8,-.9),(-.45,-.05),(.65,.95),(.95,.65),(-.05,-.45)],True);stroke([(-.45,-.05),(-.05,-.45)])
 elif kind=='text':stroke([(-.85,.8),(.85,.8)]);stroke([(0,.8),(0,-.9)]);stroke([(-.4,-.9),(.4,-.9)])
 elif kind in ['drop','gradient']:
  pts=[(0,1),(.55,.2),(.7,-.3),(.5,-.8),(0,-1),(-.5,-.8),(-.7,-.3),(-.55,.2)];stroke(pts,True,w=.022)
 elif kind=='sparkle':
  stroke([(0,1),(.2,.2),(1,0),(.2,-.2),(0,-1),(-.2,-.2),(-1,0),(-.2,.2)],True);stroke([(.6,.9),(.9,.9)]);stroke([(.75,.75),(.75,1.05)])
 elif kind=='grain':
  for i in range(16):a=i*math.tau/16;disc(name+'.dot',math.cos(a)*h*.8,math.sin(a)*h*.8,.008,z=0,p=g,m=m)
 elif kind=='palette':circle(r=.85);circle(-.3,.3,.13);circle(.25,.45,.13);circle(.5,0,.13);circle(-.4,-.3,.13)
 elif kind=='levels':
  for xx,hh in [(-.65,.5),(0,.8),(.65,1)]:stroke([(xx-.2,-.8),(xx+.2,-.8),(xx+.2,hh),(xx-.2,hh)],True)
 elif kind=='hand':stroke([(-.8,-.3),(-.7,.2),(-.4,.2),(-.4,.9),(-.1,1),(.1,.1),(.2,.9),(.5,.8),(.5,.05),(.75,.5),(1,.35),(.85,-.6),(.45,-.95),(-.1,-.8)],True)
 elif kind=='bandage':stroke([(-.9,-.35),(-.35,-.9),(.9,.35),(.35,.9)],True);stroke([(-.35,-.3),(.3,.35)]);circle(r=.1)
 elif kind=='trash':stroke([(-.7,.55),(.7,.55)]);stroke([(-.5,.55),(-.4,-.8),(.4,-.8),(.5,.55)]);stroke([(-.25,.6),(-.25,.9),(.25,.9),(.25,.6)])
 elif kind in ['undo','redo']:
  pts=[(-.6,.5),(-.25,.5),(.35,.5),(.7,.15),(.6,-.45),(.1,-.7)];
  if kind=='redo':pts=[(-a,b) for a,b in pts]
  stroke(pts);sgn=-1 if kind=='undo' else 1;stroke([(sgn*.25,.9),(sgn*.75,.5),(sgn*.25,.1)])
 else:circle();stroke([(-.4,-.4),(.4,.4)])
 return g

def gradient(name,x,y,w,h,z,p=root,nx=45,ny=30):
 verts=[];colors=[];faces=[]
 palette=[(.0,.2,'539CAB'),(.45,.1,'C7F4E9'),(.9,.1,'96E1DD'),(.2,.6,'DDF8EC'),(.6,.55,'327F96'),(.95,.8,'C4F7EF'),(.2,.95,'4C98AF')]
 for j in range(ny+1):
  for i in range(nx+1):
   u=i/nx;v=j/ny;weights=[math.exp(-((u-a)**2+(v-b)**2)/.045) for a,b,_ in palette];total=sum(weights)
   c=tuple(sum(ww*rgba(cc)[k] for ww,(_,_,cc) in zip(weights,palette))/total for k in range(3))+(1,)
   verts.append(((u-.5)*w,(.5-v)*h,0));colors.append(c)
 for j in range(ny):
  for i in range(nx):a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);attr=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for a,c in zip(attr.data,colors):a.color=c
 material=bpy.data.materials.get('Canvas · vertex colors')
 if not material:
  material=bpy.data.materials.new('Canvas · vertex colors');material.use_nodes=True;n=material.node_tree.nodes;bs=n.get('Principled BSDF');vc=n.new('ShaderNodeVertexColor');vc.layer_name='Color';material.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);material.node_tree.links.new(vc.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.35;bs.inputs['Roughness'].default_value=.55
 mesh.materials.append(material);ob=link(name,mesh,p);ob.location=(x,y,z);return ob

# Main interface: ceramic body, inset canvas, independent titlebar controls.
box('WindowEdge',0,0,10,6.94,z=-.13,d=.26,r=.12,m='shell')
box('Workspace',0,-.12,9.96,6.63,z=.012,d=.05,r=.11,m='paper')
box('Titlebar.glass',0,3.245,9.98,.43,z=.085,d=.055,r=.1,m='clear')
line('Titlebar.separator',[(-4.89,3.025),(4.89,3.025)],.008,z=.115,m='line')
for i,m in enumerate(['red','yellow','green']):disc('TrafficLights.'+m,-4.75+i*.155,3.25,.047,z=.14,m=m)
icon('Undo','undo',-4.11,3.25,.12);icon('Redo','redo',-3.88,3.25,.12)
for label,x in [('Settings',-3.7),('Projects',-3.18),('Extensions',-2.65),('About',-2.03),('···',-1.6)]:txt('Titlebar.'+label,label,x,3.25,.104,z=.135)
box('ProjectTab',-.55,3.25,.87,.245,z=.14,d=.035,r=.075,m='field');gradient('ProjectThumbnail',-.825,3.25,.2,.115,.165,nx=9,ny=6)
txt('ProjectName','Untitled',-.675,3.25,.101,z=.178);disc('UnsavedIndicator',-.2,3.25,.018,z=.18,m='ink')
icon('StartPage.icon','canvas',.055,3.25,.12);txt('StartPage.label','Start Page',.2,3.25,.103,z=.14)
icon('NewTab','plus',2.16,3.25,.12)
for label,x in [('Pro',2.96),('Smart',3.36)]:icon(label+'.chevron','chevron',x-.09,3.25,.07);txt(label+'.label',label,x,3.25,.098,z=.14)
box('Export.button',3.97,3.25,.44,.25,z=.14,d=.035,r=.06,m='field');txt('Export.label','Export',3.97,3.25,.099,z=.169,align='CENTER')
icon('Inspector.button.icon','sliders',4.37,3.25,.12);txt('Inspector.button.label','Inspector',4.49,3.25,.099,z=.14)
box('CanvasPaper',0,.05,9.05,5.08,z=.066,d=.045,r=.01,m='white')
gradient('SuperGradientCanvas',0,.05,9.02,5.05,.09)
# Toolbar detached from content as in actual application.
box('LayersButton',-4.4,-3.08,.92,.45,z=.14,d=.09,r=.15,m='clear')
icon('Layers.button.icon','layers',-4.59,-3.08,.14,z=.21);txt('Layers.button.label','Layers',-4.45,-3.08,.101,z=.21)
box('Toolbar',-.045,-3.08,7.53,.45,z=.14,d=.09,r=.14,m='clear')
box('ToolPicker',-3.12,-3.08,1.18,.31,z=.21,d=.037,r=.08,m='field');icon('ToolPicker.icon','drop',-3.6,-3.08,.14,z=.246)
txt('ToolPicker.label','Super Gradient',-3.47,-3.08,.096,z=.25);icon('ToolPicker.chevron','chevron',-2.61,-3.08,.08,z=.25)
txt('Toolbar.heading','Super Gradient',-2.34,-3.015,.105,z=.21);txt('Toolbar.hint','Use on the canvas.',-2.34,-3.17,.084,z=.21,m='muted')
box('Toolbar.currentColor',3.5,-3.08,.21,.21,z=.23,d=.05,r=.055,m='dark')
box('EffectsButton',4.38,-3.08,.98,.45,z=.14,d=.09,r=.15,m='clear');icon('Effects.button.icon','sparkle',4.08,-3.08,.14,z=.21);txt('Effects.button.label','Effects',4.23,-3.08,.104,z=.21)

# Coordinate system for panels: upper left (0,0), UI grid measured in units.
class UI:
 def __init__(self,g,left,top,w,h):self.g=g;self.left=left;self.top=top;self.w=w;self.h=h;self.prefix=g.name
 def xy(self,x,y):return self.left+x,self.top-y
 def box(self,name,x,y,w,h,m='field',r=.07,z=.085,d=.034):
  xx,yy=self.xy(x+w/2,y+h/2);return box(self.prefix+'.'+name,xx,yy,w,h,z,d,r,m,self.g)
 def text(self,name,value,x,y,size=.101,m='ink',align='LEFT',z=.15):
  xx,yy=self.xy(x,y);return txt(self.prefix+'.'+name,value,xx,yy,size,z,self.g,m,align)
 def icon(self,name,kind,x,y,size=.15,m='ink',z=.15):
  xx,yy=self.xy(x,y);return icon(self.prefix+'.'+name,kind,xx,yy,size,self.g,m,z)
 def sep(self,y,x=.14,w=None):
  a=self.xy(x,y);b=self.xy(x+(w or self.w-.28),y);return line(self.prefix+'.separator',[a,b],.006,.13,self.g,'line')
 def slider(self,name,y,value=1):
  self.box(name+'.track',.15,y,self.w-.3,.025,'line',.012,z=.125,d=.015)
  self.box(name+'.fill',.15,y,max(.02,(self.w-.3)*value),.025,'accent',.012,z=.135,d=.015)
  xx,yy=self.xy(.15+(self.w-.3)*value,y+.0125);disc(self.prefix+'.'+name+'.handle',xx,yy,.061,z=.158,p=self.g)
 def search(self,hint,y=.42):
  self.box('search',.12,y,self.w-.24,.25);self.icon('search.icon','search',.225,y+.125,.085,m='muted');self.text('search.placeholder',hint,.33,y+.125,.085,'muted')
 def header(self,title,subtitle=None):
  self.text('heading',title,.15,.23,.135);self.icon('close','close',self.w-.17,.23,.13,m='muted')
  if subtitle:self.text('subtitle',subtitle,.15,.42,.079,'muted')
 def dropdown(self,name,y,label,value):
  self.text(name+'.label',label,.15,y+.125,.092);self.box(name+'.input',.87,y,self.w-1.02,.245);self.text(name+'.value',value,.96,y+.125,.09);self.icon(name+'.chevron','chevron',self.w-.24,y+.125,.07)
def panel(name,anchor,left,top,w,h):
 g=group(name,root,anchor);ui=UI(g,left-anchor[0],top-anchor[1],w,h)
 group(name+'.polishedRim',g) # Edge is part of the body mesh, without an overlapping glass ring.
 ui.box('glassBody',0,0,w,h,'glass',.23,z=.017,d=.16)
 g['role']='menu';g['anchor']=list(anchor);g['panelWidth']=w;g['panelHeight']=h;g['menuCenter']=[left+w/2,top-h/2,.5]
 return ui

# Tool menu: categories and precise, individually modeled symbols.
tools=panel('Tools',(-3.12,-2.8,.32),-3.95,2.01,3.1,4.72)
tools.text('heading','Canvas',.72,.25,.14);tools.sep(.52,x=.72,w=2.2)
for i,k in enumerate(['canvas','selection','text','shape','pen','brush','drop','bandage']):
 y=.25+i*.385
 if i==0:tools.box('category.selected',.12,y-.16,.34,.32,'selected',.08)
 tools.icon('category.'+k,k,.29,y,.16,m='accent' if i==0 else 'muted')
for i,(name,k) in enumerate([('Move','move'),('Crop','crop'),('Hand','hand'),('Zoom','zoom'),('Eyedropper','eyedropper')]):
 y=.81+i*.385
 if i==0:tools.box('tool.selected',.72,y-.165,2.22,.33,'selected',.09)
 tools.icon('tool.'+name,k,.91,y,.13);tools.text('tool.'+name+'.label',name,1.11,y,.108)
 if i==0:tools.icon('tool.check','check',2.76,y,.1)
tools.text('hint.line1','Click a category for its last-used tool;',.72,4.32,.078,'muted');tools.text('hint.line2','hover to choose another tool.',.72,4.49,.078,'muted')

# Layers: geometry thumbnails, mask badge, enabled eyes, actual structure.
layers=panel('Layers',(-4.4,-2.8,.32),-4.73,2.01,2.05,4.72);layers.header('Layers');layers.search('Find Layers')
layers.dropdown('BlendMode',.84,'Blend Mode','Normal');layers.text('opacity.label','Opacity',.15,1.27,.086,'muted');layers.text('opacity.value','100 %',1.89,1.27,.086,'muted',align='RIGHT');layers.slider('opacity',1.42)
rows=[('Pen Path','pen',None),('Adjustment Layer','sliders',None),('Shape','shape','Mask · Effects: 2'),('TEXT','text',None),('Super Gradient','gradient','Effects: 3'),('Empty Layer','brush','Effects: 3')]
for i,(label,k,sub) in enumerate(rows):
 y=1.78+i*.37
 if i==4:layers.box('selectedRow',.12,y-.17,1.81,.32,'selected',.09)
 layers.icon('row'+str(i)+'.eye','eye',.24,y,.105,m='muted');layers.box('row'+str(i)+'.thumb',.39,y-.12,.245,.245,'field',.046)
 if i==4:
  xx,yy=layers.xy(.513,y);gradient('Layers.gradientThumbnail',xx,yy,.205,.205,.129,p=layers.g,nx=8,ny=8)
 else:layers.icon('row'+str(i)+'.thumbnail',k,.513,y,.115,m='muted')
 if i!=2:layers.text('row'+str(i)+'.title',label,.72,y-(.035 if sub else 0),.091)
 if sub and i!=2:layers.text('row'+str(i)+'.subtitle',sub,.72,y+.09,.068,'muted')
 if i==2:
  layers.box('maskThumbnail',.69,y-.12,.235,.235,'dark',.025);xx,yy=layers.xy(.805,y);disc('Layers.maskWhite',xx,yy,.087,z=.14,p=layers.g);disc('Layers.maskHole',xx,yy,.056,z=.159,p=layers.g,m='dark');layers.text('row2.title',label,.99,y-.035,.091);layers.text('row2.subtitle',sub,.99,y+.09,.068,'muted')
for k,x in [('plus',.19),('folder',.54),('canvas',.83),('trash',1.8)]:layers.icon('footer.'+k,k,x,4.48,.115,m='accent' if k=='plus' else 'muted')
layers.text('footer.FX','FX',1.1,4.48,.109)

# Effect menu matches the six actual categories and visible color adjustments.
effects=panel('Effects',(4.38,-2.8,.32),1.8,2.01,3.02,4.72);effects.header('Effects','Adding an effect creates an FX layer.');effects.search('Find Effects',.62)
for i,(a,b) in enumerate([('Color','Adjustments'),('Blur & Sharpen',''),('Distortion',''),('Light & Texture',''),('Layer Styles',''),('Portrait','')]):
 y=1.01+i*.39
 if i==0:effects.box('category.selected',.1,y-.02,.84,.29,'selected',.06)
 effects.text('category'+str(i)+'.label',a,.17,y+.07,.076,'accent' if i==0 else 'muted')
 if b:effects.text('category'+str(i)+'.line2',b,.17,y+.19,.076,'accent')
xx,yy=effects.xy(1.03,.98);line('Effects.divider',[(xx,yy),(xx,yy-3.32)],.006,z=.13,p=effects.g,m='line')
effects.text('list.title','Color Adjustments',1.13,1.05,.084)
effectrows=[('Basic Adjustments','sliders','Exposure, contrast, saturation'),('Hue & Saturation','palette','Adjust hue and color intensity'),('Selective Color','palette','Control eight color ranges'),('Levels','levels','Black, white and midtones'),('Curves','curves','RGB curves with a histogram'),('Color Wheels','palette','Highlights, midtones, shadows'),('Replace Color','palette','Replace a chosen color range'),('Remove Color','palette','Make a target color transparent'),('Fade','levels','A softly faded look'),('Smart HDR','sparkle','Balance shadows and highlights'),('Black & White','drop','Explore monochrome tones')]
for i,(label,k,desc) in enumerate(effectrows):
 y=1.29+i*.283;effects.icon('effect'+str(i)+'.symbol',k,1.22,y+.035,.115,m='muted');effects.text('effect'+str(i)+'.name',label,1.38,y,.078);effects.text('effect'+str(i)+'.detail',desc,1.38,y+.106,.058,'muted');effects.icon('effect'+str(i)+'.add','plus',2.85,y+.035,.06,m='muted')
effects.text('hint','Effects stay editable and can be disabled.',.15,4.52,.07,'muted')

# Inspector: two independent functional sheets + ordered effect switcher.
inspector=panel('Inspector',(4.45,2.96,.34),2.63,2.72,2.18,5.39);inspector.header('Super Gradient','Gradient layer')
inspector.text('smoothness.label','Smoothness',.15,.78,.091);inspector.text('smoothness.value','80 %',2.02,.78,.091,align='RIGHT');inspector.slider('smoothness',.91,.8)
inspector.text('nodes.title','Color Nodes',.15,1.26,.099)
nodecolors=['4292A6','CFF8E9','6CB3BF','A8DED9','73BBC1','FCDA8D','EA8F7D','9AB2E6','DDD2F3','84AFB4','76D6C9','F6CFD9','659EAA','E5F2EA','A3DCD9','1B6B87']
for i,col in enumerate(nodecolors):
 row=i//4;column=i%4;m=mat('NodeColor.'+str(i),col,.26);inspector.box('node'+str(i),.16+column*.48,1.49+row*.36,.39,.275,m,.067)
 if i==0:inspector.icon('node.selected','check',.355,1.625,.12,m='white')
inspector.text('nodeColor.title','Node Color',.15,3.09,.101);inspector.box('colorSwatch',.15,3.31,1.52,.3,mat('Active color','4292A6'),.07);inspector.icon('colorEyedropper','eyedropper',1.86,3.46,.15)
inspector.text('presets.title','Presets',.15,3.88,.101);inspector.box('savePreset',1.41,3.75,.62,.24,'field',.06);inspector.text('savePreset.label','Save Preset',1.72,3.87,.065,align='CENTER')
for i in range(6):
 xx,yy=inspector.xy(.435+(i%3)*.65,4.25+(i//3)*.54);inspector.box('preset'+str(i)+'.rim',.15+(i%3)*.65,4.05+(i//3)*.54,.57,.42,'white',.07);gradient('Inspector.preset'+str(i),xx,yy,.52,.37,.137,p=inspector.g,nx=8,ny=6)
inspector.text('hint','Drag nodes on the canvas to reshape color.',.15,5.15,.068,'muted')
# The switcher is geometrical, with individually movable effect entries.
switcher=group('EffectSwitcher',inspector.g,(-2.15,-.48,.0))
for i,(label,k) in enumerate([('Gradient','gradient'),('Basic','basic'),('Curves','curves'),('Film Grain','grain')]):
 entry=group('EffectEntry'+str(i),switcher,(0,-i*.59,0));disc('Switcher.'+label+'.glass',0,0,.147,z=.1,p=entry,m='clear');icon('Switcher.'+label+'.symbol',k,0,0,.15,p=entry,z=.135,m='accent' if i==0 else 'muted')
 box('Switcher.'+label+'.badge',0,-.24,.51,.155,z=.1,d=.025,r=.04,m='clear',p=entry);txt('Switcher.'+label+'.label',label,0,-.24,.064,z=.126,p=entry,align='CENTER')
icon('Switcher.add','plus',0,-2.38,.12,p=switcher,m='muted')
basic=panel('BasicInspector',(4.45,2.96,.34),2.63,2.72,2.18,5.39);basic.header('Basic','Empty Layer')
basic.text('position.heading','Position',.15,.85,.084,'muted');basic.text('dimensions.heading','Dimensions',1.19,.85,.084,'muted')
for i,(label,value) in enumerate([('X','0 px'),('W','1920 px'),('Y','0 px'),('H','1080 px')]):
 x=.15+(i%2)*1.035;y=1.01+(i//2)*.33;basic.box('field'+label,x,y,.885,.265);basic.text(label+'.label',label,x+.075,y+.132,.083,'muted');basic.text(label+'.value',value,x+.8,y+.132,.083,align='RIGHT')
for i,label in enumerate(['Center on Canvas','Center Relative to Layers']):basic.box('center'+str(i),.15+i*1.035,1.81,.885,.22,'selected',.055);basic.text('center'+str(i)+'.label',label,.59+i*1.035,1.92,.053,'accent',align='CENTER')
for name,y,val,progress in [('Rotation',2.36,'0 °',.5),('Opacity',2.85,'100 %',1)]:basic.text(name+'.label',name,.15,y,.084,'muted');basic.text(name+'.value',val,2.02,y,.084,'muted',align='RIGHT');basic.slider(name,y+.2,progress)
basic.dropdown('BlendMode',3.42,'Blend Mode','Normal');basic.text('hint','Original content preserved · Strokes: 0',.15,3.98,.068,'muted')
# No screenshot textures are loaded anywhere in this scene.
menus=[tools.g,inspector.g,layers.g,effects.g,basic.g]
for g in menus:g['geometryOnly']=True


# Full menus are preserved as alternative geometric pages, not text textures.
# These are available in the .blend and GLB; the story opens the default page.
tool_catalog={
 'Canvas':[('Move','move'),('Crop','crop'),('Hand','hand'),('Zoom','zoom'),('Eyedropper','eyedropper')],
 'Selection':[('Quick Selection','brush'),('Rectangular Marquee','selection'),('Elliptical Marquee','selection'),('Lasso','pen'),('Polygonal Lasso','pen'),('Color Range','palette')],
 'Text':[('Horizontal Text','text'),('Vertical Text','text')],
 'Shape':[('Rectangle','shape'),('Rounded Rectangle','shape'),('Ellipse','shape'),('Polygon','shape'),('Star','sparkle'),('Line','pen'),('Custom Shape','shape')],
 'Path':[('Pen Path','pen'),('Freeform Path','pen')],
 'Brush':[('Standard Brush','brush'),('Pencil','pen'),('Marker','brush'),('Airbrush','brush'),('Watercolor','drop'),('Oil Paint','brush'),('Texture Brush','grain'),('Eraser','brush')],
 'Fill':[('Linear Gradient','gradient'),('Radial Gradient','gradient'),('Super Gradient','gradient'),('Paint Bucket','drop'),('Color Fill','drop')],
 'Retouch':[('Smart Repair','sparkle'),('Texture Smoothing','bandage'),('Clone Stamp','brush'),('Dodge','drop'),('Burn','drop'),('Sponge','drop'),('Blur Brush','brush'),('Sharpen Brush','brush'),('Smudge','hand'),('Liquify Push','move')]}
canvaspage=group('ToolsPage.Canvas',tools.g);canvaspage['catalogPage']=True;canvaspage['defaultPage']=True;canvaspage['title']='Canvas'
for ob in list(tools.g.children):
 if ob is not canvaspage and (ob.name.startswith('Tools.tool.') or ob.name in ['Tools.heading','Tools.separator'] or ob.name.startswith('Tools.hint.')):ob.parent=canvaspage
catalog_pages=[]
for title,rows in list(tool_catalog.items())[1:]:
 g=group('ToolsPage.'+title,tools.g);g['catalogPage']=True;g['defaultPage']=False;g['title']=title;g['items']=[r[0] for r in rows]
 u=UI(g,tools.left,tools.top,tools.w,tools.h);u.text('heading',title,.72,.25,.14);u.sep(.52,x=.72,w=2.2)
 gap=min(.385,3.6/max(1,len(rows)))
 for i,(label,k) in enumerate(rows):
  y=.81+i*gap;u.icon('row'+str(i),k,.91,y,.13);u.text('row'+str(i)+'.label',label,1.11,y,.1)
 catalog_pages.append(g)
effect_catalog={
 'Color Adjustments':[('Basic Adjustments','sliders'),('Hue & Saturation','palette'),('Selective Color','palette'),('Levels','levels'),('Curves','curves'),('Color Wheels','palette'),('Replace Color','palette'),('Remove Color','palette'),('Fade','levels'),('Smart HDR','sparkle'),('Black & White','drop'),('Colorize','palette'),('Channel Mixer','sliders'),('LUT','palette')],
 'Blur & Sharpen':[('Gaussian Blur','drop'),('Motion Blur','drop'),('Focus Blur','drop'),('Sharpen','sparkle')],
 'Distortion':[('Bump Distortion','shape'),('Pinch Distortion','shape'),('Stretch Distortion','shape'),('Twirl Distortion','curves'),('Wave Distortion','curves')],
 'Light & Texture':[('Bloom','sparkle'),('Film Grain','grain'),('Vignette','drop'),('Pixelate','shape')],
 'Layer Styles':[('Stroke','shape'),('Shadow','shape'),('Inner Shadow','shape'),('Outer Glow','sparkle'),('Inner Glow','sparkle'),('Bevel & Emboss','shape'),('Fill Style','gradient')],
 'Portrait':[('Beauty','bandage'),('Body','move')]}
colorpage=group('EffectsPage.ColorAdjustments',effects.g);colorpage['catalogPage']=True;colorpage['defaultPage']=True;colorpage['title']='Color Adjustments'
for ob in list(effects.g.children):
 if ob is not colorpage and (ob.name.startswith('Effects.effect') or ob.name=='Effects.list.title'):ob.parent=colorpage
# The three additional items beneath the initial viewport are also geometry.
for j,(label,k) in enumerate(effect_catalog['Color Adjustments'][11:]):
 u=UI(colorpage,effects.left,effects.top,effects.w,effects.h);y=4.53+j*.28;u.icon('belowViewport'+str(j),k,1.22,y,.11);u.text('belowViewport'+str(j)+'.label',label,1.38,y,.078)
# Keep those rows in an explicitly collapsed subpage until a catalog page is opened.
extra=group('EffectsPage.MoreColorRows',effects.g);extra['catalogPage']=True;extra['defaultPage']=False;extra['title']='Additional Color Adjustments'
for ob in list(colorpage.children):
 if 'belowViewport' in ob.name:ob.parent=extra;ob.location.y+=1.5
catalog_pages.append(extra)
for title,rows in list(effect_catalog.items())[1:]:
 g=group('EffectsPage.'+title.replace(' ','').replace('&',''),effects.g);g['catalogPage']=True;g['defaultPage']=False;g['title']=title;g['items']=[r[0] for r in rows]
 u=UI(g,effects.left,effects.top,effects.w,effects.h);u.text('heading',title,1.13,1.05,.084)
 for i,(label,k) in enumerate(rows):
  y=1.32+i*.39;u.icon('row'+str(i),k,1.22,y,.115,m='muted');u.text('row'+str(i)+'.label',label,1.38,y,.079);u.icon('row'+str(i)+'.add','plus',2.85,y,.06,m='muted')
 catalog_pages.append(g)
for g in catalog_pages:
 g.scale=(.001,)*3
 for f in [1,624]:g.keyframe_insert('scale',frame=f)
(W/'content/ui-catalog.json').write_text(json.dumps({'tools':tool_catalog,'effects':effect_catalog,'basis':'Current app ToolCategory.branches and EffectCatalog.groups; English app terminology'},ensure_ascii=False,indent=2))


# Effect order belongs to the inspector's own switcher, not the Effects menu.
curve_entry=bpy.data.objects['EffectEntry2'];grain_entry=bpy.data.objects['EffectEntry3']
for row,startY,endY in [(curve_entry,-1.18,-1.77),(grain_entry,-1.77,-1.18)]:
 for f,y,z in [(1,startY,0),(255,startY,0),(276,endY,.08),(289,endY,0),(305,endY,0),(325,startY,0),(624,startY,0)]:
  row.location=(0,y,z);row.keyframe_insert('location',frame=f)

# Lighting defines a quiet luminous physical object, with enough depth for closeups.
def area(name,pos,energy,size,target):
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Key · large softbox',(-4,5,9),500,7,(0,0,0));area('Fill · studio',(5,-2,8),350,6,(0,0,0));area('Rim · cool top',(0,6,4),300,5,(0,0,0))
bpy.ops.object.camera_add(location=(.4,-.3,15));camera=bpy.context.object;camera.name='PresentationCamera';s.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=11.55
root.rotation_euler=(math.radians(7),math.radians(-9),0)
def aim(pos,target,scale):
 camera.location=pos;direction=(Vector(target)-camera.location).normalized();right=direction.cross(Vector((0,1,0))).normalized();up=right.cross(direction).normalized();camera.rotation_euler=Matrix((right,up,-direction)).transposed().to_euler();camera.data.ortho_scale=scale
# Fixed anchor, modest depth travel, asymptotic growth. No borrowed reference choreography.
s.render.fps=24;s.frame_start=1;s.frame_end=624
for g in menus:g.scale=(.001,)*3
basic.g.scale=(.001,)*3
for f in [1,624]:basic.g.keyframe_insert('scale',frame=f)
shots=[(1,(.4,-.3,15),(0,0,0),11.55),(42,(.4,-.3,15),(0,0,0),11.55),
 (100,(-2.35,-.45,15),(-2.35,-.45,.4),8.05),(150,(-2.35,-.45,15),(-2.35,-.45,.4),8.05),
 (238,(3.25,.0,15),(3.25,.0,.4),9.15),(290,(3.25,.0,15),(3.25,.0,.4),9.15),
 (378,(-3.6,-.45,15),(-3.6,-.45,.4),8.05),(430,(-3.6,-.45,15),(-3.6,-.45,.4),8.05),
 (518,(3.2,-.45,15),(3.2,-.45,.4),8.05),(568,(3.2,-.45,15),(3.2,-.45,.4),8.05),
 (614,(.4,-.3,15),(0,0,0),11.55),(624,(.4,-.3,15),(0,0,0),11.55)]
for f,pos,target,sc in shots:
 aim(pos,target,sc);camera.keyframe_insert('location',frame=f);camera.keyframe_insert('rotation_euler',frame=f);camera.data.keyframe_insert('ortho_scale',frame=f)
for g,start in zip(menus[:4],[48,188,328,468]):
 home=g.location.copy()
 for f,k,dz in [(1,.001,0),(start,.001,0),(start+25,1.018,.22),(start+38,1,.18),(start+94,1,.18),(start+118,.001,0),(624,.001,0)]:
  g.scale=(k,)*3;g.location=home+Vector((0,0,dz));g.keyframe_insert('scale',frame=f);g.keyframe_insert('location',frame=f)
 for ob in g.children:
  if ob.name.endswith(('glassBody','polishedRim')) or (ob.get('catalogPage') and not ob.get('defaultPage')):continue
  # Independent internal items grow a few frames after their panel.
  for f,k in [(1,.001),(start+8,.001),(start+35,1),(start+94,1),(start+116,.001),(624,.001)]:ob.scale=(k,)*3;ob.keyframe_insert('scale',frame=f)
for o in [camera,camera.data,*menus,*[c for g in menus for c in g.children]]:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='BEZIER'
# Retain one editable source scene; localized builds create the published models.
def descendants(o):
 yield o
 for child in o.children:yield from descendants(child)
root.rotation_euler=(math.radians(7),math.radians(-9),0);s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'image-pro.blend'))
mesh=[o for o in descendants(root) if o.type=='MESH']
report={'construction':'Geometry-only UI. Screenshot files were read only as visual references, never loaded into Blender.','meshObjects':len(mesh),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in mesh),'imageTextures':0,'menus':['Tools','Inspector','Layers','Effects','BasicInspector'],'type':'editable physical surfaces, raised glyph meshes, vector icon meshes, vertex-colored gradient mesh','toolCategories':len(tool_catalog),'toolEntries':sum(len(v) for v in tool_catalog.values()),'effectCategories':len(effect_catalog),'effectEntries':sum(len(v) for v in effect_catalog.values()),'glassMaterials':{'regularTransmission':.995,'clearTransmission':.998,'roughness':{'regular':.52,'clear':.38,'edge':.065},'rimConstruction':'single body with 12-segment rounded bevel and smooth weighted normals; no overlapping rim or opaque backing','approximation':'physical refraction, frosted transmission and specular edge; not a native macOS material'},'animationSeconds':26,'frameRate':24}
(W/'content/model-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('GEOMETRY_UI_READY',json.dumps(report),flush=True)
