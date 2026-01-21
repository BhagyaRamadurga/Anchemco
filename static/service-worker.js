self.addEventListener('install', (e) => {
    console.log('[Service Worker] Install');
});
self.addEventListener('fetch', (e) => {
    // Basic pass-through
    e.respondWith(fetch(e.request));
});
