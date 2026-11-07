import os
BASE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE, 'saida'), exist_ok=True)
s=open(os.path.join(BASE, 'saida', 'mesa_rp.html'),encoding='utf8').read()
reset=':root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}'
doc='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>'+reset+'</style></head><body>\n'+s+'\n</body></html>'
open(os.path.join(BASE, 'saida', 'Mesa_de_RP_API.html'),'w',encoding='utf8').write(doc); print(len(doc))
