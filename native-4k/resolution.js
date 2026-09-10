/* Avenzo: native-resolution source selection, no image upscaling operation. */
(() => {
  'use strict';
  const images = Array.from(document.images).filter(img =>
    img.getAttribute('srcset') && img.getAttribute('srcset').includes('/native-4k/')
  );
  if (!images.length) return;
  let pending = false;
  function applyHint(element, rect, fit) {
    const width = Number(element.getAttribute('width'));
    const height = Number(element.getAttribute('height'));
    if (!width || !height || !rect.width || !rect.height) return;
    const needed = fit === 'cover'
      ? Math.max(rect.width, rect.height * width / height)
      : rect.width;
    const hint = `${Math.ceil(needed)}px`;
    if (element.getAttribute('sizes') !== hint) element.setAttribute('sizes', hint);
  }
  function update() {
    pending = false;
    for (const img of images) {
      const rect = img.getBoundingClientRect();
      const fit = getComputedStyle(img).objectFit;
      // Measured native desktop device bounds: y=0.4266..0.7615.
      // At 3840 CSS px the existing 1000px-tall hero crops a 2160px image.
      // A 68% vertical focal point retains the phone instead of cutting its base.
      if (img.classList.contains('architecture')) {
        img.style.objectPosition = window.matchMedia('(min-width:2400px)').matches
          ? 'center 68%' : '';
      }
      applyHint(img, rect, fit);
      if (img.parentElement?.tagName === 'PICTURE') {
        for (const source of img.parentElement.querySelectorAll('source[srcset]')) {
          applyHint(source, rect, fit);
        }
      }
    }
  }
  function schedule() {
    if (!pending) { pending = true; requestAnimationFrame(update); }
  }
  if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(schedule);
    for (const img of images) observer.observe(img);
  }
  window.addEventListener('resize', schedule, { passive: true });
  window.addEventListener('pageshow', schedule, { passive: true });
  update();
})();
