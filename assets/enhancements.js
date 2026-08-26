(function () {
  'use strict';

  // ── Scroll progress bar ──────────────────────────────────────────────────────
  var progressBar = document.getElementById('scroll-progress');
  if (progressBar) {
    function updateProgress() {
      var scrollTop = window.scrollY;
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      progressBar.style.width = (docHeight > 0 ? (scrollTop / docHeight) * 100 : 0) + '%';
    }
    window.addEventListener('scroll', updateProgress, { passive: true });
  }

  // ── Back-to-top ──────────────────────────────────────────────────────────────
  var btt = document.getElementById('back-to-top');
  if (btt) {
    window.addEventListener('scroll', function () {
      btt.classList.toggle('visible', window.scrollY > 380);
    }, { passive: true });
    btt.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ── Contact obfuscation ──────────────────────────────────────────────────────
  // Re-run on DOM changes: the Dash build swaps page content client-side, so
  // anything that only ran at first paint would miss every later route.
  function deobfuscate(root) {
    (root || document).querySelectorAll('[data-obf]').forEach(function (el) {
      try {
        var decoded = atob(el.dataset.obf);
        el.removeAttribute('data-obf');
        if (el.tagName === 'A') {
          el.href = (el.dataset.obfType === 'phone' ? 'tel:' : 'mailto:') + decoded;
        }
        el.textContent = decoded;
      } catch (e) { /* silent fallback */ }
    });
  }

  deobfuscate();
  if (window.MutationObserver) {
    new MutationObserver(function () { deobfuscate(); })
      .observe(document.body, { childList: true, subtree: true });
  }

})();
