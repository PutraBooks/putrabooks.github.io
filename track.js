/* PutraBooks storefront analytics beacon.
 * One row per page view, per outbound store click and per sample download.
 * No cookies, no fingerprinting, no IP stored. Loaded with <script src="/track.js" defer>.
 */
(function () {
  if (location.protocol === 'file:') return;
  var EP = 'https://superagent-4eace1ae.base44.app/functions/trackSiteEvent';
  if (!EP) return;

  var q = new URLSearchParams(location.search);
  var p = location.pathname.replace(/index\.html?$/, '');
  var pageType = p.indexOf('/books/') === 0 ? 'book'
    : p.indexOf('/series/') === 0 ? 'series'
    : p === '/' ? 'home' : 'store';

  // No screen size, no user agent, no cookie, no IP: page, referrer and campaign only.
  var base = {
    p: location.pathname,
    t: pageType,
    r: document.referrer ? (function () { try { return new URL(document.referrer).hostname; } catch (e) { return ''; } })() : '',
    u: q.get('utm_source') || '',
    m: q.get('utm_campaign') || ''
  };

  function send(o) {
    var body = JSON.stringify(o);
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(EP, new Blob([body], { type: 'text/plain' }));
      } else {
        fetch(EP, { method: 'POST', body: body, headers: { 'Content-Type': 'text/plain' }, keepalive: true });
      }
    } catch (e) { /* analytics must never break a page */ }
  }

  function channelFor(href) {
    if (href.indexOf('/samples/') !== -1 && /\.pdf$/i.test(href)) return 'sample';
    var h;
    try { h = new URL(href, location.href).hostname; } catch (e) { return ''; }
    if (/payhip/.test(h)) return 'payhip';
    if (/ko-fi/.test(h)) return 'kofi';
    if (/carousell/.test(h)) return 'carousell';
    if (/elevenreader|elevenlabs/.test(h)) return 'elevenreader';
    if (/gumroad/.test(h)) return 'gumroad';
    if (/fourthwall/.test(h)) return 'fourthwall';
    if (/itch\.io/.test(h)) return 'itch';
    if (/esentral/.test(h)) return 'esentral';
    if (/amazon|amzn/.test(h)) return 'amazon';
    return '';
  }

  send(Object.assign({ e: 'view' }, base));

  document.addEventListener('click', function (ev) {
    var el = ev.target;
    while (el && el.tagName !== 'A') el = el.parentElement;
    if (!el || !el.href) return;
    var ch = channelFor(el.href);
    if (!ch) return;
    send(Object.assign({ e: ch === 'sample' ? 'sample' : 'click', c: ch }, base));
  }, true);
})();
