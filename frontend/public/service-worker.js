// Served from <base>/service-worker.js, so relative URLs resolve under the
// app's base path (e.g. /routio/) and the worker's scope is that path.
const CACHE_NAME = "routio-cache-v2";
const urlsToCache = [
    "./",
    "./manifest.json"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

// Network first for page navigations so a new deploy is picked up immediately
// (a cached index.html would point at hashed assets that no longer exist);
// fall back to the cached app shell when offline. Other requests (API, hashed
// assets) are left to the browser.
self.addEventListener("fetch", (event) => {
    if (event.request.mode !== "navigate") return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                if (response.ok) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put("./", copy));
                }
                return response;
            })
            .catch(() => caches.match("./"))
    );
});
