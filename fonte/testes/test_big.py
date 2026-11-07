import os
HERE = os.path.dirname(os.path.abspath(__file__))
APP = 'file://' + os.path.join(os.path.dirname(HERE), 'saida', 'Mesa_de_RP_API.html')
import json, time, urllib.request, re
from playwright.sync_api import sync_playwright
D = os.path.join(HERE, 'out') + '/'; os.makedirs(D, exist_ok=True)
M = 'http://localhost:8788'
errs = []; fails = []
def ok(label, cond, extra=''):
    print(('PASS ' if cond else 'FAIL ') + label + (('  ' + str(extra)[:300]) if extra != '' else ''))
    if not cond: fails.append(label)
def mlog(): return json.load(urllib.request.urlopen(M + '/log'))
def settle(pg, quiet=1.0, cap=25):
    t0 = time.time(); pg.wait_for_selector('#b-stop', state='hidden', timeout=20000)
    n = len(mlog()); t = time.time()
    while time.time() - t0 < cap:
        time.sleep(0.25); k = len(mlog())
        if k != n: n = k; t = time.time()
        elif time.time() - t > quiet: break
    pg.wait_for_timeout(700)
def story(pg): return pg.evaluate("(()=>{const ix=JSON.parse(localStorage.getItem('rp.index'));return JSON.parse(localStorage.getItem('rp.story.'+ix.lastId))})()")
def send(pg, text): pg.fill('#in', text); pg.click('#b-send'); settle(pg)
SETUP = """localStorage.clear();localStorage.setItem('rp.models', JSON.stringify({active:'a',list:[{id:'a',preset:'custom',name:'Mock',base:'http://localhost:8788/v1',key:'k',model:'m',ctx:32000}]}));localStorage.setItem('rp.me',JSON.stringify({name:'Kelvin',pro:'ele'}))"""

# ---------- GitHub falso ----------
GIST = {}
def gh_route(route):
    req = route.request; url = req.url; meth = req.method
    H = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET,POST,PATCH,OPTIONS'}
    if meth == 'OPTIONS': return route.fulfill(status=204, headers=H)
    if req.headers.get('authorization') != 'Bearer ghp_' + 'x' * 36: return route.fulfill(status=401, headers=H, body='{}')
    def js(o, st=200): route.fulfill(status=st, headers=dict(H, **{'Content-Type': 'application/json'}), body=json.dumps(o))
    now = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) + '.%03dZ' % (int(time.time() * 1000) % 1000)
    path = url.split('api.github.com')[1]
    if path == '/user': return js({'login': 'Lshamann'})
    if path.startswith('/gists?'): return js([{'id': k, 'files': {f: {} for f in v['files']}} for k, v in GIST.items()])
    if path == '/gists' and meth == 'POST':
        b = json.loads(req.post_data); gid = 'g%d' % (len(GIST) + 1)
        GIST[gid] = {'files': {k: v['content'] for k, v in b['files'].items()}, 'updated_at': now}
        return js({'id': gid, 'updated_at': now}, 201)
    m = re.match(r'/gists/(\w+)$', path)
    if m:
        g = GIST.get(m.group(1))
        if not g: return js({}, 404)
        if meth == 'PATCH':
            b = json.loads(req.post_data)
            for k, v in b['files'].items(): g['files'][k] = v['content']
            g['updated_at'] = now
        return js({'id': m.group(1), 'updated_at': g['updated_at'], 'files': {k: {'content': c, 'truncated': False} for k, c in g['files'].items()}})
    return js({}, 404)
TOKEN = 'ghp_' + 'x' * 36

