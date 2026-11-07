import os
HERE = os.path.dirname(os.path.abspath(__file__))
APP = 'file://' + os.path.join(os.path.dirname(HERE), 'saida', 'Mesa_de_RP_API.html')
import json, time, urllib.request
from playwright.sync_api import sync_playwright
D = os.path.join(HERE, 'out') + '/'; os.makedirs(D, exist_ok=True)
M = 'http://localhost:8788'
errs = []; fails = []
def ok(label, cond, extra=''):
    print(('PASS ' if cond else 'FAIL ') + label + (('  ' + str(extra)) if extra != '' else ''))
    if not cond: fails.append(label)
def mlog(): return json.load(urllib.request.urlopen(M + '/log'))
def settle(pg, quiet=1.0, cap=20):
    t0 = time.time(); pg.wait_for_selector('#b-stop', state='hidden', timeout=20000)
    n = len(mlog()); t = time.time()
    while time.time() - t0 < cap:
        time.sleep(0.25); k = len(mlog())
        if k != n: n = k; t = time.time()
        elif time.time() - t > quiet: break
    pg.wait_for_timeout(700)
def story(pg): return pg.evaluate("(()=>{const ix=JSON.parse(localStorage.getItem('rp.index'));return JSON.parse(localStorage.getItem('rp.story.'+ix.lastId))})()")
def ckmap(pg):
    v = pg.evaluate("(()=>{const ix=JSON.parse(localStorage.getItem('rp.index'));return localStorage.getItem('rp.ck.'+ix.lastId)})()")
    return json.loads(json.loads(v)['data']) if v else None
