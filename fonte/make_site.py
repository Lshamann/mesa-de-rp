import os
BASE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE, 'saida'), exist_ok=True)
import os, json, shutil
from playwright.sync_api import sync_playwright
OUT=os.path.dirname(BASE); os.makedirs(OUT, exist_ok=True)
frag=open(os.path.join(BASE, 'saida', 'mesa_rp.html'),encoding='utf8').read()
reset=':root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#0f1511;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}'
head=('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
 '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
 '<meta name="theme-color" content="#0f1511"><meta name="description" content="Roleplay plug-and-play com personagens, lorebook e memória.">'
 '<link rel="manifest" href="manifest.webmanifest"><link rel="icon" href="icon-192.png"><link rel="apple-touch-icon" href="icon-192.png">'
 '<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Mesa de RP">'
 '<style>'+reset+'</style></head><body>\n')
open(OUT+'/index.html','w',encoding='utf8').write(head+frag+'\n</body></html>')
json.dump({"name":"Mesa de RP","short_name":"Mesa de RP","description":"Roleplay plug-and-play com personagens, lorebook e memória.",
  "lang":"pt-BR","start_url":"./","scope":"./","display":"standalone","orientation":"portrait",
  "background_color":"#0f1511","theme_color":"#0f1511",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png","purpose":"any"},
           {"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any"},
           {"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]},
  open(OUT+'/manifest.webmanifest','w',encoding='utf8'), ensure_ascii=False, indent=1)
open(OUT+'/sw.js','w').write('''const C = "mesa-rp-v2";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./bergamot-worker.js"];
self.addEventListener("install", e => { e.waitUntil(caches.open(C).then(c => c.addAll(CORE))); self.skipWaiting(); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== C).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url); const same = u.origin === location.origin; const font = /(^|\\.)fonts\\.(googleapis|gstatic)\\.com$/.test(u.hostname) || (u.hostname === "cdn.jsdelivr.net" && u.pathname.includes("bergamot-translator"));
  if (!same && !font) return;
  if (same && r.mode === "navigate") {
    e.respondWith(fetch(r).then(res => { const cp = res.clone(); caches.open(C).then(c => c.put("./index.html", cp)); return res; }).catch(() => caches.match("./index.html")));
    return;
  }
  e.respondWith(caches.match(r).then(hit => hit || fetch(r).then(res => { if (res.ok || res.type === "opaque") { const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); } return res; })));
});
''')
open(OUT+'/bergamot-worker.js','w').write('''/* Ponte para o tradutor offline (bergamot-translator, MPL-2.0). Carrega o worker e o wasm publicados no npm via jsDelivr. */
const CDN = "https://cdn.jsdelivr.net/npm/@browsermt/bergamot-translator@0.4.9/worker/";
const _fetch = self.fetch.bind(self);
self.fetch = (url, opts) => { const u = String((url && url.url) || url); return _fetch(/bergamot-translator-worker\\.wasm$/.test(u) ? CDN + "bergamot-translator-worker.wasm" : url, opts); };
const _imp = self.importScripts.bind(self);
self.importScripts = (...s) => _imp(...s.map(x => /^(https?:|blob:|data:)/.test(String(x)) ? x : CDN + String(x).replace(/^\\.?\\//, "")));
_imp(CDN + "translator-worker.js");
''')
open(OUT+'/.nojekyll','w').write('')
svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" fill="#0f1511"/>
<g transform="translate(256 256) scale(9) translate(-16 -16)" color="#53b9ad"><rect x="3" y="3" width="26" height="26" rx="7" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="10.5" cy="10.5" r="2" fill="currentColor"/><circle cx="16" cy="16" r="2" fill="currentColor"/><circle cx="21.5" cy="21.5" r="2" fill="currentColor"/><circle cx="21.5" cy="10.5" r="2" fill="#d9a04f"/><circle cx="10.5" cy="21.5" r="2" fill="#d9a04f"/></g></svg>'''
with sync_playwright() as p:
    b=p.chromium.launch()
    for n in (192,512):
        pg=b.new_page(viewport={'width':n,'height':n})
        pg.set_content('<html><body style="margin:0">'+svg.replace('<svg ','<svg width="%d" height="%d" '%(n,n))+'</body></html>')
        pg.screenshot(path=OUT+'/icon-%d.png'%n); pg.close()
    b.close()
print(sorted(os.listdir(OUT)))
