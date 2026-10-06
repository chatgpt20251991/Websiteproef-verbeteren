/* Avenzo V2: visible, independent image-layer animation.
   Existing artwork is clipped into moving parts. No generated artwork, native 3D,
   high-resolution master or deployment is implied. No external dependencies. */
(() => {
  'use strict';
  if (window.AvenzoMotionV2) return;
  const NS = 'http://www.w3.org/2000/svg';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const instances = [];
  const listeners = [];
  const clamp = x => Math.max(0, Math.min(1, Number(x) || 0));
  const ease = p => p * p * (3 - 2 * p);
  let serial = 0, raf = 0, previewPlaying = false, frameCount = 0;
  function listen(target, type, fn, opts) {
    target.addEventListener(type, fn, opts);
    listeners.push(() => target.removeEventListener(type, fn, opts));
  }
  function el(name, attrs = {}) {
    const e = document.createElementNS(NS, name);
    Object.entries(attrs).forEach(([key, value]) => e.setAttribute(key, String(value)));
    return e;
  }
  function polygon(points) {
    return points.map(([x, y]) => `${(x * 15.86).toFixed(1)},${(y * 9.92).toFixed(1)}`).join(' ');
  }
  const leftOutline = [[6.1,65.8],[9.1,64.6],[9.1,43.5],[12.7,41.5],[14.9,41.8],[14.9,40.4],[20.7,37.5],[22.9,38.1],[28.5,34.5],[45.6,37.8],[45.9,40.3],[47.9,40.4],[47.9,62.0],[50.7,62.4],[50.7,67.2],[33.6,78.0],[32.2,78.4],[6.1,71.1]];
  const rightOutline = [[62.5,25.2],[64.6,23.7],[88.1,26.8],[89.5,27.9],[90.0,29.5],[90.0,76.3],[91.6,77.3],[91.6,82.1],[89.0,86.0],[86.5,86.1],[60.5,78.9],[60.5,73.8],[62.5,72.1],[62.5,62.6],[60.7,62.2],[60.6,54.5],[61.1,54.0],[60.7,53.0],[60.7,49.0],[61.1,48.4],[60.7,47.0],[60.7,38.8],[61.2,38.0],[62.5,37.2]];
  function makeScene(host, source, { demo = false } = {}) {
    const id = 'av2-' + (++serial);
    const svg = el('svg', {viewBox:'-80 40 1770 880', class:'av2-scene', role:'img', 'aria-label':'Bestaande Avenzo AI-module en bedienpaneel als afzonderlijk bewegende beeldlagen'});
    const defs = el('defs');
    const image = el('image', {id:id+'-image', href:source, width:1586, height:992, preserveAspectRatio:'none'});
    defs.append(image);
    [leftOutline, rightOutline].forEach((points, i) => {
      const clip = el('clipPath', {id:id+'-clip-'+i});
      clip.append(el('polygon', {points:polygon(points)})); defs.append(clip);
    });
    const floor = el('linearGradient', {id:id+'-floor', x1:'0', y1:'0', x2:'0', y2:'1'});
    floor.append(el('stop', {offset:'0', 'stop-color':'#eeeae5', 'stop-opacity':'.1'}), el('stop', {offset:'1', 'stop-color':'#d9d5ce', 'stop-opacity':'.8'}));
    defs.append(floor); svg.append(defs);
    // Neutral backdrop keeps removed objects from appearing twice. No raster upscaling.
    svg.append(el('rect', {x:-80,y:0,width:1770,height:1000,fill:'#e9e5df'}));
    svg.append(el('rect', {x:-80,y:0,width:1770,height:1000,fill:`url(#${id}-floor)`}));
    const shadows = [el('ellipse', {cx:435,cy:771,rx:330,ry:22,fill:'#1e1615',opacity:'.12'}),el('ellipse',{cx:1185,cy:854,rx:238,ry:18,fill:'#1e1615',opacity:'.12'})];
    shadows.forEach(s=>svg.append(s));
    const objects = [];
    for (let i=0;i<2;i++) {
      const g=el('g', {class:i?'av2-panel':'av2-module'});
      const clipped=el('g', {'clip-path':`url(#${id}-clip-${i})`});
      clipped.append(el('use',{href:`#${id}-image`})); g.append(clipped);svg.append(g);objects.push(g);
    }
    const connectors=el('g', {class:'av2-rails', 'aria-hidden':'true'});
    const rails=[];
    for(let i=0;i<3;i++) {
      const shadow=el('path',{fill:'none',stroke:'#19050b','stroke-width':14,'stroke-linecap':'round'});
      const body=el('path',{fill:'none',stroke:'#733044','stroke-width':10,'stroke-linecap':'round'});
      const shine=el('path',{fill:'none',stroke:'#c88792','stroke-width':2,'stroke-linecap':'round'});
      const flow=el('path',{fill:'none',stroke:'#ffe3ce','stroke-width':6,'stroke-dasharray':'36 350','stroke-linecap':'round',opacity:'.9',pathLength:1000});
      connectors.append(shadow,body,shine,flow); rails.push({shadow,body,shine,flow});
    }
    svg.append(connectors);host.append(svg); host.classList.add('av2-layer-host');
    const scene={host,svg,objects,shadows,rails,demo,amount:0,playing:false,started:0,pausedAmount:0};
    instances.push(scene);renderScene(scene,0,0);return scene;
  }
  function rotatePoint(x,y,cx,cy,angle,tx,ty) {
    const r=angle*Math.PI/180, dx=x-cx,dy=y-cy;
    return [cx+dx*Math.cos(r)-dy*Math.sin(r)+tx,cy+dx*Math.sin(r)+dy*Math.cos(r)+ty];
  }
  function renderScene(s, amount, clock=0) {
    const p=ease(clamp(amount));s.amount=clamp(amount);
    const left={x:-100*p,y:-87*p,a:-3.0*p};
    const right={x:120*p,y:-146*p,a:5.0*p};
    s.objects[0].setAttribute('transform',`translate(${left.x.toFixed(2)} ${left.y.toFixed(2)}) rotate(${left.a.toFixed(2)} 430 590)`);
    s.objects[1].setAttribute('transform',`translate(${right.x.toFixed(2)} ${right.y.toFixed(2)}) rotate(${right.a.toFixed(2)} 1220 590)`);
    s.shadows[0].setAttribute('transform',`translate(${left.x} 0) scale(${1-.10*p} 1)`);
    s.shadows[1].setAttribute('transform',`translate(${right.x} 0)`);
    s.shadows.forEach(x=>x.setAttribute('opacity',String(.12-.06*p)));
    const start=[[666,474],[628,524],[631,578]],end=[[963,444],[963,494],[963,549]];
    s.rails.forEach((r,i)=>{
      const a=rotatePoint(...start[i],430,590,left.a,left.x,left.y);
      const b=rotatePoint(...end[i],1220,590,right.a,right.x,right.y);
      const mid=(a[0]+b[0])/2;
      const d=`M ${a[0]} ${a[1]} C ${mid-24} ${a[1]+28},${mid-32} ${a[1]+30},${mid+24} ${a[1]+12} L ${b[0]} ${b[1]}`;
      [r.shadow,r.body,r.shine,r.flow].forEach(line=>line.setAttribute('d',d));
      r.flow.setAttribute('stroke-dashoffset',String(-((clock*.19+i*115+p*300)%1000)));
      r.flow.setAttribute('opacity',String(.25+.65*p));
    });
    if (s===focused) {
      slider.value=String(Math.round(s.amount*100));
      percentage.textContent=Math.round(s.amount*100)+'%';
      const label=p<.3?'01 / Modules bij elkaar':p<.75?'02 / Onderdelen bewegen los':'03 / Verbindingen bewegen mee';
      phase.textContent=label;
    }
  }
  let focused=null, slider=null, percentage=null, phase=null, playButton=null, status=null, preview=null, backButton=null;
  let previewStarted=0, previewOffset=0;
  function updateControl() {
    if(!playButton)return;
    playButton.textContent=previewPlaying?'Ⅱ  Pauzeren':'▶  Speel animatie';
    playButton.setAttribute('aria-pressed',String(previewPlaying));
    status.textContent=previewPlaying?'Animatie speelt':reduced.matches?'Automatisch uit: minder beweging ingesteld':'Gepauzeerd · sleep de balk';
    preview.classList.toggle('av2-is-playing',previewPlaying);
  }
  function request() {if(!raf&&!document.hidden)raf=requestAnimationFrame(tick);}
  function tick(now) {
    raf=0;if(document.hidden)return;
    let again=false;
    const full=document.body.classList.contains('av2-site-mode');
    instances.forEach(s=>{
      if(s.demo){
        if(previewPlaying&&!full){
          const t=(now-previewStarted+previewOffset)%10000;
          const amount=(1-Math.cos(t/10000*Math.PI*2))/2;
          renderScene(s,amount,t);again=true;
        }
      }else if(!reduced.matches&&!document.documentElement.classList.contains('av-motion-disabled')){
        const r=s.host.getBoundingClientRect();
        if(r.bottom>0&&r.top<innerHeight){
          // Full-size obvious separation at the middle of the viewport; native scrolling stays intact.
          const p=clamp((innerHeight*.94-r.top)/Math.max(1,innerHeight*.9));
          renderScene(s,p,scrollY*.9);
        }
      }
    });
    frameCount++;if(again)request();
  }
  function play(){
    if(!focused)return;
    previewPlaying=true;previewOffset=Math.acos(1-2*clamp(focused.amount))/(Math.PI*2)*10000;
    previewStarted=performance.now();updateControl();request();
  }
  function pause(){previewPlaying=false;updateControl();}
  function createPreview(source) {
    preview=document.createElement('section');preview.id='av2-preview';
    preview.setAttribute('aria-label','Avenzo bewegingspreview, niet live');
    preview.innerHTML=`<div class="av2-demo-top"><div><span class="av2-label">AVENZO DIGITAL / MOTION V2</span><h1>Nu bewegen de onderdelen.</h1><p>Jouw bestaande AI-beeld. De module en het paneel bewegen afzonderlijk.</p></div><button class="av2-site-button" type="button">Bekijk volledige homepage ↗</button></div><div class="av2-demo-frame"><div class="av2-stage-top"><span class="av2-phase">01 / Modules bij elkaar</span><span class="av2-dot-status"><i aria-hidden="true"></i><span class="av2-status">Animatie laden…</span></span></div><div class="av2-demo-stage"></div><div class="av2-controls"><button class="av2-play" type="button" aria-pressed="false">▶ Speel animatie</button><label for="av2-range">Beweeg zelf</label><input id="av2-range" type="range" min="0" max="100" step="1" value="0" aria-label="Onderdelen uit elkaar bewegen"><output class="av2-percentage" for="av2-range">0%</output></div></div><p class="av2-note">Interactieve preview, niet live. Beeldlagen uit de bestaande illustratie, geen nieuw 3D-model of 4K-bron.</p>`;
    document.body.prepend(preview);document.body.classList.add('av2-focus-mode');
    slider=preview.querySelector('input');percentage=preview.querySelector('output');phase=preview.querySelector('.av2-phase');playButton=preview.querySelector('.av2-play');status=preview.querySelector('.av2-status');
    focused=makeScene(preview.querySelector('.av2-demo-stage'),source,{demo:true});
    listen(playButton,'click',()=>previewPlaying?pause():play());
    listen(slider,'input',()=>{pause();renderScene(focused,Number(slider.value)/100,Number(slider.value)*70)});
    backButton=document.createElement('button');backButton.className='av2-back';backButton.type='button';backButton.textContent='↖ Terug naar bewegingsdemo';backButton.hidden=true;document.body.append(backButton);
    listen(preview.querySelector('.av2-site-button'),'click',()=>{
      pause();document.body.classList.remove('av2-focus-mode');document.body.classList.add('av2-site-mode');preview.hidden=true;backButton.hidden=false;window.scrollTo({top:0,behavior:'instant'});window.dispatchEvent(new Event('resize'));request();
    });
    listen(backButton,'click',()=>{
      document.body.classList.remove('av2-site-mode');document.body.classList.add('av2-focus-mode');preview.hidden=false;backButton.hidden=true;window.scrollTo({top:0,behavior:'instant'});playButton.focus({preventScroll:true});if(!reduced.matches)play();
    });
    if(!reduced.matches){renderScene(focused,.2,0);play();}else updateControl();
  }
  const image=document.querySelector('.precision-art img[data-av-original-src*="service-ai"],.precision-art img[src*="service-ai"]');
  if(image){
    const source=image.currentSrc||image.src;
    const host=image.closest('.precision-art');
    const scene=makeScene(host,source);
    image.classList.add('av2-original-hidden');
    if(document.querySelector('meta[name="avenzo-preview"]'))createPreview(source);
  }
  listen(window,'scroll',request,{passive:true});listen(window,'resize',request,{passive:true});listen(document,'click',request,{passive:true});
  listen(reduced,'change',()=>{
    pause();instances.filter(s=>!s.demo).forEach(s=>renderScene(s,0,0));request();
  });
  listen(document,'visibilitychange',()=>{
    if(document.hidden){pause();if(raf)cancelAnimationFrame(raf);raf=0;}else request();
  });
  window.AvenzoMotionV2={
    version:'2.0.0',play,pause,
    seek(value){pause();if(focused)renderScene(focused,clamp(value),clamp(value)*10000);},
    getState:()=>({version:'2.0.0',previewPlaying,reduced:reduced.matches,sceneCount:instances.length,amount:focused?.amount||0,frames:frameCount,renderer:'independent SVG-clipped image layers; not native 3D'}),
    destroy(){pause();if(raf)cancelAnimationFrame(raf);listeners.forEach(f=>f());instances.forEach(s=>{s.svg.remove();s.host.classList.remove('av2-layer-host')});document.querySelectorAll('.av2-original-hidden').forEach(e=>e.classList.remove('av2-original-hidden'));preview?.remove();backButton?.remove();document.body.classList.remove('av2-focus-mode','av2-site-mode');delete window.AvenzoMotionV2;}
  };
  request();
})();
