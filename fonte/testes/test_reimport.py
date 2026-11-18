# Testa: importar de novo um personagem (mesmo arquivo, ficha mudada, personagem excluído antes).
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'mock_claude.py'), encoding='utf-8').read())
URL = 'https://artifact.test/'
ok = lambda c, m: print(('PASS ' if c else 'FAIL ') + m)
ch = {"id": "zz1", "name": "Zuri", "role": "char", "description": "Pescadora velha.", "openings": [{"id": "o0", "label": "Cais", "text": "*Zuri remenda a rede.*"}], "lore": [], "updated": 1000}
def pack(c): return json.dumps({"format": "mesa-rp-all-v1", "exported": 1, "chars": [c], "stories": []}, ensure_ascii=False)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 820}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda js: pg.evaluate("async () => { const M = window.__mesa; " + js + " }")
    pg.add_init_script("window.__MESA_TEST = 1;"); pg.add_init_script(MOCK)
    pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)); pg.goto(URL); pg.wait_for_timeout(900)
    def imp(t):
        pg.evaluate("document.querySelector('#sheet').hidden || document.querySelector('#b-close').click()")
        pg.click('#b-stories'); pg.wait_for_timeout(250); pg.fill('#paste', t); pg.click('#b-paste'); pg.wait_for_timeout(900)
        return pg.inner_text('#imp-msg')
    m = imp(pack(ch)); ok('Importado: 1 personagem' in m, 'primeira importação: ' + m)
    m = imp(pack(ch)); ok('Nada novo' in m and 'iguais ou mais novos' in m, 'mesmo arquivo de novo: nada novo')
    c2 = dict(ch, description="Pescadora velha e cega de um olho.", updated=900)
    m = imp(pack(c2)); ok('atualizado' in m and ev("return M.S.chars.get('zz1').description") == c2['description'], 'ficha diferente (mesmo mais antiga) atualiza: ' + m[:90])
    ok(ev("return M.S.chars.get('zz1').hist.length") == 1 and ev("return M.S.chars.get('zz1').hist[0].d.description") == 'Pescadora velha.', 'ficha anterior guardada em Versões anteriores')
    pg.evaluate("document.querySelector('#b-close').click()"); ev("M.renderLibrary(); return 1")
    pg.evaluate("() => { const b = document.querySelector('[data-act=del][data-id=zz1]'); b.click(); b.click(); }"); pg.wait_for_timeout(600)
    ok(not ev("return M.S.chars.has('zz1')"), 'personagem excluído')
    m = imp(pack(dict(ch, updated=500))); ok('Importado: 1 personagem' in m and ev("return M.S.chars.has('zz1')"), 'importar de novo depois de excluir traz de volta: ' + m[:80])
    ok(not ev("return (M.S.index.gone || []).some(x => x.id === 'zz1')") and not ev("return (M.S.index.trash || []).some(x => x.id === 'zz1')"), 'sai da lixeira e da lista de excluídos')
    print('errors', errs)
