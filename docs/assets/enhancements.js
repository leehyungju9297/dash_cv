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

  // ── Scroll-triggered reveal ──────────────────────────────────────────────────
  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function revealAll() {
    document.querySelectorAll('.reveal-up').forEach(function (el) {
      el.classList.add('is-visible');
    });
  }

  if (prefersReduced) {
    revealAll();
  } else if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var delay = parseInt(el.dataset.revealDelay || '0', 10);
        setTimeout(function () { el.classList.add('is-visible'); }, delay);
        observer.unobserve(el);
      });
    }, { threshold: 0.07, rootMargin: '0px 0px -52px 0px' });

    document.querySelectorAll('.reveal-up').forEach(function (el) {
      // Stagger siblings within the same direct parent
      var parent = el.parentElement;
      var siblings = parent
        ? Array.from(parent.querySelectorAll(':scope > .reveal-up'))
        : [];
      var idx = siblings.indexOf(el);
      if (idx > 0) el.dataset.revealDelay = String(idx * 90);
      observer.observe(el);
    });
  } else {
    revealAll();
  }

  // ── Contact obfuscation ──────────────────────────────────────────────────────
  document.querySelectorAll('[data-obf]').forEach(function (el) {
    try {
      var decoded = atob(el.dataset.obf);
      var type = el.dataset.obfType;
      if (el.tagName === 'A') {
        el.href = (type === 'phone' ? 'tel:' : 'mailto:') + decoded;
      }
      el.textContent = decoded;
    } catch (e) { /* silent fallback */ }
  });

})();
