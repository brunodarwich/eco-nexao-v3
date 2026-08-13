# Plano executável de implementação

## Resultado esperado

Entregar um ECOnexão operável por equipe editorial, populado com Pindobal,
homologado em staging para Android/iOS/Web e publicado somente após gates de
segurança, conteúdo, LGPD, backup e rollback. Nenhum marco posterior corrige
silenciosamente uma decisão aberta de marco anterior.

## Princípios de sequência

- Primeiro reparar a fonte de verdade e separar ambientes.
- Depois fixar autorização/editorial e Storage antes de criar superfícies admin.
- Implementar persistência do importador antes de popular qualquer ambiente.
- Construir API administrativa antes do painel.
- Fechar dados/mídia reais antes da homologação do app público.
- Staging precede todo teste E2E e toda ação de production.
- Production e lojas exigem aprovação humana explícita.

## Marcos orientados a resultado

| Marco | Resultado verificável | Tasks | Gate liberado |
|---|---|---|---|
| 13 — Baseline e decisões | Worktree íntegro, baseline reproduzível e ADRs humanos aceitos | ECO-1301–1306 | início seguro |
| 14 — Ambientes e segurança editorial | 4 ambientes identificados, test isolado, RBAC/auditoria/Storage seguros | ECO-1401–1404 | Gate 2 parcial |
| 15 — Pindobal importável | `--apply` transacional/idempotente, relatório e carga dupla em test | ECO-1501–1505 | Gate 1 |
| 16 — API administrativa | CRUD, publish guard, reconciliação, bulk/export e autorização | ECO-1601–1605 | Gate 2 |
| 17 — Mídia real | avatar e mídia editorial processados, resolvidos e testados | ECO-1701–1704 | Gate 2 |
| 18 — Painel editorial | editores operam conteúdo, mídia, revisão e publicação sem SQL | ECO-1801–1804 | Gate 2 |
| 19 — App público fechado | Sem dados fabricados, auth/preferências/trips/offline/deep links completos | ECO-1901–1905 | Gate 3 |
| 20 — Staging operável | container, CI/CD, web/domain, observabilidade e runbooks | ECO-2001–2004 | Gate 4 |
| 21 — Homologação | E2E e aceite Android/iOS/Web, segurança, LGPD, carga e conteúdo | ECO-2101–2104 | Gates 5–6 |
| 22 — Produção e operação | go/no-go, promoção controlada, distribuição e operação assistida | ECO-2201–2205 | Gates 7–8 |

## Caminho crítico

```text
ECO-1301
  → ECO-1302/1303/1304/1305/1306
  → ECO-1401 → ECO-1402/1403/1404
  → ECO-1501 → ECO-1502 → ECO-1503 → ECO-1504 → ECO-1505
  → ECO-1601 → ECO-1602/1603 → ECO-1604/1605
  → ECO-1701/1702 → ECO-1703 → ECO-1704
  → ECO-1801 → ECO-1802/1803 → ECO-1804
  → ECO-1901/1902/1903/1904 → ECO-1905
  → ECO-2001 → ECO-2002/2003/2004
  → ECO-2101/2102/2103 → ECO-2104
  → ECO-2201 → ECO-2202 → ECO-2203 → ECO-2204 → ECO-2205
```

O caminho crítico não significa serializar tudo. O grafo e a matriz de conflitos
estão em `dependency_graph.md`.

## Estratégia de incrementos verticais

### Marco 13 — Reconciliação e decisões

Recriar/obter um clone Git íntegro, registrar commit baseline, corrigir a separação
local test/dev e reproduzir pytest em ambiente limpo. Em paralelo, o owner decide
provedor, operação editorial, identidade, mídia/licenciamento e itens de lançamento.
Nenhuma migration editorial ou infra deve começar antes dos ADRs correspondentes.

### Marco 14 — Ambientes e segurança

Provisionar development/test/staging/production com referências não secretas e
credenciais separadas. Corrigir a migration de Storage antes de promovê-la. Criar
roles editoriais fora de `auth`, com memberships mínimos, audit trail e testes A/B.
Definir backups, restore drills, secret manager e conta break-glass.

