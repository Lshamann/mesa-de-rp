# Claude simulado para os testes: window.claude (sample, db, downloads, user) falso, dentro do Playwright.
# Usado por crawl.py e test_pro.py. O app testado é fonte/saida/mesa_rp.html (ou a variável MESA_APP).
import json, re
from playwright.sync_api import sync_playwright
import os
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
APP = os.environ.get('MESA_APP') or os.path.join(HERE, '..', 'saida', 'mesa_rp.html')
D = HERE + os.sep
SK = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
html = SK + open(APP, encoding='utf-8').read() + '</body></html>'
MOCK = r"""
(() => {
  window.__calls = []; window.__saved = [];
  const store = window.__db = new Map();
  const mkDoc = path => ({ path,
    async get(){ const v = store.get(path); return {exists: v !== undefined, data: () => v === undefined ? undefined : JSON.parse(JSON.stringify(v))}; },
    async set(d){ store.set(path, JSON.parse(JSON.stringify(d))); },
    async delete(){ store.delete(path); },
    collection(n){ return mkCol(path + '/' + n); } });
  const mkCol = path => ({ doc(id){ return mkDoc(path + '/' + id); } });
  const db = { doc: p => mkDoc(p), collection: p => mkCol(p) };
  let n = 0;
  const FULL = {name:"Dra. Marta Lessa", role:"char", tagline:"Médica de um barco de pesca em alto-mar, cansada e prática.",
    description:"Marta tem 41 anos, pele castigada de sal, mãos firmes e voz rouca. Cuida da tripulação do Estrela do Sul há nove anos.",
    personality:"Prática, sarcástica, teimosa. Confia devagar.", scenario:"Três dias de mar, um náufrago a bordo e o rádio quebrado.",
    rules:"Não escreva nada por {{user}}. Ritmo lento, realismo.",
    openings:[{label:"Convés ao amanhecer", text:"*Marta enxuga as mãos num pano e olha para o homem deitado no convés.* \"Ainda respira\", diz."},{label:"Enfermaria", text:"*A luz da enfermaria balança com o mar.*"},{label:"Rádio quebrado", text:"*O rádio solta um chiado e morre.*"}],
    example_dialogue:"{{user}}: Onde estou?\n{{char}}: *Marta ergue uma sobrancelha.* \"Num barco. Bebe isso.\"\n---\n{{user}}: Obrigado.\n{{char}}: \"Guarda o agradecimento.\"",
    lore:[1,2,3,4,5,6].map(i => ({name:"Entrada "+i, keys:["barco","mar","rede"+i], content:"Fato do mundo número "+i+" sobre o barco.", always: i===1})),
    persona:{name:"Teo", pro:"ele", look:"Magro, barba por fazer.", bio:"Marinheiro de primeira viagem.", extra:"Só a roupa do corpo."}};
  const sample = async (input, opts = {}) => {
    window.__calls.push({input: JSON.parse(JSON.stringify(input)), tier: opts.modelTier});
    n++;
    if (typeof input === 'string') {
      if (window.__badjson) return {text: 'não é json', truncated:false};
      if (input.includes('Escreva 3 aberturas')) return {text: JSON.stringify([{label:'A',text:'*Abertura A.*'},{label:'B',text:'*Abertura B.*'},{label:'C',text:'*Abertura C.*'}]), truncated:false};
      if (input.includes('Escreva 6 a 8 entradas')) return {text: '```json\n' + JSON.stringify([{name:'L1',keys:['x','y'],content:'conteudo 1'},{name:'L2',keys:['z'],content:'conteudo 2'}]) + '\n```', truncated:false};
      if (input.includes('designer de personagens')) { if (opts.onText) opts.onText({text:'{"name"', delta:''}); return {text: JSON.stringify(FULL), truncated:false}; }
      if (input.includes('Corrija a frase que o aluno')) return {text: JSON.stringify(window.__scres || {ok:false, corrigida:'Ninakula chakula.', pt:'Eu como comida.', erros:[{errado:'Nakula', certo:'Ninakula', regra:'Falta o prefixo ni- (eu) e o -na- (agora).'}], dica:'Comece sempre pelo prefixo da pessoa.'}), truncated:false};
      return {text:'- Resumo: os dois se conheceram.', truncated:false};
    }
    const full = `*Ela inclina a cabeça e observa por um longo instante.* "Ka-ru." [som de trovão]\n\n*Dá um passo atrás, esperando.* (resposta ${n})`;
    if (opts.onText) { for (let i = 20; i < full.length; i += 40) opts.onText({text: full.slice(0, i), delta: ''}); opts.onText({text: full, delta: ''}); }
    return {text: full, truncated: false};
  };
  window.claude = { use: async name => ({sample, db, user: {id: async () => 'u1'}, downloads: {save: async r => { window.__saved.push(r); return {status: 'saved'}; }}})[name] || null };
})();
"""