def corpo(s): return (s.get('state') or {}).get('corpo')
def items(s): return [i['name'] for i in (s.get('sim') or {}).get('items', [])]
def send(pg, text): pg.fill('#in', text); pg.click('#b-send'); settle(pg)

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 400, 'height': 820})
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'fonts' not in m.text and 'ERR_' not in m.text else None)
    pg.goto(APP); pg.wait_for_timeout(300)
    pg.evaluate("""localStorage.clear();localStorage.setItem('rp.models', JSON.stringify({active:'a',list:[{id:'a',preset:'custom',name:'Mock',base:'http://localhost:8788/v1',key:'k',model:'m',ctx:32000}]}));localStorage.setItem('rp.me',JSON.stringify({name:'Kelvin',pro:'ele'}))""")
    pg.reload(); pg.wait_for_timeout(300)
    pg.click('[data-act=quick][data-id=tau]'); settle(pg)
    s0 = story(pg); ok('sim ready after open', s0['sim']['ready'])
    ok('chip Palavras visível, sem número', pg.is_visible('#b-vocab') and pg.inner_text('#b-vocab').strip() == '📖 Palavras', pg.inner_text('#b-vocab'))

    send(pg, '*Olho em volta.*')
    s1 = story(pg); ok('R1: estado criado (sem dedo)', corpo(s1) == 'Todos inteiros', corpo(s1))
    clock1 = s1['sim']['clock']; items1 = items(s1)

    send(pg, '*Eu quebro o dedo do Diego.*')
    pg.click('#b-memory'); pg.wait_for_timeout(200)
    pg.click('[data-mx=st-up]'); settle(pg); pg.click('#b-close')
    s2 = story(pg)
    ok('R2: estado com dedo quebrado', corpo(s2) == 'Diego com o dedo quebrado', corpo(s2))
    ok('R2: sugestão de lore do dedo', any(e['name'] == 'Dedo de Diego' for e in s2.get('sloreSug', [])))
    ok('R2: sim com Tala e relógio andou', 'Tala' in items(s2) and s2['sim']['clock'] != clock1, (items(s2), s2['sim']['clock']))
    ck = ckmap(pg); ok('pontos de volta salvos', ck and len(ck['map']) >= 3, len(ck['map']) if ck else None)

    # ---- Voltar
    pg.locator('[data-act=undo]').click(); pg.wait_for_timeout(900)
    s3 = story(pg)
    ok('Voltar: estado sem o dedo', corpo(s3) == 'Todos inteiros', corpo(s3))
    ok('Voltar: sugestão do dedo sumiu', not any(e['name'] == 'Dedo de Diego' for e in s3.get('sloreSug', [])))
    ok('Voltar: Tala sumiu e relógio voltou', 'Tala' not in items(s3) and s3['sim']['clock'] == clock1, (items(s3), s3['sim']['clock'], clock1))
    ok('Voltar: ação volta para a caixa', 'quebro o dedo' in pg.input_value('#in'))
    ok('cena (faixa) sem dedo', 'dedo' not in pg.inner_text('#scene').lower())

    # ---- outro caminho: aula de palavra
    send(pg, '*Aponto o rio.* "Como se diz isso?" *Peço que me ensina.*')
    s4 = story(pg); v4 = s4.get('vocab', [])
    ok('Palavra aprendida (Mabi, Kelvin)', len(v4) == 1 and v4[0]['w'] == 'Mabi' and v4[0]['who'] == 'Kelvin', v4)
    ok('chip mostra 1', pg.inner_text('#b-vocab').strip() == '📖 Palavras 1', pg.inner_text('#b-vocab'))
    ok('palavra sublinhada na conversa', pg.locator('#msgs .msg.tau').last.locator('.vw').count() >= 1)
    pg.locator('#msgs .msg.tau').last.locator('.vw').first.click(); pg.wait_for_timeout(150)
    ok('toque mostra o significado', 'água' in pg.inner_text('#toast'), pg.inner_text('#toast'))
    ck4 = ckmap(pg)

    # ---- Regerar: não pode contar a palavra duas vezes nem acumular tempo
    clock4 = s4['sim']['clock']
    pg.locator('[data-act=regen]').click(); settle(pg)
    s5 = story(pg); v5 = s5.get('vocab', [])
    ok('Regerar: ainda 1 palavra, n=1', len(v5) == 1 and v5[0].get('n', 1) == 1, v5)
    ok('Regerar: relógio não acumula', s5['sim']['clock'] == clock4, (s5['sim']['clock'], clock4))
    last_chat = json.load(urllib.request.urlopen(M + '/lastchat'))
    hdr = last_chat['messages'][0]['content']
    ok('Regerar: prompt usa estado de antes (sem Mabi)', 'Mabi' not in hdr and 'IDIOMAS' in hdr)

    # ---- trocar de versão
    pg.locator('[data-act=swipe][data-d="-1"]').click(); pg.wait_for_timeout(900)
    s6 = story(pg)
    ok('Versão 1: palavra continua (ponto próprio)', len(s6.get('vocab', [])) == 1 and s6['sim']['clock'] == clock4, (s6.get('vocab'), s6['sim']['clock']))

    # ---- usar a palavra: conta uso
    send(pg, '"Mabi?" *Mostro a cuia.*')
    s7 = story(pg); v7 = s7.get('vocab', [])
    ok('Uso conta: n=2 (conhecida)', v7 and v7[0].get('n') == 2, v7)
    hdr = json.load(urllib.request.urlopen(M + '/lastchat'))['messages'][0]['content']
    ok('prompt traz PALAVRAS APRENDIDAS com Mabi', 'PALAVRAS APRENDIDAS EM CENA' in hdr and 'Mabi = água' in hdr)

    # ---- painel Palavras
    pg.click('#b-vocab'); pg.wait_for_timeout(200)
    txt = pg.inner_text('#vocab-box')
    ok('painel lista Mabi sob Kelvin (você)', 'Mabi' in txt and 'kelvin (você)' in txt.lower() and 'conhecida' in txt.lower(), txt[:200])
    pg.screenshot(path=D + 'vocab_sheet.png')
    pg.click('[data-vx=rev]'); pg.wait_for_timeout(100)
    ok('revisão mostra a palavra', 'Mabi' in pg.inner_text('#vocab-box') and pg.locator('[data-vx=show]').count() == 1)
    pg.click('[data-vx=show]'); pg.wait_for_timeout(100)
    ok('revisão mostra significado', 'água' in pg.inner_text('#vocab-box'))
    pg.screenshot(path=D + 'vocab_review.png')
    pg.click('[data-vx=rev-end]'); pg.wait_for_timeout(100)
    pg.locator('[data-vx=use]').first.click(); pg.wait_for_timeout(150)
    ok('Usar põe a palavra na caixa', 'Mabi' in pg.input_value('#in'), pg.input_value('#in'))
    pg.fill('#in', '')

    # ---- anotar à mão e voltar: anotada fica
    pg.click('#b-vocab'); pg.wait_for_timeout(150)
    pg.locator('details.adv summary', has_text='Anotar').click()
    pg.fill('#vx-w', 'jërëjëf'); pg.fill('#vx-m', 'obrigado'); pg.fill('#vx-lang', 'wolof')
    pg.click('[data-vx=add]'); pg.wait_for_timeout(300); pg.click('#b-close'); pg.wait_for_timeout(700)
    pg.locator('[data-act=undo]').click(); pg.wait_for_timeout(900)
    s8 = story(pg); ws = sorted(v['w'] for v in s8.get('vocab', []))
    ok('Voltar mantém palavra anotada e volta o uso de Mabi', ws == ['Mabi', 'jërëjëf'] and [v for v in s8['vocab'] if v['w'] == 'Mabi'][0].get('n', 1) == 1, s8.get('vocab'))

    # ---- Ramificar do R1 (antes da aula): sem palavra automática
    first_tau = pg.locator('#msgs .msg.tau').nth(1)
    first_tau.locator('[data-act=branch]').click(); settle(pg)
    sb = story(pg)
    ok('Ramo: título e mensagens até R1', sb['title'].endswith('· ramo') and len(sb['messages']) == 3, (sb['title'], len(sb['messages'])))
    ok('Ramo: estado de R1, sem Mabi, com a anotada', corpo(sb) == 'Todos inteiros' and [v['w'] for v in sb.get('vocab', [])] == ['jërëjëf'], (corpo(sb), sb.get('vocab')))
    ok('Ramo: sim do ponto R1', sb['sim']['clock'] == clock1, (sb['sim']['clock'], clock1))
    ok('Ramo: tem pontos de volta', ckmap(pg) is not None)

    # ---- história antiga contaminada (sem pontos de volta) → Recalcular do zero
    pg.evaluate("""(()=>{const ix=JSON.parse(localStorage.getItem('rp.index'));const st=JSON.parse(localStorage.getItem('rp.story.'+ix.lastId));
      st.id='legacy1'; st.title='Antiga'; st.state={lugar:'Cais',hora:'noite',presentes:'Diego',corpo:'Diego com o dedo quebrado',itens:'—',relacao:'—',pendencias:'—',saber:'—'};
      st.sloreSug=[{id:'x',name:'Dedo de Diego',keys:['dedo'],content:'quebrado'}]; st.vocab=[];
      localStorage.setItem('rp.story.legacy1',JSON.stringify(st)); ix.stories.push({id:'legacy1',title:'Antiga',updated:Date.now()+5000,count:3,chunks:0,charId:st.charId,charName:st.charName}); ix.lastId='legacy1';
      localStorage.setItem('rp.index',JSON.stringify(ix)); localStorage.removeItem('rp.ck.legacy1');})()""")
    pg.reload(); pg.wait_for_timeout(400)
    pg.click('#b-stories'); pg.wait_for_timeout(200)
    pg.locator('#stlist li', has_text='Antiga').locator('button', has_text='Abrir').click(); settle(pg)
    sl = story(pg); ok('antiga aberta (ainda contaminada)', sl['id'] == 'legacy1' and corpo(sl) == 'Diego com o dedo quebrado', corpo(sl))
    pg.click('#b-memory'); pg.wait_for_timeout(200)
    pg.click('[data-mx=st-redo]'); pg.wait_for_timeout(100)
    ok('pede confirmação', 'Confirmar' in pg.inner_text('[data-mx=st-redo]'))
    pg.click('[data-mx=st-redo]'); settle(pg)
    sl2 = story(pg)
    ok('Recalcular do zero limpa o dedo', corpo(sl2) == 'Todos inteiros', corpo(sl2))
    ok('Recalcular limpa sugestões antigas', not any(e['name'] == 'Dedo de Diego' for e in sl2.get('sloreSug', [])))
    lk = json.load(urllib.request.urlopen(M + '/last'))['messages'][-1]['content']
    ok('pedido do zero não manda o estado antigo', 'do zero' in lk and 'ESTADO ATUAL' not in lk and 'dedo quebrado' not in lk)
    pg.screenshot(path=D + 'mem_redo.png')
    pg.click('#b-close')

    # ---- backup de uma história leva os pontos de volta
    bj = pg.evaluate("""(async()=>{const r = await new Promise(res=>{const o=navigator.clipboard; res(null)}); return null})()""")
    pg.click('#b-stories'); pg.wait_for_timeout(200)
    pg.evaluate("window.__clip=null; navigator.clipboard.writeText = async t => { window.__clip = t; };")
    pg.click('#b-copy-json'); pg.wait_for_timeout(500)
    clip = pg.evaluate("window.__clip")
    bk = json.loads(clip) if clip else {}
    ok('backup inclui pontos de volta', isinstance(bk.get('ck'), dict) and isinstance(bk['ck'].get('data'), str))
    pg.fill('#paste', clip or ''); pg.click('#b-paste'); settle(pg)
    si = story(pg)
    ok('backup importado abre com pontos de volta', si['id'] != 'legacy1' and ckmap(pg) is not None, si['id'])
    pg.screenshot(path=D + 'tl_chat.png')
    print('mock calls:', mlog()[-12:])
    print('errors:', errs)
    print('FAILS:', fails)
