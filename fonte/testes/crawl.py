# Auditoria: clica em cada botão visível, em cada tela, num ambiente Claude simulado e hostil
# (sem seletor de arquivo, sem confirm/alert, clipboard recusado) e relata erros e botões "mortos".
import json, sys, re, time
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'mock_claude.py'), encoding='utf-8').read())
SRC = sys.argv[1] if len(sys.argv) > 1 else APP
html = SK + open(SRC, encoding='utf-8').read() + '</body></html>'
HOSTILE = r"""
(() => {
  window.confirm = () => false; window.alert = () => {}; window.prompt = () => null;
  window.__fx = [];
  try { Object.defineProperty(navigator, 'clipboard', {value: {writeText: async t => { window.__fx.push('clip'); if (!window.__clipok) throw new Error('denied'); }, readText: async () => { throw new Error('denied'); }}, configurable: true}); } catch {}
  const oc = HTMLInputElement.prototype.click; HTMLInputElement.prototype.click = function(){ if (this.type === 'file') window.__fx.push('file:' + this.id); return oc.apply(this, arguments); };
  window.addEventListener('unhandledrejection', e => { (window.__errs = window.__errs || []).push('REJ ' + String(e.reason && (e.reason.stack || e.reason.message || JSON.stringify(e.reason)) ).slice(0, 300)); });
  // banco do mock persistente entre recargas
  const K = '__mockdb';
  const boot = () => { try { const o = JSON.parse(sessionStorage.getItem(K) || '{}'); for (const k in o) window.__db.set(k, o[k]); } catch {}
    const s = window.__db.set.bind(window.__db), d = window.__db.delete.bind(window.__db); const save = () => { try { sessionStorage.setItem(K, JSON.stringify(Object.fromEntries(window.__db))); } catch {} };
    window.__db.set = (k, v) => { const r = s(k, v); save(); return r; }; window.__db.delete = k => { const r = d(k); save(); return r; }; };
  boot();
})();
"""
URL = 'https://artifact.test/'
LIST = """() => [...document.querySelectorAll('button, a[href], [data-act], summary, .chip')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); if (!(r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && !e.disabled && !e.closest('[hidden]') && !e.closest('[inert]') && !(() => { let n = e.parentElement, first = true; while (n) { if (n.tagName === 'DETAILS' && !n.open && !(first && e.tagName === 'SUMMARY')) return true; first = false; n = n.parentElement; } return false; })())) return false; e.scrollIntoView({block:'center'}); const q = e.getBoundingClientRect(); const t = document.elementFromPoint(q.left + q.width / 2, q.top + q.height / 2); return !!t && (e === t || e.contains(t) || t.contains(e)); })
  .map((e, i) => { e.setAttribute('data-ci', i); return {i, id: e.id || '', tag: e.tagName, act: e.dataset.act || e.dataset.mx || e.dataset.vx || e.dataset.px || e.dataset.lx || e.dataset.dx || e.dataset.sy || e.dataset.ty || e.dataset.sx || '', txt: (e.textContent || e.title || e.getAttribute('aria-label') || '').trim().slice(0, 40)}; })"""
def open_story(pg):
    pg.click('#b-stories'); pg.wait_for_timeout(250); pg.locator('#stlist li').first.locator('button', has_text='Abrir').click(); pg.wait_for_timeout(700)
def sheet(btn):
    def f(pg): open_story(pg); pg.click(btn); pg.wait_for_timeout(350)
    return f
def guia(pg): sheet('#b-vocab')(pg); pg.locator('#guide > summary').click(); pg.wait_for_timeout(250)
def look(pg): pg.locator('#lib [data-act=look]').first.click(); pg.wait_for_timeout(350)
def editor(pg): pg.locator('#lib [data-act=edit]').first.click(); pg.wait_for_timeout(500)
def setup(pg): pg.locator('#lib [data-act=play]').first.click(); pg.wait_for_timeout(400)
STATES = [('biblioteca', lambda pg: None), ('início', setup), ('conversa', open_story), ('painel Histórias', sheet('#b-stories')), ('painel Memória', sheet('#b-memory')), ('painel Ajustes', sheet('#b-settings')),
          ('painel Ficha', sheet('#b-sim')), ('painel Palavras', sheet('#b-vocab')), ('guia aberto', guia), ('painel Rosto e voz', look), ('editor', editor)]
