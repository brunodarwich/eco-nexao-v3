# Decisões humanas e ADRs pendentes

Nenhum agente deve preencher silenciosamente esta tabela. `Owner` significa pessoa
com autoridade sobre produto, orçamento, contas ou risco jurídico. Uma decisão só
desbloqueia implementação quando registrada em ADR/status aceito ou documento
equivalente indicado.

| ID | Decisão | Opções mínimas a comparar | Critério de decisão | Evidência/saída / Status Registrado | Bloqueia |
|---|---|---|---|---|---|
| ECO-1302 | Provedor de contêiner FastAPI | Render, Fly.io, Railway, Cloud Run | região, custo, egress, health, rollback, SLA | ADR 0005 aceito: Google Cloud Run (`southamerica-east1`). Deploy ADIADO para Marco 20. Sem billing/serviço agora. | ECO-2001–2004 |
| ECO-1303 | Política editorial e RBAC | papéis admin/editor/reviewer/publisher, painel próprio | segregação de funções, UX, custo, auditabilidade | ADR 0006 aceito: RBAC, state machine, Publish Guard e audit trail. Owner é responsável provisório durante dev. | ECO-1403, ECO-1601–1804 |
| ECO-1304 | Identidade e sessão | guest+email, magic link, OAuth; web em memória, storage local aceito ou BFF cookie | continuidade de histórico, segurança, custo, plataformas | ADR 0007 aceito: localStorage Web, Opção 1 conflito, expurgo 90d aprovado. | ECO-1902 |
| ECO-1305 | Política de mídia | bucket público/privado, derivados, CDN, retenção, exclusão, licença/crédito/alt | LGPD, direitos, performance e custo | ADR 0008 aceito: buckets híbridos, EXIF strip, WebP, Google proxy, alt text. | ECO-1402, ECO-1701–1704 |
| ECO-1306 | Pacote de lançamento | domínios, nome/identidade final, contatos, termos, privacidade, consentimento, budget Google, contas lojas, owner de production | validade legal, marca, orçamento e operação | **PARTIAL**: Decisões parciais registradas com o Owner em 12/08/2026. Pendente de homologação jurídica, contas e marca definitiva. | ECO-1401 (escopo reduzido liberável), ECO-1905, ECO-2201–2204 |

## Registro de Decisões de Lançamento (ECO-1306) — Estado Confirmado pelo Owner

| Item | Decisão Registrada | Status | Bloqueador de Desenvol. Local? | Bloqueador de Staging / Release? |
|---|---|---|---|---|
| **Supabase Dev & Test** | Reutilização dos projetos `econexao` (dev) e `econexao-teste` (test) no Plano Free. Proibida colisão. `econexao-teste` é descartável sob autorização. | **APROVADO** | Não | Não |
| **Supabase Staging** | Provisionamento de projeto Supabase Staging isolado. | **ADIADO** | Não | Sim (Bloqueia Staging) |
| **Supabase Production** | Provisionamento de projeto Supabase Produção isolado. | **ADIADO / BLOQUEADO** | Não | Sim (Bloqueia Gate 7 / Release) |
| **Cloud Run Backend** | Adiado deploy/billing. FastAPI será mantido e testado localmente. Primeiro deploy no Marco 20. | **APROVADO (Arquitetura) / ADIADO (Deploy)** | Não | Sim (Bloqueia Staging/Prod) |
| **Domínios & Links** | Sem compra/registro de domínios agora. Desenvol. local; staging em URL provisória. | **PENDENTE / ADIADO** | Não | Sim (Bloqueia ECO-1905 / Release) |
| **Novos Gastos** | Nenhum custo ou contratação financeira autorizada nesta etapa. | **NÃO AUTORIZADOS** | Não | Não |
| **Nome Público App** | Nome provisoriamente aprovado: `ECOnexão`. Expo slug: `econexao-app`. | **PROVISÓRIO** | Não | Sim (Bloqueia Release) |
| **Package / Bundle IDs** | Android Package e iOS Bundle ID provisórios (não aplicar em app.json/eas.json ainda). | **PROVISÓRIO** | Não | Sim (Bloqueia Release/Lojas) |
| **Responsável RBAC** | Proprietário do projeto assume provisoriamente papéis admin, editor, reviewer e publisher. | **PROVISÓRIO** | Não | Sim (Bloqueia Homologação Editorial) |
| **Contas de Lojas** | Expo/EAS, Apple Developer e Google Play Console com status a confirmar/cadastrar. | **A CADASTRAR** | Não | Sim (Bloqueia Release/Builds) |
| **LGPD & Expurgo 90d** | Regra de 90 dias de expurgo de guest aprovada (ADR 0007); execução futura exige dry-run. | **APROVADO (Regra)** | Não | Não |
| **Canal Titular & Termos** | Canal DPO, Termos de Uso e Política de Privacidade pendentes de redação e aprovação. | **PENDENTE** | Não | Sim (Bloqueia Staging Público / Release) |
| **Suporte & Ops** | Proprietário do projeto é o responsável operacional provisório. Canal de suporte pendente. | **PROVISÓRIO / PENDENTE** | Não | Sim (Bloqueia Staging/Prod) |

## Checklist obrigatório do owner

- [x] Confirmar se `econexao` e `econexao-teste` são development/test (Aprovado reuso dos dois projetos existentes).
- [ ] Criar/autorizar projetos Supabase separados para staging e production (Adiado para Marco 20 e Release).
- [x] Nomear quem pode ser admin, editor, reviewer e publisher (Proprietário do projeto nomeado provisoriamente).
- [x] Escolher provedor/região do FastAPI e aprovar orçamento mensal/limites (ADR 0005 Cloud Run aceito; deploy adiado; zero gasto agora).
- [ ] Definir domínios da API, web e links universais (Adiado para antes da ECO-1905).
- [ ] Confirmar contas Apple Developer, Google Play Console e Expo/EAS, inclusive proprietário legal e método de pagamento (A cadastrar/confirmar antes dos builds de homologação).
- [x] Aprovar nome provisório do app (`ECOnexão`), mantendo slug `econexao-app` e deixando pacotes nativos para definição institucional.
- [x] Aprovar política editorial (ADR 0006) e Publish Guard.
- [ ] Aprovar política de privacidade, termos e canal do titular (Pendentes de redação e aprovação legal final).
- [x] Aprovar licenças/créditos/alt text das imagens e tratamento de fotos Google (ADR 0008 aceito; proxy 30d sem download).
- [x] Aprovar budget e quotas Google (Zero gasto autorizado no momento; dev/testes locais).
- [ ] Fornecer secrets por secret manager, nunca por prompt/commit/log.
- [ ] Aprovar staging e, separadamente, cada ação de production.
- [x] Escolher RPO/RTO e expurgo 90d de guests (ADR 0007 aceito com salvaguarda de dry-run).

## Conteúdo mínimo dos ADRs

Cada ADR deve conter contexto, alternativas reais, critérios ponderados, decisão,
consequências, custos, riscos, rollback/reversibilidade, data, owner e status.

## Regras de parada

- Sem ECO-1302 aceita: não criar Docker/deploy específico de provedor.
- Sem ECO-1303 aceita: não criar roles, políticas editoriais, `/admin` ou painel.
- Sem ECO-1304 aceita: não implementar persistência web, OAuth ou linking completo.
- Sem ECO-1305 aceita: não publicar buckets, aceitar licenças por padrão ou definir exclusão/derivados.
- Sem ECO-1306 aprovada: não criar staging pago, configurar domínios/lojas, usar chaves Google reais ou acessar production.