with sync_playwright() as p:
    b = p.chromium.launch()
    def dev(scheme='light'):
        ctx = b.new_context(viewport={'width': 400, 'height': 820}, color_scheme=scheme)
        ctx.route('https://api.github.com/**', gh_route)
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'fonts' not in m.text and 'ERR_' not in m.text and 'Failed to load resource' not in m.text else None)
        return pg
    A = dev()
    A.goto('http://localhost:8790/'); A.wait_for_timeout(400); A.evaluate(SETUP); A.reload(); A.wait_for_timeout(500)
    A.click('[data-act=quick][data-id=tau]'); settle(A)

    # ---------- NPCs e boatos ----------
    send(A, '*Olho em volta.*')
    send(A, '*Eu quebro o dedo do Diego.*')
    A.click('#b-memory'); A.wait_for_timeout(200); A.click('[data-mx=st-up]'); settle(A); A.click('#b-close')
    s = story(A)
    npcs = s.get('npcs', []); rum = s.get('rumors', [])
    ok('ficha do Diego criada', any(x['name'] == 'Diego' and 'cais' in x.get('rotina', '') for x in npcs), npcs)
    ok('boato registrado', rum and rum[0]['fato'].startswith('Kelvin quebrou') and 'Cheikh' in rum[0]['pode'], rum)
    send(A, '*Espero.*')
    hdr = json.load(urllib.request.urlopen(M + '/lastchat'))['messages'][0]['content']
    ok('narrador recebe PESSOAS e BOATOS', 'PESSOAS DA HISTÓRIA' in hdr and '- Diego:' in hdr and 'BOATOS' in hdr and 'Cheikh' in hdr)
    A.click('#b-memory'); A.wait_for_timeout(200)
    txt = A.inner_text('#mem-extra')
    ok('Memória mostra pessoas e boatos', 'Diego' in txt and 'Kelvin quebrou o dedo' in txt)
    A.locator('.pdet summary', has_text='Diego').click()
    nid = [x for x in npcs if x['name'] == 'Diego'][0]['id']
    A.fill('#np-notas-' + nid, 'Deve dinheiro ao Cheikh'); A.click('[data-px=np-save][data-id="%s"]' % nid); A.wait_for_timeout(700)
    ok('editar ficha salva', any(x.get('notas') == 'Deve dinheiro ao Cheikh' for x in story(A).get('npcs', [])))
    A.screenshot(path=D + 'big_people.png')
    A.click('#b-close')

    # ---------- diário ----------
    A.click('#b-stories'); A.wait_for_timeout(200); A.click('#b-diary'); A.wait_for_timeout(200)
    A.click('[data-dx=write]'); settle(A)
    ok('capítulo escrito', 'A briga no rio' in A.inner_text('#diary-box'), A.inner_text('#diary-box')[:120])
    ok('capítulo guardado na história', (story(A).get('diary') or [{}])[0].get('title') == 'A briga no rio')
    A.screenshot(path=D + 'big_diary.png')
    A.click('#b-close')

    # ---------- humor e expressão ----------
    A.click('#b-home'); A.wait_for_timeout(300)
    A.locator('#lib [data-act=look][data-id=tau]').click(); A.wait_for_timeout(300)
    ok('painel Rosto e voz abre', 'Expressões de Tau' in A.inner_text('#look-box'))
    with A.expect_file_chooser() as fc: A.locator('[data-lx=up][data-k=desconfiado]').click()
    fc.value.set_files(os.path.join(os.path.dirname(HERE), 'avatar.jpg')); A.wait_for_timeout(800)
    ok('expressão salva', 'Trocar' in A.locator('.xcell', has_text='Desconfiado').inner_text())
    A.screenshot(path=D + 'big_look.png')
    A.click('#b-close'); A.locator('[data-act=resume]').first.click() if A.locator('[data-act=resume]').count() else None
    A.wait_for_timeout(400)
    if A.is_visible('#v-library'): A.click('#b-stories'); A.wait_for_timeout(200); A.locator('#stlist li').first.locator('button', has_text='Abrir').click(); A.wait_for_timeout(500)
    send(A, '*Eu provoco o Tau.*')
    av = A.locator('#msgs .msg.tau').last.locator('.who .mini')
    ok('avatar troca para a expressão do humor', 'url(' in (av.get_attribute('style') or ''), av.get_attribute('title'))
    A.locator('#msgs .msg.tau').last.locator('[data-act=speak]').click(); A.wait_for_timeout(300)

    # ---------- ramos em árvore ----------
    A.locator('#msgs .msg.tau').nth(1).locator('[data-act=branch]').click(); settle(A)
    A.click('#b-stories'); A.wait_for_timeout(300)
    lis = A.locator('#stlist li')
    ok('ramo aparece recuado sob a original', lis.count() == 2 and 'branch' in (lis.nth(1).get_attribute('class') or '') and 'ramo a partir de' in lis.nth(1).inner_text(), [lis.nth(i).inner_text()[:80] for i in range(lis.count())])
    A.screenshot(path=D + 'big_tree.png')
    A.click('#b-close')

    # ---------- teste de personagem ----------
    A.click('#b-home'); A.wait_for_timeout(300)
    A.locator('#lib [data-act=dup][data-id=tau]').click(); A.wait_for_timeout(400)
    A.locator('#try-sect').scroll_into_view_if_needed()
    A.fill('#try-in', '*Ergo as mãos devagar.*'); A.click('[data-ty=send]'); settle(A)
    tl = A.inner_text('#try-log')
    ok('conversa de teste responde', 'Tau observa' in tl and 'Ergo as mãos' in tl, tl[:200])
    A.click('[data-ty=review]'); settle(A)
    ok('revisão da ficha lista problemas', 'objetivo imediato' in A.inner_text('#try-sect'))
    A.locator('#try-sect').screenshot(path=D + 'big_try.png')
    A.click('#b-home'); A.wait_for_timeout(300)

    # ---------- sincronização ----------
    A.click('#b-settings'); A.wait_for_timeout(200)
    A.fill('#sy-token', TOKEN); A.fill('#sy-p1', 'segredo123'); A.fill('#sy-p2', 'segredo123')
    A.click('[data-sy=connect]'); A.wait_for_timeout(4000)
    ok('A conectou e criou gist criptografado', len(GIST) == 1 and 'Conectado como @Lshamann' in A.inner_text('#sync-box'), A.inner_text('#sync-box')[:150])
    content = list(GIST.values())[0]['files']['mesa-rp.sync.json']
    ok('conteúdo no GitHub é ilegível', 'Kelvin' not in content and 'Diego' not in content and json.loads(content)['app'] == 'mesa-rp')
    A.screenshot(path=D + 'big_sync.png')
    nA = A.evaluate("JSON.parse(localStorage.getItem('rp.index')).stories.length")

    B = dev('dark')
    B.goto('http://localhost:8790/'); B.wait_for_timeout(400); B.evaluate(SETUP); B.reload(); B.wait_for_timeout(500)
    B.click('#b-settings'); B.wait_for_timeout(200)
    B.fill('#sy-token', TOKEN); B.fill('#sy-p1', 'errada999'); B.fill('#sy-p2', 'errada999'); B.click('[data-sy=connect]'); B.wait_for_timeout(3000)
    ok('senha errada é recusada', 'senha de criptografia não abre' in B.inner_text('#sync-box'), B.inner_text('#sy-msg'))
    B.fill('#sy-p1', 'segredo123'); B.fill('#sy-p2', 'segredo123'); B.click('[data-sy=connect]'); B.wait_for_timeout(5000)
    nB = B.evaluate("JSON.parse(localStorage.getItem('rp.index')).stories.length")
    ok('B recebeu as histórias de A', nB == nA and nB == 2, (nA, nB))
    looksB = B.evaluate("JSON.parse(localStorage.getItem('rp.index')).looks || {}")
    ok('B recebeu a expressão do Tau', 'desconfiado' in (looksB.get('tau', {}).get('expr') or {}))
    B.click('#b-close'); B.click('#b-stories'); B.wait_for_timeout(300)
    B.locator('#stlist li').nth(1).locator('button', has_text='Excluir').click(); B.locator('#stlist li').nth(1).locator('button', has_text='Confirmar').click(); B.wait_for_timeout(600)
    B.click('#b-close'); B.click('#b-settings'); B.wait_for_timeout(200); B.click('[data-sy=now]'); B.wait_for_timeout(3000)
    A.click('[data-sy=now]'); A.wait_for_timeout(3500)
    nA2 = A.evaluate("JSON.parse(localStorage.getItem('rp.index')).stories.length")
    ok('exclusão em B chega em A', nA2 == 1, nA2)
    B.screenshot(path=D + 'big_sync_dark.png')
    print('mock calls:', mlog()[-10:])
    print('errors:', errs)
    print('FAILS:', fails)
