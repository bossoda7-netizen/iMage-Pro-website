from pathlib import Path
import urllib.request,tarfile,io,json
V=Path(__file__).resolve().parents[1]/'public/vendor'
for name,version,files in [('gsap','3.13.0',['dist/gsap.min.js','dist/ScrollTrigger.min.js','dist/gsap.min.js.map','dist/ScrollTrigger.min.js.map','LICENSE']),('three','0.180.0',['build/three.module.js','build/three.core.js','examples/jsm/loaders/GLTFLoader.js','examples/jsm/environments/RoomEnvironment.js','examples/jsm/utils/BufferGeometryUtils.js','LICENSE'])]:
 data=urllib.request.urlopen(f'https://registry.npmjs.org/{name}/-/{name}-{version}.tgz',timeout=30).read();tar=tarfile.open(fileobj=io.BytesIO(data));target=V/name
 for file in files:
  member=next((m for m in tar.getmembers() if m.name=='package/'+file),None)
  if member:
   path=target/file;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(tar.extractfile(member).read())
  else:print('Not in package:',name,file)
 (target/'version.json').write_text(json.dumps({'name':name,'version':version,'source':f'https://registry.npmjs.org/{name}'}))
 print('Fetched',name,version)
