> Arquivado em: 12/08/2026  
> Razão: substituído após auditoria do estado real; os checkboxes históricos não possuíam evidência suficiente para sustentar conclusão.  
> Documento sucessor: `docs/finalization/tasks.md`  
> Observação: checkboxes e relatos de execução não constituem, isoladamente, evidência de conclusão.

# ECOnexão — Plano de implementação e tarefas

Referência funcional: `docs/backend_integration_spec.md`  
Fonte de dados inicial: `C:\Users\Bruno\Downloads\teste-rota`

Instrução para IA: antes de executar qualquer item, seguir `AGENTS.md` e `docs/ai_task_playbook.md`, produzir o mini-brief obrigatório e carregar o pacote de referências do marco. Tasks `L` devem ser executadas nas cinco etapas aplicáveis: contrato/schema, happy path, autorização/erros, testes e integração/aceite/documentação.

## Convenções

- Prioridade: `P0` bloqueia o produto; `P1` necessária para entrega; `P2` melhoria posterior.
- Tamanho: `S`, `M`, `L` indica complexidade relativa, não prazo.
- Uma tarefa só pode ser concluída com código, testes, documentação e critérios de aceite atendidos.
- IDs em `DEP` indicam dependências.
- O campo “Aceite” é cumulativo com `docs/acceptance_criteria.md` e a Definition of Done do `AGENTS.md`.
- Arquivos e evidências esperados por tipo de tarefa estão em `docs/ai_task_playbook.md`.

## Marco 0 — Decisões, baseline e contrato

- [x] **ECO-0001 — Congelar baseline funcional** (`P0`, `S`)
  - Registrar commit/base do aplicativo e executar Android/web.
  - Capturar fluxos e estados atuais das seis telas.
  - Aceite: baseline reproduzível e falhas conhecidas registradas.

- [x] **ECO-0002 — Resolver versão do Expo** (`P0`, `S`)
  - Confirmar permanência no SDK 54 ou criar épico separado de upgrade para 57.
  - Não misturar upgrade de SDK com integração do backend.
  - Aceite: versão e documentação normativa registradas.

- [x] **ECO-0003 — Aprovar decisões de produto pendentes** (`P0`, `M`)
  - Confirmar anonymous sign-in do Supabase com posterior vínculo de identidade.
  - Confirmar suporte Android, iOS e web.
  - Definir ação final do selo consciente e formato do detalhe do ator.
  - Definir provedor de hospedagem, banco e storage.
  - Aceite: ADRs curtos adicionados à spec.

- [x] **ECO-0004 — Congelar contrato OpenAPI v1** (`P0`, `M`, DEP: ECO-0003)
  - Detalhar schemas, paginação, erros, idempotência e exemplos.
  - Aceite: arquivo OpenAPI validado e revisado pelo frontend.

## Marco 1 — Fundação do backend

- [x] **ECO-0101 — Criar projeto FastAPI** (`P0`, `M`)
  - Estrutura modular, settings, logging JSON e `/health/live`.
  - Aceite: servidor inicia localmente e documentação `/docs` responde.

- [ ] **ECO-0102 — Provisionar projetos Supabase** (`P0`, `M`)
  - Criar projetos separados para development, test, staging e production; registrar apenas referências não secretas.
  - Ativar PostGIS no schema recomendado e confirmar PostgreSQL 17.
  - Aceite: consulta de smoke test cria/consulta `Point` e `LineString`; nenhuma credencial de produção está disponível no ambiente de IA.

- [x] **ECO-0103 — Configurar SQLAlchemy e migrations Supabase** (`P0`, `L`, DEP: ECO-0102)
  - Configurar pool/conexão do FastAPI, sessão por request e transações.
  - Inicializar `supabase/config.toml` e `supabase/migrations`; descobrir comandos pela versão instalada com `supabase --help`.
  - Proibir Alembic em paralelo e alterações manuais de schema sem migration reconciliada.
  - Aceite: schema vazio recebe todas as migrations em ordem; lista de migrations remota coincide com o repositório.

