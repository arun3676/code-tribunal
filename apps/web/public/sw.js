const CACHE_NAME = "tribunal-v2";
const PRECACHE_URLS = ["/", "/council", "/tribunal", "/about"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  // Only handle GET requests — never cache POSTs (verdict submissions etc.)
  if (event.request.method !== "GET") return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache only successful same-origin responses — never error pages,
        // never the cross-origin API (health polls would churn the cache).
        const sameOrigin = new URL(event.request.url).origin === self.location.origin;
        if (response.ok && sameOrigin) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() =>
        // Network failure: try cache, then fall back to root shell
        caches
          .match(event.request)
          .then((cached) => cached || caches.match("/"))
      )
  );
});
