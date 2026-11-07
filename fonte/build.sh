#!/bin/sh
# Gera as três saídas a partir de mesa.template.html:
#   saida/mesa_rp.html        -> app dentro do Claude (artifact)
#   saida/Mesa_de_RP_API.html -> cópia com API (arquivo único)
#   ../index.html etc.        -> site no GitHub Pages
cd "$(dirname "$0")" || exit 1
HOSTED_URL=https://lshamann.github.io/mesa-de-rp/ python3 build_mesa.py && python3 make_standalone.py && python3 make_site.py && rm -f ../.nojekyll
