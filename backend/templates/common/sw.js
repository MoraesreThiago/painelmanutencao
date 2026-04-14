const CACHE_NAME = "sgm-v1";
const CORE_ASSETS = ["/", "/offline/", "/manifest.webmanifest", "/static/css/app.css", "/static/js/app.js", "/static/js/pwa.js", "{% url 'brand-logo' %}"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
    ),
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    fetch(event.request).catch(async () => {
      const cachedResponse = await caches.match(event.request);
      return cachedResponse || caches.match("/offline/");
    }),
  );
});
