(function () {
  var ATTR = 'data-track';

  function cleanPayload(payload) {
    var out = {};
    Object.keys(payload).forEach(function (key) {
      if (payload[key] !== undefined && payload[key] !== null && payload[key] !== '') {
        out[key] = payload[key];
      }
    });
    return out;
  }

  function track(eventName, payload) {
    try {
      if (typeof window.gtag === 'function') {
        window.gtag('event', eventName, payload);
      }
      if (typeof window.plausible === 'function') {
        window.plausible(eventName, { props: payload });
      }
      if (window.fathom && typeof window.fathom.trackEvent === 'function') {
        window.fathom.trackEvent(eventName, payload);
      }
    } catch (err) {
      // Intentionally silent to avoid impacting UX.
    }
  }

  document.addEventListener(
    'click',
    function (event) {
      var target = event.target instanceof Element ? event.target.closest('[' + ATTR + ']') : null;
      if (!target) {
        return;
      }

      var eventName = target.getAttribute(ATTR);
      if (!eventName) {
        return;
      }

      var payload = cleanPayload({
        location: target.getAttribute('data-track-location'),
        label: target.getAttribute('data-track-label'),
        href: target.getAttribute('href'),
      });

      track(eventName, payload);
    },
    { passive: true }
  );
})();
