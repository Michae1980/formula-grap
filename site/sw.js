const CACHE_NAME = "formula-graph-pwa-v2";
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./data/graph-data.js",
  "./manifest.webmanifest",
  "./icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  const isSameOrigin = url.origin === self.location.origin;
  const isKatexCdn = url.hostname === "cdn.jsdelivr.net" && url.pathname.includes("/katex@");

  if (!isSameOrigin && !isKatexCdn) return;

  // 同源页面与 KaTeX 资源使用 Stale-While-Revalidate：秒开离线可用，联网时后台静默更新
  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(req);
      const networkFetch = fetch(req)
        .then((resp) => {
          if (resp && (resp.ok || resp.type === "opaque")) {
            cache.put(req, resp.clone());
          }
          return resp;
        })
        .catch(() => null);

      if (cached) {
        event.waitUntil(networkFetch);
        return cached;
      }
      const fresh = await networkFetch;
      if (fresh) return fresh;
      if (req.mode === "navigate") {
        return cache.match("./index.html");
      }
      return new Response("Offline", { status: 503, statusText: "Offline" });
    })
  );
});
