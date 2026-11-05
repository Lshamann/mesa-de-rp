/* Ponte para o tradutor offline (bergamot-translator, MPL-2.0). Carrega o worker e o wasm publicados no npm via jsDelivr. */
const CDN = "https://cdn.jsdelivr.net/npm/@browsermt/bergamot-translator@0.4.9/worker/";
const _fetch = self.fetch.bind(self);
self.fetch = (url, opts) => { const u = String((url && url.url) || url); return _fetch(/bergamot-translator-worker\.wasm$/.test(u) ? CDN + "bergamot-translator-worker.wasm" : url, opts); };
const _imp = self.importScripts.bind(self);
self.importScripts = (...s) => _imp(...s.map(x => /^(https?:|blob:|data:)/.test(String(x)) ? x : CDN + String(x).replace(/^\.?\//, "")));
_imp(CDN + "translator-worker.js");
