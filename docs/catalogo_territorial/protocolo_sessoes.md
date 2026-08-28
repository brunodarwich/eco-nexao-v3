# Protocolo obrigatório das sessões ECO-25XX

## 1. Início e `/goal`

Cada prompt começa com `/goal` e define um único resultado observável. Se o ambiente
não reconhecer o comando, o agente deve tratá-lo como declaração explícita de meta,
sem criar uma automação ou executar outra task. Uma sessão executa somente uma
ECO-25XX e não antecipa a seguinte.

## 2. Leitura e mini-brief

O agente raiz lê integralmente AGENTS, `docs/README.md`, spec, playbook, este pacote,
o prompt da task e todas as referências citadas. Antes de editar, publica o mini-brief
de `docs/ai_task_playbook.md`. Subagente não substitui essa leitura.

## 3. Subagentes proporcionais

- Tasks S documentais: agente raiz; `revisor` somente leitura obrigatório.
- Tasks M: `planejador` somente leitura → raiz/implementador → `testador` → `revisor`.
- Tasks L, migrations, ingestão, Google ou mídia: `planejador` → `implementador` →
  `testador` → `revisor` → `consolidador`, sempre sequenciais, um ativo por vez.
- Nenhum subagente cria outros. O agente raiz lê instruções de skills pessoalmente.
- Finding P0/P1 volta ao implementador; testes e revisão afetados são repetidos.

## 4. `/browser`, web e skills

- `/browser` significa usar o Browser skill para inspeção visual/interativa quando o
  prompt exigir Google Console, mapa web ou evidência renderizada. Não autoriza login,
  criação de chave, billing, upload, alteração ou acesso production.
- Documentação e changelog atuais Google/Supabase devem ser consultados antes de
  implementar essas integrações. Em pesquisa técnica, usar fontes oficiais.
- Use a skill `browser:control-in-app-browser` para UI web; `spreadsheets` apenas para
  gerar/analisar artefato tabular solicitado; `imagegen` não se aplica a fotos Google;
  `computer-use` somente se uma aplicação Windows for explicitamente necessária.
- Se uma skill for usada, anunciar o motivo e cumprir integralmente seu `SKILL.md`.

## 5. Segurança, dados e paradas

- `C:\Users\Bruno\Downloads\teste-rota` é somente leitura.
- Nenhum segredo, token, DSN, Place payload pessoal ou foto é colocado em prompt/log.
- Nenhuma chamada Google em CI; staging smoke requer autorização explícita.
- Não inventar Place ID. Fuzzy match somente cria candidato.
- Conteúdo Google não é copiado para Storage; fotos usam o modelo de proxy aceito.
- Não exibir Places em mapa incompatível com as políticas vigentes.
- Migration é criada pela Supabase CLI instalada, nunca por timestamp inventado.
- Parar em ADR aberto, falta de direitos, custo/billing, produção ou escrita remota
  destrutiva.

## 6. Entrega

Usar o formato do playbook, acrescentando: status, hashes/contagens, gates humanos,
verificações Google/atribuição/custo, privacidade, rollback e próxima task. `VERIFIED`
exige reprodução independente no ambiente adequado.