- [x] **ECO-0104 — Configurar qualidade e testes** (`P0`, `S`)
  - Ruff, mypy, pytest, coverage e comandos padronizados.
  - Aceite: CI local verde com teste mínimo.

- [x] **ECO-0105 — Configurar erros, CORS e request ID** (`P0`, `M`)
  - Envelope de erro, handlers, CORS explícito e propagação de request ID.
  - Aceite: erros 4xx/5xx não vazam detalhes internos.

- [x] **ECO-0106 — Criar `.env.example` e política de segredos** (`P0`, `S`)
  - Supabase URL/publishable key, conexão Postgres, secret/service key apenas server-side, Google, OSRM e observabilidade.
  - Aceite: nenhum segredo real versionado; scanner de segredos no CI.

- [x] **ECO-0107 — Configurar segurança base do Supabase** (`P0`, `L`, DEP: ECO-0102, ECO-0103)
  - Definir schemas expostos/privados, grants explícitos e padrão RLS-on.
  - Não criar objetos customizados em `auth`, `storage` ou `realtime`.
  - Executar Security/Performance Advisors antes de promover migrations.
  - Aceite: tabelas novas não ficam acessíveis por `anon`/`authenticated` sem decisão explícita e teste negativo.

## Marco 2 — Domínio e migrations

- [x] **ECO-0201 — Modelar regiões, rotas, origens e geometrias** (`P0`, `L`, DEP: ECO-0103)
  - Implementar tabelas e índices GiST.
  - Aceite: constraints impedem origem duplicada e geometria inválida.

- [x] **ECO-0202 — Modelar atores, categorias e acessibilidade** (`P0`, `L`, DEP: ECO-0103)
  - Implementar relação rota–ator com métricas espaciais.
  - Aceite: ator pode pertencer a várias rotas sem duplicação.

- [x] **ECO-0203 — Modelar alertas e mídia** (`P1`, `M`, DEP: ECO-0103)
  - Aceite: consulta de alertas ativos respeita janela temporal.

- [x] **ECO-0204 — Modelar proveniência e ingestão** (`P0`, `L`, DEP: ECO-0103)
  - External refs, runs, raw records, reconciliação e field provenance.
  - Aceite: cada ator importado aponta para ao menos uma fonte.

- [x] **ECO-0205 — Modelar usuário, preferências e favoritos** (`P0`, `L`, DEP: ECO-0103)
  - `profiles.id` referencia `auth.users.id`; constraints únicas e exclusão em cascata revisada.
  - Aceite: favoritos são isolados por usuário e idempotentes.

- [x] **ECO-0206 — Modelar viagens, visitas e selos** (`P1`, `M`, DEP: ECO-0205)
  - Aceite: métricas podem ser recalculadas a partir dos eventos persistidos.

- [x] **ECO-0207 — Implementar e testar RLS/policies** (`P0`, `L`, DEP: ECO-0201..0206, ECO-0107)
  - Policies de leitura pública somente onde aprovadas; ownership com `(select auth.uid())` para dados de usuário.
  - UPDATE com `USING` e `WITH CHECK`; views expostas com `security_invoker = true`.
  - Aceite: matriz `anon`, usuário A, usuário B e backend cobre SELECT/INSERT/UPDATE/DELETE e prova ausência de acesso cruzado.

## Marco 3 — Pipeline de dados Pindobal

- [x] **ECO-0301 — Inventariar e hashear fontes** (`P0`, `S`)
  - Manifesto de arquivos, encoding, quantidade, cabeçalhos e checksum.
  - Aceite: importação detecta alteração não aprovada da fonte.

- [x] **ECO-0302 — Criar importador OSRM** (`P0`, `M`, DEP: ECO-0201)
  - Converter três CSVs em LineStrings e calcular bounds/distâncias.
  - Aceite: Porto 45,229 km; Aeroporto 41,452 km; Rodoviária 42,319 km dentro da tolerância definida.

- [x] **ECO-0303 — Criar importador SEMTUR** (`P0`, `L`, DEP: ECO-0202, ECO-0204)
  - Normalizar campos e preservar texto bruto/proveniência.
  - Aceite: relatório soma 674 registros entre importados, rejeitados e candidatos.

