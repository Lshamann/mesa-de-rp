import json, re, base64
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = sys.argv[:1]
src = open(os.path.join(HERE, 'crawl.py'), encoding='utf-8').read()
exec(src.split("\nURL = 'https://artifact.test/'\nLIST")[0])
URL = 'https://artifact.test/'
fails = []
def ok(l, c, x=''):
    print(('PASS ' if c else 'FAIL ') + l + (('  ' + str(x)[:260]) if x != '' else ''))
    if not c: fails.append(l)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGP8z8Dwn4EIwESMolGFAGZ2AgHqzSdOAAAAAElFTkSuQmCC')
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 400, 'height': 820}); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.add_init_script(MOCK); pg.add_init_script(HOSTILE)
    pg.route('https://fonts.googleapis.com/**', lambda r: r.abort()); pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html))
    def load(): pg.goto(URL); pg.wait_for_selector('#v-library:not([hidden])'); pg.wait_for_timeout(300)
    load(); pg.evaluate("sessionStorage.clear(); localStorage.clear(); localStorage.setItem('rp.prefs', JSON.stringify({theme:'auto', sim:true}))"); load()
    pg.wait_for_timeout(1700)
    pr = pg.evaluate("JSON.parse(localStorage.getItem('rp.prefs'))")
    ok('migração: simulação desligada e aviso único', pr.get('sim') is False and pr.get('v') == 2 and 'simulação agora vem desligada' in pg.inner_text('#toast'), pr)
    load(); ok('aviso não repete', 'simulação agora' not in (pg.inner_text('#toast') if pg.is_visible('#toast') else ''))
    # 1. início rápido sem simulação
    pg.locator('[data-act=quick][data-id=tau]').click(); pg.wait_for_timeout(1600)
    calls = pg.evaluate("window.__calls.filter(c => typeof c.input === 'string').map(c => c.input.slice(0, 60))")
    ok('história nova sem simulação (nenhuma consulta de ficha)', not any('simula' in c.lower() for c in calls) and not pg.is_visible('#simbar'), calls)
    pg.fill('#in', 'rascunho que não pode sumir'); pg.wait_for_timeout(800)
    load(); pg.click('#b-stories'); pg.wait_for_timeout(250); pg.locator('#stlist li').first.locator('button', has_text='Abrir').click(); pg.wait_for_timeout(600)
    ok('rascunho volta depois de recarregar', pg.input_value('#in') == 'rascunho que não pode sumir', pg.input_value('#in'))
    pg.click('#b-send'); pg.wait_for_timeout(2600)
    ok('rascunho some depois de enviar', pg.evaluate("localStorage.getItem('rp.draft')") is None)
    # 2. copiar com clipboard recusado -> caixa de copiar
    pg.click('#b-stories'); pg.wait_for_timeout(250); pg.click('#b-copy-json'); pg.wait_for_timeout(500)
    ok('cópia recusada abre a caixa de copiar', pg.is_visible('#io') and 'Copiar' in pg.inner_text('#io-t'))
    backup = pg.input_value('#io-body textarea'); ok('caixa traz o backup inteiro', backup.startswith('{"format":"mesa-rp-v1"'), backup[:40])
    pg.screenshot(path=D + 'pro_copy.png')
    pg.evaluate("window.__clipok = true"); pg.locator('#io-acts button', has_text='Copiar').click(); pg.wait_for_timeout(300)
    ok('botão Copiar da caixa copia e fecha', not pg.is_visible('#io') and 'copiado' in pg.inner_text('#toast')); pg.evaluate("window.__clipok = false")
    # 3. carregar backup sem seletor de arquivo
    pg.click('#b-import'); pg.wait_for_timeout(1700)
    ok('sem seletor: abre Trazer arquivo', pg.is_visible('#io') and 'Trazer arquivo' in pg.inner_text('#io-t'), pg.inner_text('#io-t') if pg.is_visible('#io') else 'fechado')
    pg.screenshot(path=D + 'pro_file.png')
    pg.fill('#io-body textarea', backup); pg.locator('#io-acts button', has_text='Usar o que colei').click(); pg.wait_for_timeout(1200)
    n = pg.evaluate("[...window.__db.keys()].filter(k => /\\/stories\\/[^/]+$/.test(k)).length")
    ok('backup colado é importado', n == 2 and not pg.is_visible('#io'), n)
    # 4. baixar falhando -> caixa de copiar
    pg.click('#b-stories') if not pg.is_visible('#sh-stories') else None; pg.wait_for_timeout(250)
    pg.evaluate("window.__dlfail = true")
    # 5. imagem sem seletor: colar
    pg.click('#b-close') if pg.is_visible('#b-close') else None; pg.click('#b-home'); pg.wait_for_timeout(300)
    pg.locator('#lib [data-act=dup][data-id=tau]').click(); pg.wait_for_timeout(500)
    pg.locator('[data-act=pick-img]').first.click(); pg.wait_for_timeout(1700)
    ok('imagem sem seletor: abre Trazer imagem', pg.is_visible('#io') and 'Trazer imagem' in pg.inner_text('#io-t'))
    pg.evaluate("""b64 => { const bin = atob(b64), a = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
      const f = new File([a], 'x.png', {type:'image/png'}); const dt = new DataTransfer(); dt.items.add(f);
      const ev = new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}); document.querySelector('.pastebox').dispatchEvent(ev); }""", base64.b64encode(PNG).decode())
    pg.wait_for_timeout(900)
    ok('imagem colada vira retrato', not pg.is_visible('#io') and pg.locator('#ed-body .tile, #ed-body .portrait, #ed-body [style*="data:image"]').count() >= 1)
    pg.click('#e-cancel'); pg.wait_for_timeout(300)
    # 6. tela de início com simulação ligada
    pg.locator('#lib [data-act=play][data-id=tau]').click(); pg.wait_for_timeout(400)
    ok('início mostra a simulação desligada', pg.locator('#setup-form .seg button[aria-pressed=true]', has_text='Desligada').count() == 1 or pg.locator('#setup-form .seg button.on', has_text='Desligada').count() == 1)
    pg.locator('#setup-form .seg').get_by_role('button', name='Ligada', exact=True).click(); pg.locator('#setup-form button[type=submit]').click(); pg.wait_for_timeout(1800)
    calls = pg.evaluate("window.__calls.filter(c => typeof c.input === 'string').map(c => c.input.slice(0, 80))")
    ok('ligada no início: monta a ficha', any('simula' in c.lower() for c in calls), calls[-3:])
    # 7. guia de suaíli
    pg.click('#b-vocab'); pg.wait_for_timeout(300); pg.locator('#guide > summary').click(); pg.wait_for_timeout(200)
    ok('guia com seções de regras', pg.locator('#guide details.gsec').count() >= 20 and pg.locator('#guide details.gsec summary', has_text='Dizer “não”').count() == 1, pg.locator('#guide details.gsec').count())
    pg.locator('#guide details.gsec summary', has_text='Dizer “não”').click(); pg.wait_for_timeout(150)
    pg.screenshot(path=D + 'pro_guide.png')
    pg.fill('#g-q', 'agua'); pg.wait_for_timeout(250)
    t = pg.inner_text('#guide'); ok('busca sem acento acha água', 'maji' in t and 'Ninataka maji' in t, t[:120])
    pg.locator('#guide button.glr', has_text='Ninataka maji').first.click(); pg.wait_for_timeout(250)
    ok('frase do guia vai para a mensagem', 'Ninataka maji' in pg.input_value('#in'), pg.input_value('#in'))
    # 8. diagnóstico
    pg.click('#b-settings'); pg.wait_for_timeout(300)
    dg = pg.inner_text('#diag-box'); ok('diagnóstico mostra ambiente', 'dentro do Claude' in dg and 'Mesa de RP 2026' in dg, dg[:100])
    # 9. janela que "pisca" e não entrega nada: o segundo toque oferece colar
    pg.evaluate("document.querySelector('#b-close') && !document.querySelector('#sheet').hidden && document.querySelector('#b-close').click()"); pg.wait_for_timeout(200)
    pg.evaluate("HTMLInputElement.prototype.click = function(){ if (this.type === 'file') { window.dispatchEvent(new Event('blur')); return; } }")
    pg.click('#b-stories'); pg.wait_for_timeout(250); pg.click('#b-import'); pg.wait_for_timeout(1700)
    ok('janela que só pisca: primeiro toque não abre nada', not pg.is_visible('#io'))
    pg.click('#b-import'); pg.wait_for_timeout(300)
    ok('segundo toque abre Trazer arquivo', pg.is_visible('#io') and 'Trazer arquivo' in pg.inner_text('#io-t'))
    pg.click('#io-acts >> text=Fechar'); pg.wait_for_timeout(150)
    # 10. diálogo de copiar fecha ao trocar de tela
    pg.click('#b-copy-json'); pg.wait_for_timeout(400)
    ok('cópia recusada abre o diálogo', pg.is_visible('#io') and 'Copiar' in pg.inner_text('#io-t'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc fecha o diálogo', not pg.is_visible('#io'))
    print('errors:', errs, pg.evaluate("window.__errs || []")); print('FAILS:', fails)
