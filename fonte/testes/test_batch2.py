# Testa: Anteriormente, momentos marcados, busca na história, dados e lixeira.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'mock_claude.py'), encoding='utf-8').read())
URL = 'https://artifact.test/'
ok = lambda c, m: print(('PASS ' if c else 'FAIL ') + m)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 820}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ev = lambda js: pg.evaluate("async () => { const M = window.__mesa; " + js + " }")
    pg.add_init_script("window.__MESA_TEST = 1;"); pg.add_init_script(MOCK); pg.route('https://fonts.googleapis.com/**', lambda r: r.abort())
    pg.route(URL, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)); pg.goto(URL); pg.wait_for_timeout(900)
    pg.click('[data-act=quick][data-id=tau]'); pg.wait_for_timeout(1500)
    ev("""const st = M.S.story; const add = (role, text) => st.messages.push({id: 'm' + st.messages.length, role, text, alts: [text], ai: 0, lore: []});
      add('user', 'Pergunto sobre a irmã dele.'); add('assistant', '*Tau aponta para o mar.* "Dada yangu, Neema. Ela pesca com a rede grande."');
      add('user', 'Peço água.'); add('assistant', '*Ele estende a cabaça.* "Maji. Kunywa." Depois ri da sua cara de cansaço.');
      add('user', 'Durmo na rede.'); add('assistant', '*A noite cai sobre a aldeia e a fogueira estala baixo.*');
      await M.S.store.setArchive(st.id, 1, [{id:'a1', role:'assistant', text:'Muito antes, Tau mostrou o FAROL apagado da ponta da ilha.', alts:[], ai:0, star:true}]); st.archiveChunks = 1; st.archived = 1;
      M.persist(true); M.renderLog(); return 1;""")
    pg.wait_for_timeout(300)
    # marcar
    pg.locator('#msgs article[data-i="2"] [data-act=star]').click(); pg.wait_for_timeout(250)
    ok(ev("return !!M.S.story.messages[2].star") and pg.locator('#msgs article.starred').count() == 1, 'marcar mensagem')
    ok('★ Marcado' in pg.inner_text('#msgs article[data-i="2"] .acts'), 'botão vira ★ Marcado')
    pg.click('#b-find'); pg.wait_for_timeout(600)
    t = pg.inner_text('#find-out')
    ok('Neema' in t and 'FAROL' in t, 'lista de marcados mostra atual e antiga: ' + t[:100].replace('\n', ' '))
    pg.fill('#find-q', 'agua'); pg.wait_for_timeout(500)
    t = pg.inner_text('#find-out'); ok('1 resultado' in t and pg.locator('#find-out mark').count() == 1 and pg.inner_text('#find-out mark').lower() == 'água', 'busca sem acento destaca o trecho')
    pg.fill('#find-q', 'farol'); pg.wait_for_timeout(500)
    ok('antiga' in pg.inner_text('#find-out'), 'busca acha mensagem arquivada')
    pg.click('#find-out button:has-text("Ir até lá")'); pg.wait_for_timeout(500)
    ok(pg.locator('#msgs [data-mid=a1]').count() == 1 and pg.evaluate("window.__mesa.S.old != null"), 'ir até lá carrega antigas e encontra a mensagem')
    pg.click('#b-find'); pg.wait_for_timeout(300); pg.fill('#find-q', 'Neema'); pg.wait_for_timeout(500)
    pg.click('#find-out button:has-text("Ir até lá")'); pg.wait_for_timeout(300)
    ok(pg.locator('#msgs article.flash[data-mid=m2]').count() == 1, 'mensagem destacada ao pular')
    pg.click('#b-find'); pg.wait_for_timeout(300); pg.fill('#find-q', ''); pg.click('#find-box .chip'); pg.wait_for_timeout(500)
    ok(pg.locator('#find-out li').count() == 2, 'filtro só marcados: %d' % pg.locator('#find-out li').count())
    pg.keyboard.press('Escape'); pg.evaluate("document.querySelector('#b-close').click()"); pg.wait_for_timeout(200)
    # dados
    r = ev("const out = []; for (let i = 0; i < 300; i++) { const r = M.rollDice('2d6+1'); out.push(r.total); } return [Math.min(...out), Math.max(...out), M.rollDice('d20').label, M.rollDice('xx'), M.rollDice('d1')]")
    ok(r[0] >= 3 and r[1] <= 13 and r[2] == 'd20' and r[3] is None and r[4] is None, 'rolagem dentro dos limites e entradas ruins recusadas: %s' % r)
    pg.fill('#in', 'Tento pular o muro.'); pg.click('#b-dice'); pg.wait_for_timeout(200)
    ok(pg.locator('#io .dicegrid button').count() == 8, 'janela de dados abre')
    pg.click('#io .dicegrid button:has-text("d20")'); pg.wait_for_timeout(200)
    v = pg.input_value('#in'); ok(v.startswith('Tento pular o muro. [🎲 d20: ') and pg.is_hidden('#io'), 'resultado entra na mensagem: ' + v)
    pg.click('#b-send'); pg.wait_for_timeout(2500)
    last_call = pg.evaluate("window.__calls.filter(c => typeof c.input !== 'string').slice(-1)[0]")
    txt = str(last_call['input'][-1]['content']) if last_call else ''
    ok('Rolagem: a mensagem de' in txt and 'Respeite o resultado' in txt, 'narrador recebe a instrução da rolagem')
    ok(pg.locator('#msgs article.you .cnote', has_text='d20').count() >= 1, 'rolagem aparece como etiqueta na conversa')
    # anteriormente
    ev("M.S.story.updated = Date.now() - 7 * 3600e3; M.S.story.recap = null; M.openStory(M.S.story); return 1"); pg.wait_for_timeout(900)
    ok(pg.locator('#msgs .recap').count() == 1 and 'Resumo' in pg.inner_text('#msgs .recap'), 'Anteriormente aparece ao voltar depois de horas')
    n0 = pg.evaluate("window.__calls.length")
    ev("M.S.story.updated = Date.now() - 7 * 3600e3; M.openStory(M.S.story); return 1"); pg.wait_for_timeout(600)
    ok(pg.evaluate("window.__calls.length") == n0 and pg.locator('#msgs .recap').count() == 1, 'sem mensagem nova: reaproveita, sem consulta extra')
    pg.click('#msgs .recap [data-act=recap-x]'); pg.wait_for_timeout(200)
    ok(pg.locator('#msgs .recap').count() == 0, 'Fechar some com o Anteriormente')
    ev("M.openStory(M.S.story); return 1"); pg.wait_for_timeout(500)
    ok(pg.locator('#msgs .recap').count() == 0, 'voltar logo em seguida: sem Anteriormente')
    # lixeira: história
    sid = ev("return M.S.story.id")
    pg.click('#b-stories'); pg.wait_for_timeout(400)
    pg.locator('#stlist li').first.locator('button:has-text("Excluir")').click(); pg.locator('#stlist li').first.locator('button:has-text("Confirmar exclusão")').click(); pg.wait_for_timeout(600)
    ok(ev("return M.S.index.stories.length") == 0 and ev("return (M.S.index.trash || []).length") == 1, 'excluir manda a história para a lixeira')
    ok(ev("return !!(await M.S.store.getStory('%s'))" % sid), 'dados da história continuam guardados')
    pg.click('#b-stories'); pg.wait_for_timeout(400); pg.locator('#trash > summary').click()
    ok('lixeira (1)' in pg.inner_text('#trash').lower(), 'lixeira aparece em Histórias')
    pg.click('#trash button:has-text("Restaurar")'); pg.wait_for_timeout(600)
    ok(ev("return M.S.index.stories.length") == 1 and ev("return M.S.index.trash.length") == 0 and not ev("return (M.S.index.gone || []).some(x => x.id === '%s')" % sid), 'restaurar devolve a história e tira a marca de excluída')
    # lixeira: personagem
    ev("""const c = M.normChar(Object.assign(M.blankChar(), {id: 'cx', name: 'Zuri', description: 'd', openings: [{id:'o', label:'a', text:'oi'}]})); await M.saveChar(c); M.S.chars.set(c.id, c); M.renderLibrary(); return 1""")
    pg.evaluate("document.querySelector('#b-close') && document.querySelector('#b-close').click()"); pg.wait_for_timeout(200)
    pg.evaluate("window.__mesa.renderLibrary()"); pg.evaluate("() => { const b = document.querySelector('[data-act=del][data-id=cx]'); b.click(); b.click(); }"); pg.wait_for_timeout(600)
    ok(not ev("return M.S.chars.has('cx')") and ev("return M.S.index.trash.some(t => t.kind === 'char' && t.id === 'cx')"), 'excluir personagem vai para a lixeira')
    pg.click('#b-stories'); pg.wait_for_timeout(400); pg.evaluate("document.querySelector('#trash').open = true"); pg.click('#trash button:has-text("Restaurar")'); pg.wait_for_timeout(600)
    ok(ev("return M.S.chars.has('cx') && M.S.index.chars.some(x => x.id === 'cx')"), 'restaurar personagem')
    # limpeza de 30 dias
    ev("M.S.index.trash = [{kind:'story', id:'%s', name:'x', at: Date.now() - 31*864e5, meta:{id:'%s', chunks:1}}]; M.S.index.stories = []; await M.trashPurge(false); return 1" % (sid, sid))
    ok(ev("return M.S.index.trash.length") == 0 and not ev("return !!(await M.S.store.getStory('%s'))" % sid), 'depois de 30 dias apaga de vez')
    print('errors', errs)
