const appearance = matchMedia('(prefers-color-scheme: dark)');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const compact = matchMedia('(max-width: 820px)').matches;
const chapters = [...document.querySelectorAll('.chapter')];
const stage = document.querySelector('#model-stage');
const metadata = await fetch('assets/downloads/release.json').then(r=>r.json()).catch(()=>null);
if (metadata?.downloadUrl && metadata.releaseReady) {
  const a=document.querySelector('[data-download]');a.href=metadata.downloadUrl;a.removeAttribute('aria-disabled');if (!a.textContent.trim()) a.textContent='iMage Pro ↓';
  if (metadata.notarized) document.querySelector('.release-status').hidden=true;
}
if (metadata?.sourceUrl) {
  const a=document.querySelector('[data-source]');a.href=metadata.sourceUrl;a.textContent='GitHub ↗';const status=document.querySelector('.source-status');if(status)status.hidden=true;
}
if (window.gsap && window.ScrollTrigger && !reduced) {
  gsap.registerPlugin(ScrollTrigger);
  const motion=gsap.matchMedia();
  motion.add('(prefers-reduced-motion: no-preference)',()=>{
    gsap.fromTo('.hero-heading > *',{y:22,autoAlpha:0},{y:0,autoAlpha:1,duration:.85,stagger:.09,ease:'power2.out'});
    gsap.fromTo('.hero-window',{y:25,autoAlpha:0},{y:0,autoAlpha:1,duration:1.2,ease:'power2.out',delay:.2});
    document.querySelectorAll('.reveal').forEach(el=>gsap.fromTo(el,{y:30,autoAlpha:0},{y:0,autoAlpha:1,duration:.8,ease:'power2.out',scrollTrigger:{trigger:el,start:'top 90%',once:true}}));
  });
}
if (!compact && !reduced && stage && window.gsap && window.ScrollTrigger) {
  const loadObserver=new IntersectionObserver(async entries=>{
    if(!entries.some(e=>e.isIntersecting))return;
    loadObserver.disconnect();
    try {
      const THREE=await import('three');
      const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');
      const {RoomEnvironment}=await import('three/addons/environments/RoomEnvironment.js');
      const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'});
      renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.transmissionResolutionScale=.75;
      renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
      stage.append(renderer.domElement);
      const scene=new THREE.Scene();
      const pmrem=new THREE.PMREMGenerator(renderer);const studioRoom=new RoomEnvironment();
      const reflectionMap=pmrem.fromScene(studioRoom,.04);scene.environment=reflectionMap.texture;
      studioRoom.dispose();pmrem.dispose();
      const opaqueGlass=matchMedia('(prefers-reduced-transparency: reduce), (prefers-contrast: more)').matches;
      const camera=new THREE.OrthographicCamera(-6,6,6,-6,.1,100);
      const pose=new THREE.Group();pose.rotation.set(.10,-.14,0);scene.add(pose);
      const initialAppearance=appearance.matches?'dark':'light';
      const modelLanguage=({'zh-Hans':'zh',en:'en',ja:'ja',ko:'ko'})[document.documentElement.lang]||'zh';
      stage.dataset.modelLanguage=modelLanguage;
      const modelUrls={light:`assets/3d/${modelLanguage}/image-pro.glb?v=localized-ui-11`,dark:`assets/3d/${modelLanguage}/image-pro-dark.glb?v=localized-ui-11`};
      const gltf=await new GLTFLoader().loadAsync(modelUrls[initialAppearance]);
      stage.dataset.initialModel=initialAppearance;
      const model=gltf.scene;model.rotation.x=Math.PI/2;pose.add(model);
      // Keep exported physical materials, raised glyphs and vertex colors.
      // All UI parts are geometry; never replace them with screenshot planes.
      const adaptMaterial=(source,mesh)=>{
        let material=source.clone();
        if(source.name.startsWith('Liquid glass')||source.name==='Glass · polished lip'){
          const rim=source.name==='Glass · polished lip';
          material.envMapIntensity=rim?.4:.18;material.specularIntensity=rim?1:.3;
          // Refraction uses this surface's actual depth, including small switcher lenses.
          mesh.geometry.computeBoundingBox();
          const extent=mesh.geometry.boundingBox.getSize(new THREE.Vector3());
          material.thickness=Math.max(.006,Math.min(extent.x,extent.y,extent.z));
          material.ior=1.38;material.attenuationDistance=Infinity;
          material.attenuationColor=new THREE.Color(0xffffff);
          if(opaqueGlass){material.transmission=0;material.roughness=.3;}
        }else if(source.name==='Canvas · vertex colors'){
          material=new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide,toneMapped:false});
        }else material.envMapIntensity=.65;
        return material;
      };
      const contentSurfaces=new Set(['WindowEdge','Workspace','CanvasPaper','SuperGradientCanvas']);
      const isContentSurface=mesh=>{let node=mesh;while(node&&node!==model){if(contentSurfaces.has(node.name))return true;node=node.parent;}return false;};
      model.traverse(o=>{
        o.scale.setScalar(1);
        if(o.userData.catalogPage)o.visible=!!o.userData.defaultPage;
        if(o.isMesh){
          o.material=Array.isArray(o.material)?o.material.map(m=>adaptMaterial(m,o)):adaptMaterial(o.material,o);
          const surfaces=Array.isArray(o.material)?o.material:[o.material];
          const glass=surfaces.some(m=>m.transmission>0);
          o.layers.set(glass||isContentSurface(o)?0:1);
        }
      });
      const ambient=new THREE.HemisphereLight(0xffffff,0x90909a,1.1);ambient.layers.enable(1);scene.add(ambient);
      const key=new THREE.DirectionalLight(0xffffff,1.3);key.position.set(-4,6,9);key.layers.enable(1);scene.add(key);
      const fill=new THREE.DirectionalLight(0xe9efff,.65);fill.position.set(5,-2,6);fill.layers.enable(1);scene.add(fill);
      stage.dataset.glassMode=opaqueGlass?'opaque-accessibility':'frosted-refraction';stage.dataset.foregroundPass='separate-sharp-ui';
      const menus=['Tools','Inspector','Layers','Effects','BasicInspector'].map(n=>model.getObjectByName(n)).filter(Boolean);
      menus.forEach(p=>{p.userData.home=p.position.clone();p.scale.setScalar(.001);p.visible=false;});
      const switcher=model.getObjectByName('EffectSwitcher');
      const curveEntry=model.getObjectByName('EffectEntry2');
      const grainEntry=model.getObjectByName('EffectEntry3');
      const orderHome=[curveEntry?.position.clone(),grainEntry?.position.clone()];
      const sceneMenus=['Tools','Inspector','Layers','Effects','Inspector'];
      let visible=true,disposed=false,active=-1,transition=null,aspect=1;
      const view={x:0,y:0,height:12};
      const appearanceMaterials=new Map();
      const geometryByAppearance=new Map([[initialAppearance,new Map()]]);
      const geometryLoads=new Map();
      model.traverse(o=>{if(o.isMesh)geometryByAppearance.get(initialAppearance).set(o.name,o.geometry);});
      const applyGeometry=()=>{
        const wanted=appearance.matches?'dark':'light';
        const loaded=geometryByAppearance.has(wanted)?wanted:initialAppearance;
        const meshes=geometryByAppearance.get(loaded);
        model.traverse(o=>{if(o.isMesh&&meshes.has(o.name))o.geometry=meshes.get(o.name);});
        stage.dataset.edgeProfile=loaded==='dark'?'tight-dark-bevel':'rounded-light-bevel';
        stage.dataset.loadedGeometryCount=String(geometryByAppearance.size);
      };
      const loadGeometry=theme=>{
        if(geometryLoads.has(theme))return geometryLoads.get(theme);
        const pending=new GLTFLoader().loadAsync(modelUrls[theme]).then(asset=>{
          const meshes=new Map(),materials=new Set();
          asset.scene.traverse(o=>{if(o.isMesh){meshes.set(o.name,o.geometry);(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m));}});
          materials.forEach(m=>m.dispose());
          if(disposed){meshes.forEach(g=>g.dispose());return;}
          geometryByAppearance.set(theme,meshes);applyGeometry();draw();
        }).catch(error=>{console.warn('Appearance geometry unavailable.',error);geometryLoads.delete(theme);});
        geometryLoads.set(theme,pending);return pending;
      };
      model.traverse(o=>{if(o.isMesh)(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>{
        if(!appearanceMaterials.has(m))appearanceMaterials.set(m,{color:m.color.clone(),emissive:m.emissive?.clone(),environment:m.envMapIntensity,specular:m.specularIntensity});
      });});
      const darkPalette={
        'Window · satin ceramic':'#30343b','Workspace · porcelain':'#191c22',
        'Liquid glass · regular':'#7c8088','Liquid glass · clear':'#92969e',
        'Glass · polished lip':'#aab1ba','Type · graphite':'#f1f3f6',
        'Secondary · slate':'#bec7d2','Separators · mist':'#555f6d',
        'Input · frosted inset':'#303640','Selection · pale blue':'#294d60',
        'Accent · azure':'#74c9ff','Control · ivory':'#e8edf3'
      };
      const updateAppearance=()=>{
        const dark=appearance.matches;
        appearanceMaterials.forEach((saved,m)=>{
          m.color.copy(saved.color);if(saved.emissive)m.emissive.copy(saved.emissive);
          m.envMapIntensity=saved.environment;m.specularIntensity=saved.specular;
          if(dark&&darkPalette[m.name]){
            m.color.set(darkPalette[m.name]);
            if(saved.emissive&&saved.emissive.r+saved.emissive.g+saved.emissive.b>0)m.emissive.copy(m.color);
            if(m.name.startsWith('Liquid glass'))m.envMapIntensity=.09;
            if(m.name==='Glass · polished lip'){m.envMapIntensity=.17;m.specularIntensity=.4;}
            if(opaqueGlass&&m.name.startsWith('Liquid glass'))m.color.set('#282d35');
          }
        });
        ambient.intensity=dark?.82:1.1;key.intensity=dark?1.05:1.3;fill.intensity=dark?.4:.65;
        applyGeometry();const wanted=dark?'dark':'light';if(!geometryByAppearance.has(wanted))loadGeometry(wanted);
        stage.dataset.appearance=dark?'dark':'light';draw();
      };
      const draw=()=>{
        if(!visible||document.hidden||disposed)return;
        // Only content and glass enter the transmission buffer. Keep foreground glyphs
        // out of the refractive image, then draw them sharply against retained depth.
        camera.layers.set(0);renderer.autoClear=true;renderer.render(scene,camera);
        camera.layers.set(1);renderer.autoClear=false;renderer.render(scene,camera);
        camera.layers.set(0);renderer.autoClear=true;
      };
      const projection=()=>{
        const half=view.height/2;camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;
        camera.position.set(view.x,view.y,18);camera.lookAt(view.x,view.y,0);camera.updateProjectionMatrix();draw();
      };
      const size=()=>{const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h)return;aspect=w/h;renderer.setSize(w,h);projection();};
      const resizeObserver=new ResizeObserver(size);resizeObserver.observe(stage);size();
      updateAppearance();appearance.addEventListener('change',updateAppearance);
      stage.querySelector('.model-fallback').style.opacity='0';
      const parts=p=>p.children.filter(o=>!o.name.endsWith('glassBody')&&!o.name.endsWith('polishedRim')&&(!o.userData.catalogPage||o.userData.defaultPage));
      const menuTarget=p=>{
        const [x,y,z]=p.userData.menuCenter;
        const center=new THREE.Vector3(p.name==='Inspector'?x-.2:x,y,z).applyEuler(pose.rotation);
        const menuWidth=p.userData.panelWidth+(p.name==='Inspector'?.65:0);
        const h=Math.max(p.userData.panelHeight+.95,(menuWidth+.9)/(aspect*.57));
        return {x:center.x+h*aspect*.135,y:center.y,height:h};
      };
      const apply=i=>{
        if(active===i)return;
        transition?.kill();active=i;
        transition=gsap.timeline({onUpdate:projection});
        menus.forEach(p=>{
          if(p.name===sceneMenus[i])return;
          transition.to(p.scale,{x:.001,y:.001,z:.001,duration:.28,ease:'power2.in',onComplete:()=>{p.visible=false;}},0);
        });
        if(i<0){transition.to(view,{x:0,y:0,height:Math.max(8.2,11.4/aspect),duration:.8,ease:'power2.inOut'},.08);return;}
        const p=menus.find(menu=>menu.name===sceneMenus[i]);p.visible=true;p.scale.setScalar(.025);p.position.copy(p.userData.home);
        const content=parts(p);content.forEach(o=>o.scale.setScalar(.001));
        transition.to(p.scale,{x:1,y:1,z:1,duration:.65,ease:'back.out(1.15)'},.12)
          .to(p.position,{y:p.userData.home.y+.20,duration:.65,ease:'power2.out'},.12)
          .to(content.map(o=>o.scale),{x:1,y:1,z:1,duration:.4,stagger:{amount:.16},ease:'power2.out'},.26)
          .to(view,{...menuTarget(p),duration:.85,ease:'power2.inOut'},.2);
        if(curveEntry&&grainEntry){curveEntry.position.copy(orderHome[0]);grainEntry.position.copy(orderHome[1]);}
        if(i===4 && curveEntry && grainEntry){
          transition.to(curveEntry.position,{z:orderHome[1].z,y:.09,duration:.65,ease:'power2.inOut'},1.15)
            .to(grainEntry.position,{z:orderHome[0].z,y:.04,duration:.65,ease:'power2.inOut'},1.15)
            .to(curveEntry.position,{y:0,duration:.25},1.8)
            .to(grainEntry.position,{y:0,duration:.25},1.8);
        }
        document.querySelectorAll('[data-chapter-link]').forEach((a,index)=>a.setAttribute('aria-current',String(index===i)));
        stage.dataset.activeScene=chapters[i].dataset.scene;
        stage.dataset.switcherVisible=String(p.name==='Inspector');
        stage.dataset.activeMenu=p.name;
      };
      const sync=()=>{
        const bounds=document.querySelector('.story').getBoundingClientRect();
        if(bounds.top>innerHeight*.56||bounds.bottom<innerHeight*.3){apply(-1);return;}
        let nearest=0,distance=Infinity;
        chapters.forEach((c,i)=>{const r=c.getBoundingClientRect(),d=Math.abs(r.top+r.height/2-innerHeight/2);if(d<distance){distance=d;nearest=i;}});
        apply(nearest);
      };
      view.height=Math.max(8.2,11.4/aspect);projection();
      let scheduled=false;
      const onScroll=()=>{if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;sync();});};
      window.addEventListener('scroll',onScroll,{passive:true});
      const scroll=ScrollTrigger.create({trigger:'.story',start:'top bottom',end:'bottom top',onUpdate:sync,onRefresh:sync});
      const visibilityObserver=new IntersectionObserver(e=>{visible=e[0].isIntersecting;if(visible)draw();});visibilityObserver.observe(stage);
      document.addEventListener('visibilitychange',draw);
      window.addEventListener('pagehide',()=>{
        disposed=true;window.removeEventListener('scroll',onScroll);transition?.kill();scroll.kill();resizeObserver.disconnect();visibilityObserver.disconnect();
        document.removeEventListener('visibilitychange',draw);appearance.removeEventListener('change',updateAppearance);reflectionMap.dispose();renderer.dispose();
        const geometries=new Set(),materials=new Set();model.traverse(o=>{if(o.isMesh){geometries.add(o.geometry);(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>materials.add(m));}});
        geometryByAppearance.forEach(meshes=>meshes.forEach(g=>geometries.add(g)));geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());
      },{once:true});
      ScrollTrigger.refresh();sync();draw();
    } catch(error){console.warn('3D model unavailable; geometry render retained.',error);stage.querySelector('.model-fallback').style.opacity='1';}
  },{rootMargin:'400px'});
  loadObserver.observe(stage);
}
