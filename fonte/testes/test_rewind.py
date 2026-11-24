# Testa: arrastar a linha de botões não gera resposta; Voltar até aqui (com ponto de volta, nas mensagens antigas e desfazer).
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'mock_claude.py'), encoding='utf-8').read())
URL = 'https://artifact.test/'
ok = lambda c, m: print(('PASS ' if c else 'FAIL ') + m)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 400, 'height': 820}, has_touch=True, is_mobile=True); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda js: pg.evaluate("async () => { const M = window.__mesa; " + js + " }")
    ncalls = lambda: pg.evaluate("window.__calls.filter(c => typeof c.input !== 'string').length")
    pg.add_init_script("window.__MESA_TEST = 1;"); pg.add_init_script(MOCK)
    pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)); pg.goto(URL); pg.wait_for_timeout(900)
    pg.click('[data-act=quick][data-id=tau]'); pg.wait_for_timeout(1500)
    def send(t):
        pg.fill('#in', t); pg.click('#b-send'); pg.wait_for_timeout(2200); ev("M.ckMark(); return 1")
    send('Oi, Tau.')
    ev("M.applyKeeperJSON(M.S.story, {npcs: [{nome: 'Guarda', jeito: 'sério'}]}); M.ckMark(); return 1")
    send('Eu roubo a canoa do pescador.')
    ev("M.applyKeeperJSON(M.S.story, {npcs: [{nome: 'Vítima', jeito: 'furioso'}]}); M.ckMark(); return 1")
    send('Remo para longe.')
    # 1. arrasto na linha de botões
    swipe = """(sel) => { const el = document.querySelector(sel); const r = el.getBoundingClientRect(); const x = r.left + r.width - 20, y = r.top + r.height / 2;
      const mk = (cx) => new Touch({identifier: 1, target: el, clientX: cx, clientY: y});
      el.dispatchEvent(new TouchEvent('touchstart', {touches: [mk(x)], changedTouches: [mk(x)], bubbles: true}));
      el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [mk(x - 160)], bubbles: true})); }"""
    last = ev("const st = M.S.story; let k = st.messages.length - 1; return k")
    n0 = ncalls(); pg.evaluate(swipe, '#msgs article[data-i="%d"] .acts' % last); pg.wait_for_timeout(1500)
    ok(ncalls() == n0, 'arrastar a linha de botões não gera resposta nova')
    n0 = ncalls(); pg.evaluate(swipe, '#msgs article[data-i="%d"] .body' % last); pg.wait_for_timeout(2200)
    ok(ncalls() == n0 + 1, 'arrastar o texto da última resposta continua pedindo outra versão')
    # 2. voltar até a resposta do roubo (com ponto de volta)
    idx = ev("return M.S.story.messages.findIndex(m => m.role === 'assistant' && M.S.story.messages[M.S.story.messages.indexOf(m) - 1] && M.S.story.messages[M.S.story.messages.indexOf(m) - 1].text.includes('roubo'))")
    btn = '#msgs article[data-i="%d"] [data-act=rewind]' % idx
    pg.click(btn); pg.wait_for_timeout(150)
    ok('Confirmar: desfazer 4 mensagens' in pg.inner_text(btn), 'pede confirmação com a contagem: ' + pg.inner_text(btn))
    pg.click(btn); pg.wait_for_timeout(800)
    ok(ev("return M.S.story.messages.length") == idx - 1, 'apaga o roubo e tudo depois')
    ok(ev("return M.S.story.npcs.map(p => p.name).join(',')") == 'Guarda', 'anotações voltam ao ponto de antes do roubo')
    ok('roubo a canoa' in pg.input_value('#in'), 'sua ação volta para a caixa de texto')
    ok(pg.locator('#msgs .rewind').count() == 1 and 'Desfazer a volta' in pg.inner_text('#msgs .rewind'), 'aviso com Desfazer a volta')
    pg.click('#msgs .rewind [data-act=rewind-undo]'); pg.wait_for_timeout(600)
    ok(ev("return M.S.story.messages.length") == 7 and 'Vítima' in ev("return M.S.story.npcs.map(p => p.name).join(',')"), 'desfazer a volta traz tudo de volta')
    # 3. voltar até uma mensagem antiga (arquivada): memória e anotações limpas pela IA
    ev("""const st = M.S.story; const old = [{id:'a1', role:'assistant', text:'Tau te achou na praia.', alts:['Tau te achou na praia.'], ai:0},
      {id:'a2', role:'user', text:'Eu roubo a canoa do pescador.'}, {id:'a3', role:'assistant', text:'O pescador grita. Você foge com a canoa.', alts:['x'], ai:0}];
      await M.S.store.setArchive(st.id, 1, old); st.archiveChunks = 1; st.archived = 3; st.memory = 'Alex chegou na ilha. Alex roubou a canoa de um pescador e virou inimigo dos pescadores.';
      st.rumors = [{id:'r1', fato:'Alex roubou a canoa', sabem:['Pescadores'], pode:[]}]; st.rep = [{id:'g1', grupo:'Pescadores', nivel:-2}]; M.persist(true); return 1""")
    pg.fill('#in', '')
    ev("await M.rewindTo('a3'); return 1"); pg.wait_for_timeout(1500)
    st = ev("const st = M.S.story; return {n: st.messages.length, ids: st.messages.map(m => m.id), mem: st.memory, npcs: st.npcs.map(p => p.name), rum: st.rumors.length, rep: st.rep.length, arc: st.archiveChunks, archived: st.archived}")
    ok(st['ids'] == ['a1'] and st['archived'] == 0, 'mensagens antigas reescritas: sobra só o que veio antes: %s' % st['ids'])
    ok('roubou' not in st['mem'] and 'Nada mais aconteceu' in st['mem'], 'memória limpa do roubo: ' + st['mem'])
    ok('Vítima' not in st['npcs'] and st['rum'] == 0 and st['rep'] == 0, 'NPC, boato e reputação do roubo removidos')
    ok('roubo a canoa' in pg.input_value('#in'), 'ação antiga volta para a caixa de texto')
    ok(any('VOLTOU NO TEMPO' in c['input'] for c in pg.evaluate("window.__calls") if isinstance(c['input'], str)), 'pediu a limpeza à IA')
    ok('limpa' in pg.inner_text('#msgs .rewind'), 'aviso diz que a memória foi limpa')
    pg.click('#msgs .rewind [data-act=rewind-undo]'); pg.wait_for_timeout(800)
    st = ev("const st = M.S.story; return {n: st.messages.length, mem: st.memory, a: (await M.S.store.getArchive(st.id, 1)).length}")
    ok(st['n'] == 7 and 'roubou' in st['mem'] and st['a'] == 3, 'desfazer também devolve as mensagens antigas e a memória')
    print('errors', errs)
