# Ideias e pendências da Mesa de RP

Leia isto primeiro, seja você (Kelvin) ou uma conversa nova com o Claude. Aqui fica o que já existe, o que falta testar, o que vem depois e os problemas conhecidos. Para pedir algo, escreva em **Pedidos** lá embaixo (pelo próprio GitHub, no celular: abrir o arquivo → lápis → salvar) ou diga numa conversa: "leia o IDEIAS.md do repositório Lshamann/mesa-de-rp".

## Como o app é feito

- É um app de arquivo único. A fonte está em `fonte/mesa.template.html` e o build gera três saídas:
  - `fonte/saida/mesa_rp.html`: o app dentro do Claude, publicado como artifact em https://claude.ai/artifact/MhixUeaJz8hmDmNU7YzKEB (privado do dono; usa o Claude, sem chave);
  - `fonte/saida/Mesa_de_RP_API.html`: cópia com API num arquivo só (também fica no projeto "Mesa de RP" do Claude);
  - `index.html`, `sw.js`, `manifest.webmanifest`, `bergamot-worker.js` na raiz: o site em https://lshamann.github.io/mesa-de-rp/.
- Para gerar tudo: `sh fonte/build.sh` (Python 3 e Playwright).
- Auditoria de botões: `fonte/testes/crawl.py` clica em cada controle de cada tela num Claude simulado e hostil (sem seletor de arquivo, sem confirm, cópia recusada) e aponta erros e botões mortos; `test_pro.py` cobre as saídas de emergência. Os dois usam o Claude simulado de `fonte/testes/mock_claude.py` e rodam sem servidor: `python3 fonte/testes/test_pro.py` e `python3 fonte/testes/crawl.py`.
- Testes com servidor falso em `fonte/testes/`. Rode `node fonte/testes/mockapi2.js` (porta 8788) e `python3 -m http.server 8790` na raiz, depois `python3 fonte/testes/test_tl.py` e `python3 fonte/testes/test_big.py`.
- Regras que valem sempre:
  - chaves de API, token do GitHub e senha de sincronização ficam só no aparelho; nunca entram em backup nem neste repositório;
  - histórias e personagens de quem usa nunca vêm para cá;
  - o app do Claude não acessa a internet (só o Claude); API, tradutor offline e sincronização existem só no site.

## O que já existe (até 15/11/2026)

- Modelos: Claude (dentro do Claude) ou API (OpenRouter, Gemini, Groq, DeepSeek, Mistral, OpenAI, Ollama, LM Studio, personalizada), com medidor de uso e plano B quando o limite do Claude acaba.
- Tau (v6): fala suaíli de verdade (sem tradução para o jogador), ri fácil, caça com arco; povo inspirado nos caçadores-coletores (partilha, mel com o pássaro-guia). Guia de suaíli escondido no painel Palavras. A ficha é gerada por `fonte/make_tau6.py` a partir da v5.
- Personagens: editor com IA, cards do SillyTavern, Chub, conversas .jsonl do SillyTavern, personagem a partir de imagem, elenco em grupo, teste antes de jogar e revisão da ficha.
- Memória: resumo automático, estado da cena (com "quem sabe o quê"), lore aprendida, fichas de NPC com rotina, boatos, diário em capítulos.
- Linha do tempo: Voltar, Regerar, trocar de versão, editar a última resposta e Ramificar levam o estado junto; "Recalcular do zero" para histórias antigas.
- Simulação: fome, sede, energia, higiene, necessidades, saúde, relógio, inventário realista.
- Idiomas: tradução por IA, Google e offline (Bergamot); dicionário de palavras aprendidas em cena, com níveis e revisão.
- Rosto e voz: expressões por humor que trocam sozinhas e vozes por personagem.
- Robustez (15/11/2026): quando o ambiente bloqueia a janela de arquivos, a cópia ou o download (app do Claude no celular), o app abre uma caixa para colar ou copiar à mão; Ajustes → Diagnóstico mostra ambiente e erros da sessão; rascunho da mensagem não se perde ao recarregar; renomear histórias.
- Simulação vem desligada em histórias novas (liga na tela de início, na Ficha ou em Ajustes).
- Site: login com senha, bloqueio automático e sincronização criptografada pelo GitHub (Gist secreto).