- [x] **ECO-0304 — Criar importador do recorte Pindobal** (`P0`, `L`, DEP: ECO-0302, ECO-0303)
  - Importar 303 coordenadas e interpretar corretamente posição/segmento de rota.
  - Aceite: nenhuma coordenada válida é silenciosamente descartada.

- [x] **ECO-0305 — Importar snapshot Google legado** (`P0`, `L`, DEP: ECO-0204)
  - Marcar limitações e não inventar `google_place_id` ausente.
  - Aceite: relatório soma 737 registros e identifica os que não têm ID externo persistível.

- [x] **ECO-0306 — Implementar reconciliação SEMTUR × Google** (`P0`, `L`, DEP: ECO-0303, ECO-0305)
  - Match determinístico e fuzzy com score explicável.
  - Aceite: casos ambíguos entram em fila, sem merge destrutivo.

- [x] **ECO-0307 — Relacionar atores às geometrias com PostGIS** (`P0`, `L`, DEP: ECO-0302, ECO-0306)
  - Distância à rota, posição, flags por origem e índice espacial.
  - Aceite: amostra comparada aos CSVs e tolerância documentada.

- [x] **ECO-0308 — Criar seed publicável de Pindobal** (`P0`, `M`, DEP: ECO-0307)
  - Comando idempotente, dry-run e relatório final.
  - Aceite: duas execuções produzem o mesmo estado e contagens.

## Marco 4 — Conectores externos

- [x] **ECO-0401 — Implementar cliente Google Places (New)** (`P1`, `L`)
  - Field masks mínimos, retry, timeout, paginação, orçamento e métricas.
  - Aceite: testes usam servidor simulado; nenhuma chamada externa no CI.

- [x] **ECO-0402 — Corrigir persistência de Place ID** (`P0`, `M`, DEP: ECO-0401)
  - IDs externos, refresh e detecção de place movido/obsoleto.
  - Aceite: nova ingestão preserva o ID do fornecedor ponta a ponta.

- [x] **ECO-0403 — Criar job incremental de atualização de POIs** (`P1`, `L`, DEP: ECO-0401, ECO-0402)
  - Agendamento, lock, checkpoint, custo máximo e relatório.
  - Aceite: falha parcial pode retomar sem duplicar registros.

- [x] **ECO-0404 — Implementar `OsrmConnector`** (`P1`, `M`)
  - Recalcular apenas por ação editorial/job.
  - Aceite: contrato não expõe detalhes específicos do fornecedor.

- [x] **ECO-0405 — Preparar conector Google Business Profile** (`P2`, `L`)
  - OAuth, elegibilidade, consentimento, contas e locations autorizadas.
  - Aceite: feature flag desligada até aprovação do Google e do estabelecimento.

- [x] **ECO-0406 — Implementar Supabase Storage** (`P1`, `L`)
  - Buckets separados para avatar e mídia editorial; policies, upload seguro, processamento, EXIF, alt text e lifecycle.
  - Testar INSERT/SELECT/UPDATE quando houver upsert.
  - Aceite: avatar e imagem editorial funcionam usando publishable key/JWT ou URL assinada, sem expor secret/service key.

## Marco 5 — API de leitura territorial

- [x] **ECO-0501 — Implementar regiões e bootstrap** (`P0`, `M`, DEP: ECO-0201)
  - `GET /regions` e parte pública do `GET /bootstrap`.
  - Aceite: região ativa inválida recebe fallback explícito.

- [x] **ECO-0502 — Implementar lista de rotas** (`P0`, `L`, DEP: ECO-0308)
  - Busca, filtros, paginação e contagens.
  - Aceite: combinações `q`, `saved` e `verified` testadas.

- [x] **ECO-0503 — Implementar detalhe de rota** (`P0`, `L`, DEP: ECO-0308)
  - Overview, stats, origens e resumos.
  - Aceite: 404 padronizado e sem fallback silencioso para outra rota.

- [x] **ECO-0504 — Implementar geometria e mapa** (`P0`, `L`, DEP: ECO-0308)
  - Payload por origem, bounds, pins e legenda.
  - Aceite: resposta é enxuta e coordenadas são válidas.