### Marco 15 — Pindobal

Fazer `--apply` falhar fechado sem sessão, implementar unit of work, persistência e
relatório. Idempotência deve ser provada por duas execuções no test, com snapshot
hash-equal e zero duplicação. Somente depois gerar pacote de promoção para staging;
casos fuzzy permanecem pendentes de revisão.

### Marco 16 — API administrativa

Congelar contrato `/api/v1/admin`, autorização por capability, paginação e
idempotência. Implementar CRUD por agregados coerentes e publish guard que bloqueie
conteúdo incompleto. Bulk import/export e jobs devem ser assíncronos, observáveis e
auditados. Rotas continuam sem SQL direto.

### Marco 17 — Mídia

Substituir URLs/tokens fabricados pelo fluxo oficial do Supabase Storage. Validar
bytes, dimensões e MIME; remover EXIF; gerar derivados; exigir alt/crédito/licença
conforme ADR. Resolver URLs no backend, evitar overwrite de path e reconciliar
órfãos. Testar INSERT/SELECT/UPDATE/DELETE com usuário A/B/editor.

### Marco 18 — Painel

O painel usa apenas a API administrativa. Cada editor declara lock/versão, vê erros
de validação, salva rascunho, solicita revisão e publica somente quando o backend
autoriza. Histórico/auditoria é legível, mas não alterável. Exportações têm checksum.

### Marco 19 — Aplicativo público

Remover adapters que inventam dados, consumir paginação, resolver mídia e favorito
real. Completar conta guest→permanente, preferências aplicadas, trips/visitas,
consentimento e comportamento offline explícito. Fechar package/bundle IDs,
deep links e conteúdo legal aprovado sem atualizar Expo.

### Marco 20 — Staging

Produzir imagem Linux imutável, startup/readiness, migrations pré-deploy e rollback.
Deployar staging no provedor aceito, web com domínio/CORS e observabilidade. CI gera
artefatos, SBOM, scan, approvals e smoke tests; qualidade sem deploy continua sendo
apenas CI.

### Marco 21 — Homologação

Executar E2E em staging e dispositivos/navegadores reais. Reproduzir toda matriz de
aceite, acessibilidade, rede degradada, performance, segurança, LGPD, Google e
conteúdo. Falha P0 reabre a task dona e impede go/no-go.

### Marco 22 — Produção

Owner aprova go/no-go, janela, backup e rollback. Migrations e conteúdo são
promovidos com evidência e sem credenciais em prompts. Publicação web/EAS/lojas é
separada da carga de dados. Operação assistida encerra somente após SLOs estáveis e
um exercício de rollback/restore compatível.

## Primeiras tasks recomendadas

1. **ECO-1301** — restaurar fonte de verdade Git, ambiente test isolado e baseline
   reproduzível; é pré-condição de qualquer paralelismo.
2. **ECO-1302** — escolher formalmente provedor de contêiner e topologia de deploy.
3. **ECO-1303** — decidir workflow editorial, RBAC, política de publicação e painel.
4. **ECO-1304** — decidir identidade guest→conta, web session e ciclo LGPD.
5. **ECO-1305** — decidir privacidade/licenças/derivados e exposição de mídia.

ECO-1302–1305 podem ocorrer em paralelo depois do pacote de evidências da ECO-1301,
desde que cada ADR tenha owner e arquivos exclusivos.

## Métricas de conclusão

- 100% das tasks P0 com evidência reproduzível.
- Zero dados fabricados apresentados como reais.
- Zero migrations em drift entre repositório e ambiente promovido.
- RLS/Storage negativos e positivos verdes para identidades distintas.
- Duas cargas Pindobal idênticas sem duplicação.
- Todos os ACs P0 aprovados em staging nas três plataformas.
- Zero vulnerabilidade crítica/alta aberta; exceções têm aceite humano e prazo.
- Restore/rollback ensaiado e runbook utilizável por pessoa diferente da autora.
