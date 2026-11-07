// mock para linha do tempo + palavras (porta 8788)
const http = require('http');
let last = null, lastChat = null, log = [], n = 0;
const NPC = {npcs:[{nome:'Diego', aparencia:'magro, uns 30 anos, mãos de pescador', jeito:'fala rápido e baixo', rotina:'no cais de manhã cedo', sabe:'sabe da briga; não sabe quem é Kelvin', acha:'tem medo de Kelvin'}], boatos:[{fato:'Kelvin quebrou o dedo de Diego', sabem:['Diego','Tau'], pode_chegar:['Cheikh'], como:'pescadores do cais', distorcao:'que foi de propósito'}]};
const after = (u, tag) => { const i = u.indexOf(tag); return i < 0 ? '' : u.slice(i + tag.length); };
http.createServer((q, r) => {
  const H = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'};
  if (q.method === 'OPTIONS') { r.writeHead(204, H); return r.end(); }
  if (q.url === '/log') { r.writeHead(200, {...H, 'Content-Type': 'application/json'}); return r.end(JSON.stringify(log)); }
  if (q.url === '/reset') { log = []; r.writeHead(200, H); return r.end('ok'); }
  if (q.url === '/lastchat') { r.writeHead(200, {...H, 'Content-Type': 'application/json'}); return r.end(JSON.stringify(lastChat)); }
  if (q.url === '/last') { r.writeHead(200, {...H, 'Content-Type': 'application/json'}); return r.end(JSON.stringify(last)); }
  let b = ''; q.on('data', d => b += d); q.on('end', () => {
    const j = JSON.parse(b); last = j;
    const u = j.messages[j.messages.length - 1].content;
    if (j.messages.length > 1) lastChat = j;
    let out, kind;
    if (/anotador de continuidade/.test(u)) {
      kind = /do zero/.test(u) ? 'keeper-fresh' : 'keeper';
      const msgs = after(u, 'MENSAGENS RECENTES:');
      const dedo = /dedo quebrou/i.test(msgs);
      const o = {estado: {lugar: 'Beira do rio', hora: 'manhã', presentes: 'Tau, Kelvin, Diego', corpo: dedo ? 'Diego com o dedo quebrado' : 'Todos inteiros', itens: '—', relacao: 'tensa', pendencias: '—', saber: dedo ? 'Tau viu a briga' : '—'},
        lore: dedo ? [{name: 'Dedo de Diego', keys: ['Diego', 'dedo'], content: 'Diego quebrou o dedo na briga perto do rio.'}] : []};
      if (/"npcs"/.test(u) && dedo) Object.assign(o, NPC);
      if (/"vocab"/.test(u) && /Mabi/.test(msgs)) o.vocab = [{palavra: 'Mabi', significado: 'água', idioma: 'namaru', quem: 'Kelvin', como: 'Tau apontou o rio'}];
      out = JSON.stringify(o);
    } else if (/estado inicial da simulação/.test(u)) {
      kind = 'siminit';
      out = JSON.stringify({hora: '07:30', dia: 3, status: {Kelvin: {saude: 85, fome: 60, sede: 60, energia: 70, higiene: 50, bexiga: 80}, Tau: {saude: 100, fome: 70, sede: 80, energia: 75, higiene: 60, bexiga: 80}},
        itens: [{name: 'Calça cargo', size: 'M', kg: 0.6, where: 'pernas', wear: 'pernas', cap: {vol: 2, max: 'P'}}, {name: 'Camisa', size: 'M', kg: 0.3, where: 'torso', wear: 'torso'}, {name: 'Faca', size: 'P', kg: 0.2, where: 'Calça cargo'}]});
    } else if (/motor de simulação/.test(u)) {
      kind = 'sim';
      const nar = after(u, 'NARRAÇÃO:');
      const dedo = /dedo quebrou/i.test(nar);
      const o = dedo ? {minutos: 30, efeitos: {Kelvin: {saude: -15}}, inventario: [{op: 'add', name: 'Tala', size: 'P', kg: 0.1, to: 'auto'}]} : {minutos: 10, inventario: []};
      if (/"estado"/.test(u)) o.estado = {lugar: 'Beira do rio', hora: 'manhã', presentes: 'Tau, Kelvin', corpo: dedo ? 'Diego com o dedo quebrado' : 'Todos inteiros', itens: '—', relacao: 'tensa', pendencias: '—', saber: '—'}, o.lore = [];
      if (/"npcs"/.test(u) && dedo) Object.assign(o, NPC);
      if (/"vocab"/.test(u) && /Mabi/.test(nar)) o.vocab = [{palavra: 'Mabi', significado: 'água', idioma: 'namaru', quem: 'Kelvin', como: 'Tau apontou o rio'}];
      out = JSON.stringify(o);
    } else if (/Você registra as palavras/.test(u)) {
      kind = 'vocab';
      out = JSON.stringify({vocab: /Mabi/.test(u) ? [{palavra: 'Mabi', significado: 'água', idioma: 'namaru', quem: 'Kelvin', como: 'Tau apontou o rio'}] : []});
    } else if (/cronista de um roleplay/.test(u)) { kind = 'diary'; out = JSON.stringify({titulo:'A briga no rio', texto:'Kelvin chegou ao rio e encontrou Tau de lança baixa. A conversa começou em silêncio e terminou com Diego segurando a mão machucada.'}); }
    else if (/revisa fichas de personagens/.test(u)) { kind = 'review'; out = JSON.stringify([{onde:'Cenário', problema:'Não diz o que Tau quer nesta cena.', sugestao:'Dê a ele um objetivo imediato.'},{onde:'Aberturas', problema:'A abertura 2 decide a reação do jogador.', sugestao:'Termine antes da reação.'}]); }
    else if (/memória de um roleplay/.test(u)) { kind = 'summary'; out = '- Resumo.'; }
    else {
      kind = 'chat'; n++;
      const said = u.split('\n\n---\n')[0];
      if (/quebro o dedo/i.test(said)) out = `*Diego grita quando o dedo estala.* "Meu dedo quebrou!" *Tau recua um passo.* (v${n})`;
      else if (/ensina|como se diz/i.test(said)) out = `*Tau aponta o rio e repete devagar:* "Mabi." *Depois leva a mão em concha à boca, como quem bebe.* (v${n})`;
      else if (/provoco/i.test(said)) out = `*Tau estreita os olhos, desconfiado, e não abaixa a lança.* (v${n})`;
      else if (/mabi/i.test(said)) out = `*Tau sorri ao ouvir "mabi" e passa a cuia cheia.* (v${n})`;
      else out = `*Tau observa em silêncio, a lança baixa.* (resposta ${n})`;
    }
    log.push(kind);
    r.writeHead(200, {...H, 'Content-Type': 'text/event-stream'});
    const parts = out.match(/[\s\S]{1,8}/g); let i = 0;
    const t = setInterval(() => {
      if (i < parts.length) r.write('data: ' + JSON.stringify({choices: [{delta: {content: parts[i++]}}]}) + '\n\n');
      else { r.write('data: ' + JSON.stringify({choices: [{delta: {}, finish_reason: 'stop'}]}) + '\n\ndata: [DONE]\n\n'); r.end(); clearInterval(t); }
    }, 3);
  });
}).listen(8788, () => console.log('mock2 up'));
