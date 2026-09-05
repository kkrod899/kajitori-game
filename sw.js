const CACHE_NAME = "kajitori-shell-v3";
const APP_SHELL = [
  "./",
  "./index.html",
  "./kajitori_minimal_pictogram_compact.html",
  "./kajitori_v03.css",
  "./kajitori_v03_core.js",
  "./kajitori_v03_actions.js",
  "./kajitori_v03_ui.js",
  "./manifest.webmanifest",
  "./icons/icon.svg",
  "./icons/icon-180.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            event.waitUntil(
              caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()))
            );
          }
          return response;
        })
        .catch(() => caches.match(request).then((cached) => {
          return cached || caches.match("./kajitori_minimal_pictogram_compact.html");
        }))
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          event.waitUntil(
            caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()))
          );
        }
        return response;
      })
      .catch(() => caches.match(request))
  );
});
