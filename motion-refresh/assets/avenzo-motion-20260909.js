/* Avenzo Digital | Motion enhancement 1.0.0
 * Native scrolling; no analytics, cookies, network requests or scroll hijacking.
 * Raster scenes remain raster scenes: this is 2.5D camera motion, not rigged 3D.
 */
(() => {
  'use strict';
  if (window.AvenzoMotion) return;
  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const compact = matchMedia('(max-width: 760px)');
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const q = (s, el = document) => Array.from(el.querySelectorAll(s));
  const cleanups = [];
  let enabled = false, frame = 0, lastTime = 0, lastY = scrollY, framesRendered = 0;
  let manualOff = false;
  try { manualOff = sessionStorage.getItem('avenzo.motion.off') === '1'; } catch (_) {}
  const listen = (el, event, fn, options) => {
    el.addEventListener(event, fn, options);
    cleanups.push(() => el.removeEventListener(event, fn, options));
  };
  const progress = document.createElement('div');
  progress.className = 'av-scroll-progress';
  progress.setAttribute('aria-hidden', 'true');
  document.body.append(progress);
  const control = document.createElement('button');
  control.type = 'button'; control.className = 'av-motion-control';
  control.setAttribute('aria-label', 'Decoratieve beweging');
  (document.querySelector('.av-footer__inner') || document.querySelector('.site-footer') || document.body).append(control);
  const visuals = [];
  const hosts = q('.hero-picture, .precision-art, .software-visual');
  q('img.detail-art').forEach(img => {
    const wrapper = document.createElement('div'); wrapper.className = 'av-detail-visual';
    img.before(wrapper); wrapper.append(img); hosts.push(wrapper);
  });
  const storyGroups = [];
  q('.working-section').forEach(section => {
    const intro = section.querySelector(':scope > div');
    const steps = q(':scope > ol > li', section);
    if (!intro || !steps.length) return;
    section.classList.add('av-story');
    const meter = document.createElement('div'); meter.className = 'av-story-meter';
    meter.setAttribute('aria-hidden', 'true'); meter.innerHTML = '<span></span>';
    intro.append(meter);
    if (document.body.classList.contains('home')) {
      const original = document.querySelector('.software-visual img');
      if (original) {
        const figure = document.createElement('div'); figure.className = 'av-story-visual';
        figure.setAttribute('aria-hidden', 'true');
        const copy = original.cloneNode(true); copy.alt = ''; copy.loading = 'lazy';
        copy.sizes = '(min-width: 1920px) 620px, (min-width: 1100px) 40vw, 100vw';
        figure.append(copy); intro.append(figure); hosts.push(figure);
      }
    }
    storyGroups.push({ section, intro, steps, meter: meter.firstElementChild });
  });
  function addFlow(host, image) {
    if (!/service-ai-/.test(image.getAttribute('data-av-original-src') || image.getAttribute('src') || '')) return null;
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 960 600');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');
    svg.setAttribute('aria-hidden', 'true'); svg.classList.add('av-data-flow');
    [
      'M 400 285 L 465 298 Q 478 302 495 296 L 582 271',
      'M 400 315 L 464 331 Q 478 335 494 329 L 582 301',
      'M 400 347 L 464 362 Q 478 367 494 361 L 582 334'
    ].forEach((d, i) => {
      const line = document.createElementNS(ns, 'path'); line.setAttribute('d', d);
      line.setAttribute('pathLength', '100'); line.setAttribute('fill', 'none');
      line.setAttribute('stroke-dasharray', '10 100'); svg.append(line);
    });
    host.append(svg);
    return q('path', svg);
  }
  hosts.forEach(host => {
    const image = host.querySelector('img'); if (!image) return;
    host.classList.add('av-motion-visual'); image.classList.add('av-motion-image');
    const glow = document.createElement('span'); glow.className = 'av-light';
    glow.setAttribute('aria-hidden', 'true');
    // picture content model is source/img only; decorate its outer section instead.
    if (host.tagName !== 'PICTURE') host.append(glow);
    const v = { host, image, glow, hero: host.classList.contains('hero-picture'),
      flow: addFlow(host, image), x: 0, y: 0, tx: 0, ty: 0, active: false, seen: false };
    visuals.push(v);
    listen(v.hero ? host.closest('.home-hero') : host, 'pointermove', event => {
      if (!enabled || !fine.matches || event.pointerType === 'touch') return;
      const r = host.getBoundingClientRect();
      v.tx = clamp((event.clientX - r.left) / r.width, 0, 1) * 2 - 1;
      v.ty = clamp((event.clientY - r.top) / r.height, 0, 1) * 2 - 1;
      v.active = true; request();
    }, { passive: true });
    listen(v.hero ? host.closest('.home-hero') : host, 'pointerleave', () => { v.tx = 0; v.ty = 0; v.active = false; request(); }, { passive: true });
  });
  const headings = q('.hero-copy h1 > span');
  const reveal = q('.section-intro, .precision-service, .software-copy > *, .av-footer__intro > *, .av-footer__detail, .av-footer__brand-row, .service-body .section-heading, .applications > *, .faq-section > div:first-child, .studio-statement > *, .related > h2');
  let observer;
  function show(el) { el.classList.remove('av-reveal-wait'); el.classList.add('av-revealed'); }
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        show(entry.target); observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -4% 0px', threshold: 0.06 });
  }
  function setReveal() {
    if (observer) observer.disconnect();
    reveal.forEach((el, i) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty('--av-delay', `${el.matches('.precision-service') ? (i % 3) * 55 : 0}ms`);
      // Never hide above-the-fold content, focused elements, hash targets or content without IO.
      if (enabled && observer && r.top >= innerHeight && !el.contains(document.activeElement)) {
        el.classList.add('av-reveal-wait'); observer.observe(el);
      } else show(el);
    });
  }
  function request() {
    if (!enabled || document.hidden || frame) return;
    frame = requestAnimationFrame(render);
  }
  function render(now) {
    frame = 0;
    if (!enabled || document.hidden) return;
    const dt = Math.min(50, now - (lastTime || now - 16.7)); lastTime = now;
    const ease = 1 - Math.exp(-dt / 75);
    const y = scrollY, vh = innerHeight;
    const height = document.documentElement.scrollHeight - vh;
    const docP = height > 0 ? clamp(y / height) : 0;
    lastY = y;
    // Read geometry first, write all transforms afterwards.
    const boxes = visuals.map(v => v.host.getBoundingClientRect());
    const stories = storyGroups.map(g => ({ g, rect: g.section.getBoundingClientRect(),
      introHeight: g.intro.getBoundingClientRect().height,
      steps: g.steps.map(s => s.getBoundingClientRect()) }));
    const hero = document.querySelector('.home-hero');
    const heroRect = hero ? hero.getBoundingClientRect() : null;
    progress.style.transform = `scaleX(${docP.toFixed(5)})`;
    let settling = false;
    visuals.forEach((v, i) => {
      const r = boxes[i];
      if (r.bottom < -50 || r.top > vh + 50 || !r.height) { v.host.classList.remove('av-in-view'); return; }
      v.host.classList.add('av-in-view');
      v.x = lerp(v.x, fine.matches ? v.tx : 0, ease);
      v.y = lerp(v.y, fine.matches ? v.ty : 0, ease);
      if (Math.abs(v.x - v.tx) + Math.abs(v.y - v.ty) > .006 && fine.matches) settling = true;
      const p = clamp((vh - r.top) / (vh + r.height));
      const travel = compact.matches ? 3 : (v.hero ? 13 : 7);
      const shift = (p - .5) * travel * 2;
      const rx = v.hero ? 0 : -v.y * (compact.matches ? 0 : 1.9);
      const ry = v.hero ? 0 : v.x * (compact.matches ? 0 : 2.6);
      // Existing image is preserved. A small overscan covers parallax edges, never a big zoom.
      const scale = v.hero ? 1.025 : 1.045;
      const transform = `perspective(1400px) translate3d(${(v.x * (v.hero ? 3 : 4)).toFixed(2)}px,${shift.toFixed(2)}px,0) rotateX(${rx.toFixed(3)}deg) rotateY(${ry.toFixed(3)}deg) scale(${scale})`;
      v.image.style.transform = transform;
      if (v.flow) {
        const svg = v.host.querySelector('.av-data-flow'); svg.style.transform = transform;
        v.flow.forEach((line, index) => {
          const phase = (p * 2.8 + index * .27 + v.x * .06) % 1;
          line.style.strokeDashoffset = String(-phase * 100);
          line.style.opacity = String(Math.sin(phase * Math.PI) * .85);
        });
      }
      v.glow.style.opacity = v.active ? '.16' : '0';
      v.glow.style.transform = `translate3d(${(v.x * 22).toFixed(2)}%,${(v.y * 16).toFixed(2)}%,0)`;
    });
    if (heroRect) {
      const p = clamp(-heroRect.top / Math.max(heroRect.height, 1));
      headings.forEach((h, i) => {
        h.style.transform = `translate3d(${((i ? -1 : 1) * p * (compact.matches ? 4 : 18)).toFixed(2)}px,${(p * 9).toFixed(2)}px,0)`;
      });
    }
    stories.forEach(({ g, rect, introHeight, steps }) => {
      const p = clamp((vh * .65 - rect.top) / Math.max(1, rect.height - vh * .25));
      g.meter.style.transform = `scaleX(${p.toFixed(5)})`;
      g.section.classList.toggle('av-sticky-safe', !compact.matches && introHeight < vh - 130);
      let best = 0, distance = Infinity;
      steps.forEach((r, index) => {
        const d = Math.abs(r.top + r.height * .35 - vh * .53);
        if (d < distance) { distance = d; best = index; }
      });
      g.steps.forEach((step, index) => step.classList.toggle('av-step-active', index === best));
    });
    framesRendered++;
    if (settling) request();
  }
  function reset() {
    if (frame) cancelAnimationFrame(frame); frame = 0; lastTime = 0;
    visuals.forEach(v => {
      v.x = v.y = v.tx = v.ty = 0; v.active = false;
      v.image.style.removeProperty('transform'); v.host.classList.remove('av-in-view');
      v.glow.style.opacity = '0';
      if (v.flow) v.host.querySelector('.av-data-flow').style.removeProperty('transform');
    });
    headings.forEach(h => h.style.removeProperty('transform'));
    storyGroups.forEach(g => g.section.classList.remove('av-sticky-safe'));
  }
  function refreshPreference() {
    enabled = !reduced.matches && !manualOff;
    root.classList.toggle('av-motion-enabled', enabled);
    root.classList.toggle('av-motion-disabled', !enabled);
    root.dataset.avenzoMotion = '20260909';
    control.setAttribute('aria-pressed', String(enabled));
    control.textContent = reduced.matches ? 'Beweging uit · systeeminstelling' : `Beweging ${enabled ? 'aan' : 'uit'}`;
    control.disabled = reduced.matches;
    if (!enabled) reset();
    setReveal(); request();
  }
  listen(control, 'click', () => {
    manualOff = !manualOff;
    try { sessionStorage.setItem('avenzo.motion.off', manualOff ? '1' : '0'); } catch (_) {}
    refreshPreference();
  });
  listen(reduced, 'change', refreshPreference);
  listen(fine, 'change', () => { visuals.forEach(v => { v.tx = v.ty = 0; }); request(); });
  listen(window, 'scroll', request, { passive: true });
  listen(window, 'resize', request, { passive: true });
  listen(window, 'pageshow', () => { setReveal(); request(); });
  listen(document, 'visibilitychange', () => {
    if (document.hidden) { if (frame) cancelAnimationFrame(frame); frame = 0; lastTime = 0; }
    else request();
  });
  listen(document, 'focusin', event => {
    reveal.filter(el => el.contains(event.target)).forEach(show); request();
  });
  listen(document, 'toggle', request, true);
  q('img').forEach(img => listen(img, 'load', request, { once: true }));
  let resize;
  if ('ResizeObserver' in window) { resize = new ResizeObserver(request); resize.observe(document.body); }
  window.AvenzoMotion = Object.freeze({
    version: '1.0.0',
    getState: () => ({ enabled, reduced: reduced.matches, framesRendered, visualCount: visuals.length,
      storyCount: storyGroups.length, renderer: 'CSS 2.5D with SVG data paths', native3D: false }),
    pause: () => { manualOff = true; refreshPreference(); },
    resume: () => { manualOff = false; refreshPreference(); },
    destroy: () => {
      manualOff = true; refreshPreference(); cleanups.forEach(fn => fn());
      observer?.disconnect(); resize?.disconnect(); progress.remove(); control.remove();
      document.querySelectorAll('.av-light,.av-data-flow,.av-story-meter,.av-story-visual').forEach(el => el.remove());
      visuals.forEach(v => v.host.classList.remove('av-motion-visual','av-in-view'));
      document.querySelectorAll('.av-motion-image').forEach(el => el.classList.remove('av-motion-image'));
      document.querySelectorAll('.av-detail-visual').forEach(el => el.replaceWith(...el.childNodes));
      storyGroups.forEach(g => g.section.classList.remove('av-story','av-sticky-safe'));
      root.classList.remove('av-motion-enabled','av-motion-disabled');
      delete root.dataset.avenzoMotion; delete window.AvenzoMotion;
    }
  });
  refreshPreference();
})();
