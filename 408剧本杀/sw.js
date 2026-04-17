// 408 · 墨语之卷之谜 Service Worker
const CACHE = 'exam-408-v5';
const ASSETS = [
  './',
  './408剧本杀.html',
  './manifest.json',
  './icon.svg',
  './icon-192.png',
  './icon-512.png',
  './data/boot.js',
  './data/rooms.js',
  './data/engine.js',
  './data/game.js',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  e.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req).then(resp => {
        if (resp && resp.ok && resp.type === 'basic') {
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return resp;
      }).catch(() => caches.match('./408剧本杀.html'));
    })
  );
});