- [x] **ECO-0505 — Implementar alertas** (`P1`, `M`, DEP: ECO-0203)
  - Aceite: severidade `info`, `warning`, `critical` preservada.

- [x] **ECO-0506 — Implementar catálogo e detalhe de ator** (`P0`, `L`, DEP: ECO-0308)
  - Busca, categorias, paginação, contatos e acessibilidade.
  - Aceite: ator inexistente retorna 404; dados Google têm atribuição/proveniência apropriada.

## Marco 6 — Sessão, usuário e mutations

- [x] **ECO-0601 — Implementar anonymous sign-in do Supabase** (`P0`, `M`, DEP: ECO-0205, ECO-0207)
  - Criar sessão anônima, perfil correspondente e bootstrap autenticado.
  - Não usar `auth.role()` para distinguir guest; usuário anônimo também usa o papel Postgres `authenticated`.
  - Aceite: ownership por `auth.uid()` funciona; reinstalação, logout e expiração têm comportamento documentado.

- [x] **ECO-0602 — Integrar Supabase Auth e validação no FastAPI** (`P1`, `L`, DEP: ECO-0601)
  - Login/cadastro, vínculo do guest, refresh/logout e armazenamento seguro no Expo.
  - FastAPI valida assinatura assimétrica/JWKS, emissor, audiência, expiração e `sub`; nunca autoriza por `user_metadata`.
  - Aceite: testes de token ausente, inválido, expirado, usuário A/B, refresh concorrente, vínculo e logout.

- [x] **ECO-0603 — Implementar perfil e avatar** (`P1`, `L`, DEP: ECO-0406, ECO-0602)
  - Integrar `profiles` a `auth.users.id` sem alterar o schema gerenciado `auth`.
  - Aceite: validação de arquivo, policy de ownership e rollback de upload falho.

- [x] **ECO-0604 — Implementar preferências** (`P0`, `M`, DEP: ECO-0601)
  - Região, contraste, leitor, escala e locale.
  - Aceite: PATCH parcial e restauração no bootstrap.

- [x] **ECO-0605 — Implementar favoritos idempotentes** (`P0`, `L`, DEP: ECO-0601)
  - Rota e ator; PUT/DELETE repetidos são seguros.
  - Aceite: testes concorrentes e isolamento por usuário.

- [x] **ECO-0606 — Implementar viagens, visitas e impacto** (`P1`, `L`, DEP: ECO-0206, ECO-0602)
  - Aceite: números do perfil derivam do servidor, não de constantes.

- [x] **ECO-0607 — Implementar conteúdo de suporte** (`P1`, `S`)
  - Aceite: links e contatos são validados e atualizáveis sem nova versão do app.

## Marco 7 — Camada de dados do Expo

- [x] **ECO-0701 — Criar client HTTP tipado** (`P0`, `M`, DEP: ECO-0004)
  - Base URL, timeout, headers, request ID, refresh e parsing de erros.
  - Aceite: nenhum componente chama `fetch` diretamente.

- [x] **ECO-0702 — Gerar/sincronizar tipos do OpenAPI** (`P0`, `M`, DEP: ECO-0701)
  - Aceite: CI detecta quebra de contrato.

- [x] **ECO-0703 — Configurar cache de servidor** (`P0`, `M`)
  - Query keys por região/rota/origem/filtro; invalidação documentada.
  - Aceite: troca de região não mistura resultados.

- [x] **ECO-0704 — Refatorar AppContext** (`P0`, `L`, DEP: ECO-0703)
  - Remover listas remotas do reducer e manter sessão/preferências/UI global.
  - Aceite: `mockData.ts` não participa de runtime fora de story/teste.

- [x] **ECO-0705 — Implementar estados padrão** (`P0`, `M`)
  - Skeleton/loading, vazio, erro, retry, offline e mutation error.
  - Aceite: componentes são acessíveis e reutilizados nas seis telas.

