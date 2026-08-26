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

  // ── Mobile navigation ────────────────────────────────────────────────────────
  // A disclosure, not a drawer: the button owns aria-expanded, the nav gets an
  // `open` class, and both reset whenever the route changes so the menu is never
  // left hanging over the page it just navigated to.
  var navToggle = document.getElementById('nav-toggle');
  var nav = document.getElementById('top-nav');

  function setNav(open) {
    if (!navToggle || !nav) return;
    navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    navToggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    nav.classList.toggle('open', open);
  }

  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      setNav(navToggle.getAttribute('aria-expanded') !== 'true');
    });

    // Any link inside closes it, including the client-side ones that never
    // reload the document.
    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) setNav(false);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && navToggle.getAttribute('aria-expanded') === 'true') {
        setNav(false);
        navToggle.focus();
      }
    });

    // Leaving the mobile breakpoint clears the state, so a menu opened on a
    // phone does not survive a rotation into the desktop layout.
    var wide = window.matchMedia('(min-width: 761px)');
    var onWide = function (event) { if (event.matches) setNav(false); };
    if (wide.addEventListener) wide.addEventListener('change', onWide);
    else if (wide.addListener) wide.addListener(onWide);
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
