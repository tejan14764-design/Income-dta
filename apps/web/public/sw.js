/**
 * INCOME – Service Worker for PWA offline support.
 * Caches static assets; API calls are network-first.
 * Sensitive data is NEVER stored in the service worker cache.
 */

const CACHE_VERSION = "income-v1";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_BASE = "/api/v1";

// Static assets to pre-cache
const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
];

// Install: pre-cache static assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith("income-") && key !== STATIC_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch: network-first for API, cache-first for static
self.addEventListener("fetch", (event) => {
  const { url, method } = event.request;

  // Never cache API calls or non-GET requests (financial data must always be live)
  if (url.includes(API_BASE) || method !== "GET") {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ success: false, error: "Offline – network unavailable." }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        })
      )
    );
    return;
  }

  // For navigation requests, serve the app shell
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.match("/index.html").then((r) => r || fetch(event.request))
      )
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        // Only cache successful responses for static assets
        if (
          response.ok &&
          !url.includes("chrome-extension") &&
          response.type === "basic"
        ) {
          const clone = response.clone();
          caches.open(STATIC_CACHE).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});