- [x] **ECO-0706 — Armazenar tokens com segurança** (`P0`, `M`, DEP: ECO-0601)
  - Adaptar persistência da sessão Supabase ao SecureStore no nativo e estratégia segura no web.
  - Aceite: access/refresh token não aparece em logs nem armazenamento inseguro; restauração e logout funcionam.

## Marco 8 — Integração global, Início e Rotas

- [x] **ECO-0801 — Implementar bootstrap do aplicativo** (`P0`, `L`, DEP: ECO-0501, ECO-0706)
  - Sessão Supabase anônima/autenticada, refresh, fontes, preferências e recuperação de erro.

- [x] **ECO-0802 — Implementar seletor global de região** (`P0`, `M`, DEP: ECO-0604, ECO-0703)
  - Modal acessível compartilhado pelo header e hero.
  - Aceite: escolha persiste e invalida consultas corretas.

- [x] **ECO-0803 — Integrar homepage** (`P0`, `L`, DEP: ECO-0502, ECO-0605)
  - Rotas salvas, favoritos, empty state e CTAs.

- [x] **ECO-0804 — Integrar tela de rotas** (`P0`, `L`, DEP: ECO-0502)
  - Busca com debounce, chips, paginação, cards e limpar filtros.

- [x] **ECO-0805 — Implementar favorito otimista de rota** (`P0`, `M`, DEP: ECO-0605)
  - Rollback, anúncio acessível e prevenção de toque duplicado.

## Marco 9 — Detalhe e mapa da rota

- [x] **ECO-0901 — Integrar detalhe de rota** (`P0`, `L`, DEP: ECO-0503)
  - Hero, overview, `RouteStats`, alertas e preview de atores.

- [x] **ECO-0902 — Integrar simulador de origem** (`P0`, `L`, DEP: ECO-0504)
  - Atualizar distância, duração, geometria e badge.
  - Aceite: Porto/Aeroporto/Rodoviária exibem seus valores reais.

- [x] **ECO-0903 — Implementar MapAdapter real** (`P0`, `L`, DEP: ECO-0003)
  - Adaptador nativo e web conforme plataformas aprovadas.
  - Aceite: linha, bounds e pins da Pindobal são visualmente verificados.

- [x] **ECO-0904 — Ativar zoom e câmera** (`P0`, `M`, DEP: ECO-0903)
  - Limites, acessibilidade e desabilitação nos extremos.

- [x] **ECO-0905 — Integrar pins, filtros e bottom sheet** (`P0`, `L`, DEP: ECO-0504, ECO-0903)
  - Aceite: filtros não escondem o pin selecionado de modo inconsistente.

- [x] **ECO-0906 — Preservar ator/origem na navegação** (`P0`, `M`)
  - `actorId` e `originId` em parâmetros tipados.
  - Aceite: preview → mapa → catálogo mantém contexto e foco.

- [x] **ECO-0907 — Corrigir retry da rota não encontrada/erro** (`P1`, `S`)
  - Retry repete consulta; voltar continua ação independente.

## Marco 10 — Catálogo e detalhe do ator

- [x] **ECO-1001 — Integrar catálogo** (`P0`, `L`, DEP: ECO-0506)
  - Busca, categorias completas, contagem, paginação e limpar filtros.

- [x] **ECO-1002 — Criar tela endereçável de ator** (`P0`, `L`, DEP: ECO-0506)
  - `/actor/[actorId]`, fotos, contatos, horários, acessibilidade e fonte.

- [x] **ECO-1003 — Tornar ActorCard funcional** (`P0`, `M`, DEP: ECO-1002)
  - Card abre detalhe; coração não dispara abertura.

- [x] **ECO-1004 — Implementar favorito otimista de ator** (`P0`, `M`, DEP: ECO-0605)

- [x] **ECO-1005 — Implementar contatos externos** (`P1`, `M`)
  - Telefone, site, Instagram e mapa; confirmação quando necessário.
  - Aceite: esquemas inválidos são bloqueados e erro é compreensível.

## Marco 11 — Perfil, preferências e histórico

- [x] **ECO-1101 — Integrar perfil e impacto** (`P0`, `L`, DEP: ECO-0603, ECO-0606)
  - Dados reais, avatar e selo consciente.

