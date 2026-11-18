#!/bin/sh
# Roda todos os testes que não precisam de servidor, numa build de teste (com um personagem fictício de id "tau").
# Ao final refaz a build de verdade, sem personagem embutido. Uso: sh fonte/testes/rodar_tudo.sh
cd "$(dirname "$0")/../.." || exit 1
R=$(pwd)
TEST_CHAR=$R/fonte/testes/fixtures/personagem_teste.json sh fonte/build.sh > /dev/null || exit 1
fail=0
for t in test_pro test_pins test_chars test_srs test_misc; do
  echo "== $t"
  out=$(timeout 600 python3 fonte/testes/$t.py 2>&1); echo "$out" | grep -v "^PASS" | tail -12
  p=$(echo "$out" | grep -c "^PASS"); f=$(echo "$out" | grep -c "^FAIL\|Traceback\|FAILS: \[.\+\]")
  echo "$t: $p ok, $f falhas"; [ "$f" -gt 0 ] && fail=1
done
echo "== crawl (auditoria de botões)"
out=$(timeout 1800 python3 fonte/testes/crawl.py 2>&1); echo "$out" | grep "^ACHADO\|NÃO ENTROU\|Traceback" | head -20
n=$(echo "$out" | grep -c "^ACHADO\|Traceback"); echo "crawl: $n achados"; [ "$n" -gt 0 ] && fail=1
sh fonte/build.sh > /dev/null
[ "$fail" -eq 0 ] && echo "TUDO OK" || echo "HÁ FALHAS"
exit $fail
