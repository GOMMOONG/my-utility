// 최소한의 서비스 워커 — PWA 설치 요건 충족용
// 오프라인 캐싱은 없음 (Streamlit은 서버 연결이 필수)

self.addEventListener('install', function(event) {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', function(event) {
  event.respondWith(fetch(event.request));
});