- [x] **ECO-1102 — Criar tela de rotas salvas** (`P1`, `M`)
  - Pode reutilizar `/routes?saved=true`, preservando deep link.

- [x] **ECO-1103 — Criar tela de atores favoritos** (`P0`, `M`)

- [x] **ECO-1104 — Criar histórico de viagens e visitas** (`P0`, `L`, DEP: ECO-0606)

- [x] **ECO-1105 — Criar preferências de acessibilidade** (`P0`, `L`, DEP: ECO-0604)
  - Alto contraste, modo leitor e escala; aplicar sem reinício.

- [x] **ECO-1106 — Integrar configurações regionais** (`P0`, `S`, DEP: ECO-0802)

- [x] **ECO-1107 — Criar suporte e operação editorial** (`P1`, `M`, DEP: ECO-0607)

- [x] **ECO-1108 — Auditar falsos botões do perfil** (`P0`, `S`)
  - Aceite: todos navegam/executam ação ou deixam de ter semântica interativa.

## Marco 12 — Segurança, qualidade e lançamento

- [x] **ECO-1201 — Testes E2E dos fluxos críticos** (`P0`, `L`)
  - Região, busca, detalhe, origem, mapa, ator, favoritos, perfil e preferências.

- [x] **ECO-1202 — Auditoria de acessibilidade** (`P0`, `L`)
  - TalkBack/VoiceOver, teclado web, foco, contraste, escala e anúncios.

- [x] **ECO-1203 — Testes de rede degradada/offline** (`P0`, `M`)
  - Timeout, retry, cache, mutation falha e retomada.

- [x] **ECO-1204 — Revisão de segurança e LGPD** (`P0`, `L`)
  - Threat model, JWT Supabase, RLS, Storage policies, autorização por objeto, retenção, exclusão e logs.
  - Testar que `service_role`/secret key não aparece no bundle Expo.

- [x] **ECO-1205 — Revisão das políticas Google e atribuições** (`P0`, `M`)
  - Places, fotos, avaliações, armazenamento, Place IDs e GBP.

- [x] **ECO-1206 — Observabilidade e orçamento** (`P0`, `M`)
  - Erros, métricas, traces, alertas e limite de custo dos conectores.

- [x] **ECO-1207 — Pipeline CI/CD e ambientes** (`P0`, `L`)
  - Backend, migrations Supabase promovidas development → staging → production, advisors, Expo build e rollback.

- [x] **ECO-1208 — Carga e desempenho** (`P1`, `M`)
  - Listas paginadas, consulta espacial, payload do mapa e imagens.

- [x] **ECO-1209 — Homologação da matriz de telas** (`P0`, `L`)
  - Revisar cada linha da seção 11 da spec.
  - Aceite: evidência em Android, iOS e web conforme escopo aprovado; nenhuma interação incompleta.

- [x] **ECO-1210 — Remover mocks de produção e publicar** (`P0`, `M`, DEP: ECO-1201..1209)
  - Aceite: build de produção não contém fallback silencioso para dados fictícios.

## Ordem de entrega recomendada

1. Marcos 0–3: fundação e Pindobal reproduzível.
2. Marcos 5 e 7: API de leitura e client Expo.
3. Marco 8: primeira fatia vertical publicável — regiões, homepage e rotas.
4. Marco 9: detalhe, origens e mapa real.
5. Marcos 6 e 10: identidade, favoritos e atores.
6. Marco 11: perfil e todos os itens hoje inertes.
7. Marco 4 em paralelo controlado: atualização externa após os imports estarem estáveis.
8. Marco 12: endurecimento, homologação e lançamento.

## Definition of Done global

Uma task funcional só está pronta quando:

- Contrato e tipos estão sincronizados.
- Migration/seed é reproduzível quando aplicável.
- Loading, vazio, erro e retry foram implementados.
- Acessibilidade foi verificada.
- Testes positivos, negativos e de autorização passaram.
- Logs e métricas não expõem dados sensíveis.
- Documentação foi atualizada.
- Não existe fallback silencioso para mock.
- A ação funciona por toque, teclado e leitor de tela nas plataformas suportadas.