only = sys.argv[2] if len(sys.argv) > 2 else None
report = []
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 400, 'height': 820})
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append('ERR ' + str(e)[:300]))
    pg.add_init_script(MOCK); pg.add_init_script(HOSTILE)
    pg.route('https://fonts.googleapis.com/**', lambda r: r.abort()); pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html))
    def load(): pg.goto(URL); pg.wait_for_selector('#v-library:not([hidden])'); pg.wait_for_timeout(250)
    # semente: um personagem próprio e uma história com duas trocas
    load(); pg.evaluate("sessionStorage.clear()"); load()
    pg.locator('#lib [data-act=dup][data-id=tau]').click(); pg.wait_for_timeout(400); pg.click('#e-save'); pg.wait_for_timeout(600)
    pg.click('#b-home') if pg.is_visible('#b-home') and not pg.is_visible('#v-library') else None; pg.wait_for_timeout(300)
    pg.locator('[data-act=quick][data-id=tau]').click(); pg.wait_for_timeout(1500)
    for t in ['*Olho em volta.*', '*Mostro as mãos.*']: pg.fill('#in', t); pg.click('#b-send'); pg.wait_for_timeout(2600)
    seed = pg.evaluate("sessionStorage.getItem('__mockdb')")
    print('semente ok, erros até aqui:', errs + (pg.evaluate("window.__errs || []")))
    for name, enter in STATES:
        if only and only not in name: continue
        load(); 
        try: enter(pg)
        except Exception as e: print('NÃO ENTROU EM', name, str(e)[:120]); continue
        items = pg.evaluate(LIST); print('==', name, len(items), 'controles', flush=True)
        for it in items:
            pg.evaluate("s => sessionStorage.setItem('__mockdb', s)", seed); load()
            try: enter(pg)
            except Exception as e: report.append((name, it, 'ENTRADA FALHOU')); continue
            cur = pg.evaluate(LIST)
            m = [c for c in cur if (c['id'], c['act'], c['txt']) == (it['id'], it['act'], it['txt'])]
            if not m: continue
            errs.clear(); pg.evaluate("window.__errs = []; window.__fx = []; window.__mut = 0; window.__mo && window.__mo.disconnect(); window.__mo = new MutationObserver(l => { window.__mut += l.length; }); window.__mo.observe(document.body, {subtree:true, childList:true, attributes:true, characterData:true}); window.__sv0 = window.__saved.length; window.__c0 = window.__calls.length;")
            try: pg.locator('[data-ci="%d"]' % m[0]['i']).click(timeout=2500, no_wait_after=True)
            except Exception as e: report.append((name, it, 'NÃO CLICÁVEL')); print('ACHADO [%s] #%s {%s} "%s" -> NÃO CLICÁVEL' % (name, it['id'], it['act'], it['txt']), flush=True); continue
            pg.wait_for_timeout(1900)
            try: r = pg.evaluate("({mut: window.__mut, fx: window.__fx, errs: window.__errs, saved: window.__saved.length - window.__sv0, calls: window.__calls.length - window.__c0, toast: (document.querySelector('#toast') && !document.querySelector('#toast').hidden) ? document.querySelector('#toast').textContent : ''})")
            except Exception as e: r = {'mut': 1, 'fx': [], 'errs': ['EVAL ' + str(e)[:80]], 'saved': 0, 'calls': 0, 'toast': ''}
            bad = errs + r['errs']
            dead = r['mut'] == 0 and not r['fx'] and not r['saved'] and not r['calls']
            fileonly = any(x.startswith('file:') for x in r['fx']) and r['mut'] <= 2 and not r['toast']
            if bad or dead or fileonly:
                why = ('ERRO ' + ' | '.join(bad)) if bad else ('MORTO (nada acontece)' if dead else 'SÓ ABRE SELETOR DE ARQUIVO (sem alternativa visível)')
                report.append((name, it, why)); print('ACHADO [%s] %s #%s {%s} "%s" -> %s' % (name, it['tag'], it['id'], it['act'], it['txt'], why), flush=True)
    print('\n===== RELATÓRIO =====')
    for name, it, why in report: print('[%s] %s #%s {%s} "%s" -> %s' % (name, it['tag'], it['id'], it['act'], it['txt'], why))
    print('total de achados:', len(report))
