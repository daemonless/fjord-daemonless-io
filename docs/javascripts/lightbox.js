// Lightbox initialization for .glightbox elements.
// Hooks into window.document$ for Zensical instant navigation SPA updates.
function initLightbox() {
  if (typeof GLightbox !== 'undefined') {
    GLightbox({ selector: '.glightbox' });
  }
}

if (window.document$ && window.document$.subscribe) {
  window.document$.subscribe(initLightbox);
} else if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLightbox);
} else {
  initLightbox();
}