## Prosa (segundo app)

- Mensageiro em que os contatos são personagens de IA: https://lshamann.github.io/mesa-de-rp/prosa/ e artifact próprio no Claude. Fonte em `fonte/prosa/` (`python3 fonte/prosa/build.py`).
- v1 (11/11/2026): lista de conversas, balões, digitando, lida, contato criado por uma frase, importar card PNG/JSON, trazer personagens da Mesa de RP (mesmo navegador), contato que puxa assunto sozinho (espaça se ficar sem resposta), resumo automático de conversas longas, backup.
- No site usa o modelo ativo da Mesa de RP (mesmo navegador) ou um próprio em Ajustes.
- 15/11/2026: card colado como texto (Novo contato → Colar um card), Copiar backup e Restaurar do texto colado, para quando a janela de arquivos ou o download não funcionam.
- Ideias: grupos, fotos e áudios, status, notificações de verdade (precisa de servidor), sincronização como a da Mesa.
- Personagem novo: Idris dos Santos (`fonte/make_idris.py` gera o card; a foto não fica no repositório).

## Para testar jogando

- [ ] No app do Claude no celular: Histórias → Escolher arquivo abre a caixa “Trazer arquivo”? Colar o backup funciona? E copiar e baixar?
- [ ] O guia de suaíli novo (regras 🧩 e busca) ajuda a montar frases?
- [ ] O Tau fala suaíli correto, sem traduzir, e as palavras que ele ensina entram no 📖 Palavras?
- [ ] O Tau ri e provoca na medida certa (sem virar palhaço quando o perigo é real)?
- [ ] Ousmane: as fichas de NPC (Cheikh, vizinhos) e os boatos respeitam quem estava presente?
- [ ] "Recalcular do zero" na história do dedo quebrado limpou tudo?
- [ ] Sincronização entre celular e computador (e uma exclusão viajando).
- [ ] Expressões do Tau e do Ousmane trocando na conversa.
- [ ] O francês do Ousmane lido com voz francesa no "Ouvir".

## Ideias para depois

- Revisão semanal agendada que só propõe melhorias (nunca publica sozinha); depende de a ferramenta de tarefas agendadas estar disponível na conversa.
- Agenda do mundo: eventos com data (festa na sexta, barco que chega no dia 5), clima e estações.
- Mapa de lugares visitados, com quem mora ou trabalha onde.
- Exportar o diário como PDF ou ePub, com o retrato do personagem.
- Lorebook compartilhado entre personagens do mesmo mundo.
- Levar a sincronização para o app do Claude (hoje: "Copiar tudo" e colar no site).
- Rodar os testes automaticamente no GitHub a cada mudança.
- Gerar as imagens de expressão dentro do app, se surgir um gerador disponível.

## Problemas conhecidos

- No app do Claude no celular a janela de escolher arquivo não abre: cards em .png não entram por lá (use o .json colado, ou o navegador, ou o site). Isso foi confirmado só em ambiente simulado; se algum botão ainda falhar, mande o relatório de Ajustes → Diagnóstico.
- Pontos de volta só existem a partir da atualização de 07/11/2026; em histórias anteriores, use Memória → Recalcular do zero.
- Ramos criados antes de 07/11/2026 não aparecem na árvore de Histórias.
- Sincronização: se a mesma história mudou em dois aparelhos, fica a versão mais nova inteira (não mescla mensagens).
- O tradutor offline depende do espelho dos modelos no Hugging Face.
- Nos testes antigos de mock, `test_feat.py` trava no clique de lore (limitação do mock, não do app).

## Pedidos

<!-- Escreva aqui o que quer mudar, um por linha. Ex.: - O Tau esquece o nome da irmã depois de muitas mensagens. -->
