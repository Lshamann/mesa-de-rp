# Testa: crioulo haitiano (e iorubá) na tradução das falas.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'mock_claude.py'), encoding='utf-8').read())
URL = 'https://artifact.test/'
ok = lambda c, m: print(('PASS ' if c else 'FAIL ') + m)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 820}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda js: pg.evaluate("async () => { const M = window.__mesa; " + js + " }")
    pg.add_init_script("window.__MESA_TEST = 1;"); pg.add_init_script(MOCK)
    pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)); pg.goto(URL); pg.wait_for_timeout(900)
    pg.click('[data-act=quick][data-id=tau]'); pg.wait_for_timeout(1500)
    pg.fill('#in', '"Eu não sei onde ele está."'); pg.click('#b-tr'); pg.wait_for_timeout(300)
    names = pg.evaluate("[...document.querySelectorAll('#trmenu button')].map(b => b.textContent)")
    ok(any('Crioulo haitiano' in n for n in names) and any('Iorubá' in n for n in names), 'menu tem crioulo haitiano e iorubá')
    pg.click('#trmenu button:has-text("Crioulo haitiano")'); pg.wait_for_timeout(1200)
    c = [x for x in pg.evaluate("window.__calls") if isinstance(x['input'], str) and 'Traduza para' in x['input']]
    ok(c and 'Traduza para crioulo haitiano' in c[-1]['input'] and 'kreyòl ayisyen' in c[-1]['input'], 'pedido de tradução vai para o crioulo haitiano')
    pg.click('#b-tr'); pg.wait_for_timeout(300)
    if not pg.is_visible('#trmenu'): pg.click('#b-tr'); pg.wait_for_timeout(300)
    href = pg.evaluate("[...document.querySelectorAll('#trmenu a')].map(a => a.href).join(' ')")
    ok('tl=ht' in href, 'link do Google Tradutor usa ht')
    ok(ev("return M.guessLang('Mwen pa konnen kote li ye, zanmi.', 'pt')") == 'ht', 'reconhece crioulo haitiano para a voz')
    ok(ev("return M.guessLang('Eu não sei onde ele está, você sabe?', 'pt')") == 'pt', 'português continua português')
    ok(ev("return M.guessLang('Je ne sais pas où il est, mon ami.', 'pt')") == 'fr', 'francês continua francês')
    print('errors', errs)
