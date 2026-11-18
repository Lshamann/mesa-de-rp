# Testa: lugares (anotador, prompt, painel) e NPC que vira personagem.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'mock_claude.py'), encoding='utf-8').read())
URL = 'https://artifact.test/'
ok = lambda c, m: print(('PASS ' if c else 'FAIL ') + m)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 820}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda js: pg.evaluate("async () => { const M = window.__mesa; " + js + " }")
    prompt = lambda: ev("const t = M.buildTurns(M.S.story, M.S.char, M.S.story.messages.length).turns; return t[0].content;")
    pg.add_init_script("window.__MESA_TEST = 1;"); pg.add_init_script(MOCK); pg.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)); pg.goto(URL); pg.wait_for_timeout(900)
    pg.click('[data-act=quick][data-id=tau]'); pg.wait_for_timeout(1500)
    ev("""M.applyKeeperJSON(M.S.story, {estado: {lugar: 'Praia do norte'}, npcs: [{nome: 'Neema', aparencia: 'Alta, tranças curtas', jeito: 'Fala pouco e ri baixo', rotina: 'Pesca de manhã', sabe: 'Sabe que Alex veio do mar', acha: 'Desconfia de Alex'}],
      lugares: [{nome: 'Farol Velho', tipo: 'farol apagado', onde: 'ponta norte da ilha', quem: 'ninguém', visitado: false}, {nome: 'Aldeia Namaru', tipo: 'aldeia', onde: 'perto do rio', quem: 'Tau e Neema', visitado: true}]}); M.persist(true); return 1""")
    ok(ev("return M.S.story.places.length") == 2 and ev("return M.S.story.places.find(p => p.name === 'Aldeia Namaru').vis") is True, 'anotador cria os lugares')
    ev("M.applyKeeperJSON(M.S.story, {lugares: [{nome: 'farol velho', quem: 'um ermitão', visitado: true}, {nome: 'Aldeia Namaru', visitado: false}]}); return 1")
    pl = ev("return M.S.story.places")
    fv = [x for x in pl if x['name'] == 'Farol Velho'][0]; al = [x for x in pl if x['name'] == 'Aldeia Namaru'][0]
    ok(len(pl) == 2 and fv['quem'] == 'um ermitão' and fv['tipo'] == 'farol apagado' and fv['vis'] and al['vis'], 'atualiza sem duplicar, mantém o que não mudou e "visitado" não volta atrás')
    r = prompt(); ok('LUGARES DA HISTÓRIA' in r and 'Farol Velho: farol apagado' in r and 'já esteve lá' in r, 'lugares entram no prompt')
    pg.click('#b-memory'); pg.wait_for_timeout(300)
    ok('Farol Velho' in pg.inner_text('#mem-extra') and pg.locator('[data-px=pl-vis]').count() == 2, 'painel mostra os lugares')
    pg.fill('#pl-new', 'Gruta das Abelhas'); pg.fill('#pl-tipo', 'gruta com colmeias'); pg.click('[data-px=pl-add]'); pg.wait_for_timeout(250)
    ok(ev("return M.S.story.places.length") == 3 and 'Gruta das Abelhas' in pg.inner_text('#mem-extra'), 'adicionar lugar à mão')
    pg.locator('[data-px=pl-del]').last.click(); pg.wait_for_timeout(250)
    ok(ev("return M.S.story.places.length") == 2, 'remover lugar')
    sp = ev("const st = M.S.story; return st.places.length")
    # NPC vira personagem
    pg.locator('#mem-extra details.pdet summary', has_text='Neema').click(); pg.wait_for_timeout(200)
    pg.click('[data-px=np-char]'); pg.wait_for_timeout(500)
    ok(pg.input_value('#e-name') == 'Neema' and 'Alta, tranças curtas' in pg.input_value('#e-desc') and 'Fala pouco' in pg.input_value('#e-pers'), 'editor abre com as anotações do NPC')
    ok('Desconfia de {{user}}' in pg.input_value('#e-scen'), 'nome do jogador vira {{user}} na ficha')
    ok('Complete a ficha de Neema' in pg.input_value('#e-idea'), 'pedido para a IA completar já vem escrito')
    print('errors', errs)
