# Testa: lembrete de backup, aparência, Sobre você e livro ePub.
import os, zipfile, io
import xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'mock_claude.py'), encoding='utf-8').read())
URL = 'https://artifact.test/'
ok = lambda c, m: print(('PASS ' if c else 'FAIL ') + m)
PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 820}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda js: pg.evaluate("async () => { const M = window.__mesa; " + js + " }")
    pg.add_init_script("window.__MESA_TEST = 1;"); pg.add_init_script(MOCK); pg.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)); pg.goto(URL); pg.wait_for_timeout(900)
    # ---- backup lembrete: sem histórias não avisa
    ok(ev("return M.bkInfo()") is None, 'sem histórias: sem lembrete')
    pg.click('[data-act=quick][data-id=tau]'); pg.wait_for_timeout(1500)
    pg.click('#b-home') if pg.is_visible('#b-home') else None
    ev("M.S.view; return 1")
    ok(ev("return M.bkInfo()") is None, 'história nova: ainda sem lembrete (relógio começa agora)')
    ev("localStorage.setItem('rp.bkfirst', String(Date.now() - 40*864e5)); return 1")
    info = ev("return M.bkInfo()")
    ok(info is not None and info['days'] >= 39 and not info['last'], 'após 40 dias sem backup: lembrete (nunca salvou)')
    ev("M.bkMark(); return 1")
    ok(ev("return M.bkInfo()") is None, 'depois de salvar backup: some')
    ev("localStorage.setItem('rp.lastbk', String(Date.now() - 35*864e5)); return 1")
    info = ev("return M.bkInfo()"); ok(info is not None and info['last'] > 0, 'backup antigo: lembrete com dias')
    ev("M.renderLibrary(); document.querySelector('#b-home') && 0; return 1")
    pg.evaluate("document.querySelector('#v-library') && (window.__mesa.S.view = 'library')")
    pg.evaluate("() => { const b = document.querySelector('.brand'); b && b.click(); }"); pg.wait_for_timeout(500)
    if not pg.locator('[data-act=bk-later]').count():
        pg.evaluate("window.__mesa.renderLibrary()")
    ok(pg.locator('[data-act=bk-later]').count() == 1 and pg.locator('[data-act=bk-now]').count() == 1, 'cartão de lembrete na biblioteca')
    pg.evaluate("document.querySelector('[data-act=bk-later]').click()"); pg.wait_for_timeout(300)
    ok(ev("return M.bkInfo()") is None, '"Lembrar depois" adia')
    ev("localStorage.removeItem('rp.bksnooze'); window.__mesa.renderLibrary(); return 1")
    pg.evaluate("document.querySelector('[data-act=bk-now]').click()"); pg.wait_for_timeout(800)
    ok(len(pg.evaluate("window.__saved")) >= 1 and ev("return M.bkInfo()") is None, '"Salvar agora" baixa e marca o backup')
    # ---- aparência
    pg.click('#b-set') if pg.is_visible('#b-set') else pg.evaluate("document.querySelector('[data-sheet=settings], #b-settings') && document.querySelector('[data-sheet=settings], #b-settings').click()")
    pg.wait_for_timeout(300)
    if not pg.locator('#seg-fs').is_visible():
        pg.evaluate("() => { const b = [...document.querySelectorAll('button')].find(x => /ajustes/i.test(x.textContent)); b && b.click(); }"); pg.wait_for_timeout(300)
    ok(pg.locator('#seg-fs button').count() == 4 and pg.locator('#seg-ac button').count() == 5, 'opções de aparência aparecem')
    pg.click('#seg-fs >> text=Enorme'); pg.click('#seg-ac >> text=Rosa'); pg.click('#seg-lh >> text=Folgado'); pg.click('#seg-rf >> text=Sem serifa'); pg.wait_for_timeout(150)
    st = pg.evaluate("() => { const s = document.documentElement.style; return [s.getPropertyValue('--read-fs'), s.getPropertyValue('--read-lh'), s.getPropertyValue('--accent'), getComputedStyle(document.querySelector('#look-demo')).fontSize, getComputedStyle(document.querySelector('#look-demo')).fontFamily]; }")
    ok(st[0] == '21.5px' and st[1] == '1.85' and st[2].startswith('#') and st[3] == '21.5px' and 'system-ui' in st[4], 'letra, espaçamento, cor e fonte aplicados: %s' % st)
    pg.click('#seg-ac >> text=Violeta'); pg.wait_for_timeout(100)
    ok(pg.evaluate("document.documentElement.style.getPropertyValue('--accent')") == '', 'voltar ao violeta (padrão) remove o ajuste')
    pg.reload(); pg.wait_for_timeout(900)
    ok(pg.evaluate("document.documentElement.style.getPropertyValue('--read-fs')") == '21.5px', 'preferência de aparência persiste')
    # ---- Sobre você
    pg.click('[data-act=quick][data-id=tau]'); pg.wait_for_timeout(1500)
    pg.click('#b-memory'); pg.wait_for_timeout(300)
    pg.fill('#yo-look', 'Cabelo cortado rente e um curativo na testa'); pg.click('[data-mx=you-save]'); pg.wait_for_timeout(300)
    r = pg.evaluate("() => { const M = window.__mesa; const t = M.buildTurns(M.S.story, M.S.char, M.S.story.messages.length).turns; return t[0].content; }")
    ok('Aparência e identidade têm consequência' in r, 'regra de consequência da aparência está no prompt')
    ok('curativo na testa' in r, 'aparência editada na Memória entra no prompt')
    # ---- ePub
    pg.evaluate("() => { const M = window.__mesa; M.S.char.portrait = '%s'; const st = M.S.story; st.diary = [{n:1, title:'A praia', text:'*A maré baixou.* \"Karibu\" & mais.\\n\\nSegundo parágrafo <com> símbolos.'}, {n:2, title:'A trilha', text:'Eles andaram.'}]; }" % PNG)
    arr = pg.evaluate("() => Array.from(window.__mesa.buildEpub(window.__mesa.S.story))")
    data = bytes(arr); z = zipfile.ZipFile(io.BytesIO(data)); names = z.namelist()
    ok(z.testzip() is None, 'zip íntegro (CRC ok)')
    ok(names[0] == 'mimetype' and z.getinfo('mimetype').compress_type == 0 and z.read('mimetype') == b'application/epub+zip', 'mimetype primeiro e sem compressão')
    bad = []
    for n in names:
        if n.endswith(('.xhtml', '.opf', '.xml')):
            try: ET.fromstring(z.read(n))
            except Exception as e: bad.append((n, str(e)))
    ok(not bad, 'todo XML é bem formado %s' % bad)
    ok(all(x in names for x in ['META-INF/container.xml', 'OEBPS/content.opf', 'OEBPS/nav.xhtml', 'OEBPS/cap1.xhtml', 'OEBPS/cap2.xhtml', 'OEBPS/cover.png', 'OEBPS/titulo.xhtml']), 'arquivos do livro: %s' % names)
    opf = ET.fromstring(z.read('OEBPS/content.opf')); ns = {'o': 'http://www.idpf.org/2007/opf'}
    ids = {i.get('id') for i in opf.findall('.//o:manifest/o:item', ns)}; refs = [i.get('idref') for i in opf.findall('.//o:spine/o:itemref', ns)]
    ok(all(r in ids for r in refs) and len(refs) == 3, 'spine aponta só para itens do manifesto')
    cap = z.read('OEBPS/cap1.xhtml').decode()
    ok('<em>A maré baixou.</em>' in cap and '&amp; mais' in cap and '&lt;com&gt;' in cap, 'itálico e símbolos escapados no capítulo')
    ok(z.read('OEBPS/cover.png')[:4] == b'\x89PNG', 'capa é o retrato do personagem')
    # sem diário: capítulos a partir das mensagens
    ev("M.S.story.diary = []; return 1"); arr2 = pg.evaluate("() => Array.from(window.__mesa.buildEpub(window.__mesa.S.story))")
    z2 = zipfile.ZipFile(io.BytesIO(bytes(arr2))); ok('OEBPS/cap1.xhtml' in z2.namelist() and z2.testzip() is None, 'sem diário: gera capítulos a partir da conversa')
    before = len(pg.evaluate("window.__saved")); pg.evaluate("document.querySelector('#b-epub').click()"); pg.wait_for_timeout(600)
    sv = pg.evaluate("window.__saved"); ok(len(sv) == before + 1 and sv[-1]['filename'].endswith('.epub'), 'botão do livro envia .epub ao download')
    print('errors', errs)
