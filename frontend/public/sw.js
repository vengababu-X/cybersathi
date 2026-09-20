// Offline cache so the knowledge base, quiz and fonts stay readable in a village hall with
// no connectivity. Network-first for the cacheable API resources, cache-first for the shell.
//
// Deliberate exclusion: the detection endpoints (/api/v1/scam, /url, /assistant) are never
// cached. A stale risk verdict is worse than an honest "you are offline".
const CACHE = 'cybersathi-v2';
const SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
  '/shield.svg',
  '/icon-192.png',
  '/fonts/fonts.css',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches
      .open(CACHE)
      // A single missing file must not fail the whole install.
      .then((c) => Promise.all(SHELL.map((url) => c.add(url).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Knowledge base / quiz / helplines are worth keeping offline.
function isCacheableApi(pathname) {
  return (
    pathname.startsWith('/api/v1/kb') ||
    pathname.startsWith('/api/v1/qr/scenarios') ||
    pathname.startsWith('/api/v1/meta/helplines')
  );
}

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Anything cross-origin (an outbound link, an embedded image) is left alone.
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/')) {
    if (!isCacheableApi(url.pathname)) return;
    event.respondWith(
      fetch(request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(request, copy));
          return res;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // A page navigation: prefer the network so a deploy is picked up, fall back to the shell.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/index.html').then((r) => r || caches.match('/')))
    );
    return;
  }

  // Static assets (hashed JS/CSS from /assets/, fonts, icons): serve from cache when we have
  // it, and populate the cache the first time each file is fetched. Without this the app
  // shell would load offline but its JS bundle would not.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((res) => {
        if (res.ok && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(request, copy));
        }
        return res;
      });
    })
  );
});
