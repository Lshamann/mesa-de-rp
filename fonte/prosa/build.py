import os
B = os.path.dirname(os.path.abspath(__file__)); src = open(os.path.join(B, 'prosa.src.html'), encoding='utf8').read()
os.makedirs(os.path.join(B, 'saida'), exist_ok=True)
open(os.path.join(B, 'saida', 'prosa.html'), 'w', encoding='utf8').write(src)
page = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#c8472d"><style>html{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>\n' + src + '\n</body></html>'
site = os.environ.get('PROSA_SITE', os.path.join(B, 'saida', 'site')); os.makedirs(site, exist_ok=True)
open(os.path.join(site, 'index.html'), 'w', encoding='utf8').write(page); print('ok', len(src) // 1024, 'KiB')
