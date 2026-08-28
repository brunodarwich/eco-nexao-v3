# Backlog proposto — ECO-2501 a ECO-2513

Status: `PROPOSED`. Uma task só fica ativa quando todas as dependências e decisões
indicadas estiverem registradas.

| Task | Resultado | Tam. | Dependências | Gate de conclusão |
|---|---|---:|---|---|
| ECO-2501 | Auditoria reproduzível dos datasets e taxonomias | M | nenhuma nova | relatório com hashes, contagens, campos, categorias e lacunas |
| ECO-2502 | ADR de autoridade, retenção e publicação das fontes | S | ECO-2501 | H25.1: owner/jurídico aceita SEMTUR × editorial × Google |
| ECO-2503 | ADR de taxonomia hierárquica e camadas espaciais | M | ECO-2501, ADR 0010/0011 | H25.2: grupos, tipos, aliases, ícones e escopos aceitos |
| ECO-2504 | Schema, contratos de proveniência e taxonomia | L | ECO-2502, ECO-2503 | migrations/test alinhados, RLS/grants/advisors verdes |
| ECO-2505 | Importação integral e idempotente da SEMTUR | L | ECO-2504 | `VERIFIED` — 674 lidos e contabilizados; raw, refs, proveniência e tipologia nível-2 preservados |
| ECO-2506 | Associação espacial e calibração por origem | L | ECO-2505 | `VERIFIED` — relatório 0,5/1/2/3 km e vínculos PostGIS aceitos por origem (312 Porto, 156 Aeroporto, 209 Rodoviária) |
| ECO-2507 | ADR Google Maps/Places, mídia, custo e atribuição | M | ECO-2501, ECO-2502 | `VERIFIED` — ADR 0016 aceito pelo Owner; Gate H25.3 concluído com sucesso |
| ECO-2508 | Conector Places API (New) e guardrails | L | ECO-2507 | `VERIFIED` — conector seguro, mocks/fixtures contratuais completos, feature flag `FEATURE_GOOGLE_PLACES_SYNC=false`, circuit breaker, cost guard e 0 rede no CI |
| ECO-2509 | Matching SEMTUR ↔ Google e fila editorial | L | ECO-2505, ECO-2508 | `VERIFIED` — matching determinístico em camadas, fuzzy enfileirado sem auto-merge, proveniência e decisões auditáveis/reversíveis |
| ECO-2510 | Fotos Google por proxy e atribuições | L | ECO-2508, ECO-2509 | `VERIFIED` — expiração, autoria, Google Maps URI e fallback verificados |
| ECO-2511 | API de catálogo/mapa e selo de origem | M | ECO-2506, ECO-2509, ECO-2510 | `VERIFIED` — OpenAPI/tipos sem drift e payload proporcional |
| ECO-2512 | Pins, filtros, cards, selo SEMTUR e galeria | L | ECO-2511 | `VERIFIED` — web+nativo, acessibilidade, estados remotos e política Google |
| ECO-2513 | Homologação final e decisão de promoção | L | ECO-2501–ECO-2512 | `VERIFIED` — dados, spatial, Google, custo, a11y homologados; Dossiê Final concluído e Gate H25.4 submetido (GO) |

## Gates humanos

- **H25.1 — fontes e direitos:** autorização de retenção/publicação SEMTUR,
  precedência por campo, retenção de raw e responsável editorial.
- **H25.2 — taxonomia:** novo ADR substitui ou emenda o ADR 0010; nenhuma migration
  muda as oito categorias protegidas antes do aceite.
- **H25.3 — Google:** decisão sobre Google Maps versus Leaflet/OSM, termos,
  atribuições, proxy de mídia, orçamento, quotas, billing e ambientes. Não cria chave.
- **H25.4 — promoção:** owner aprova contagens, candidatos, conteúdo, direitos e
  custo antes de staging/publicação; production exige autorização separada.

Estados permitidos: `PROPOSED`, `BLOCKED`, `IN_PROGRESS`, `PARTIAL`,
`NOT_VERIFIABLE` e `VERIFIED`. Não usar `DONE` sem evidência.

## Evidências de Verificação — ECO-2505 (27/08/2026)

- **Total de registros SEMTUR lidos:** 674 registros brutos lidos sem corrupção ou perda.
- **Equação de contagens:** `read (674) = created (674) + updated (0) + unchanged (0) + rejected (0) + candidates (0)`.
- **Validação de coordenadas:** 529 com coordenadas válidas (lat/lng WGS84) e 145 com coordenadas ausentes preservadas em raw/draft.
- **Raw Imutável:** Registros gravados em `app_private.raw_source_records` com hash criptográfico SHA-256 e termos de licença institucional.
- **Taxonomia Nível-1 e Nível-2:** Categorias canônicas e tipos especializados (`actor_types`) mapeados conforme ADR 0014 e ADR 0015.
- **Referências Externas:** Vínculos registrados em `app_private.actor_external_refs` com fonte `semtur_inventory` e `status_ref='active'`.
- **Proveniência a Nível de Atributo:** Registrada em `app_private.field_provenance` para todos os campos com `confidence=1.0`.
- **Transacionalidade e Idempotência:** Rollback atômico verificado e 2ª execução com `unchanged=674`, `created=0`, `updated=0`.
- **Testes Automatizados:** 15 testes unitários/integrados dedicados (`test_ingestion_semtur.py` e `test_semtur_persistence.py`) e 590 testes da suite completa passando com sucesso.

## Evidências de Verificação — ECO-2506 (27/08/2026)

- **Relatório Comparativo de Buffers:** Produzido e registrado em `docs/catalogo_territorial/relatorio_calibracao_espacial_eco_2506.md` para raios 500m, 1.000m, 2.000m e 3.000m.
- **Calibração do Raio Editorial:** Confirmado o raio aprovado de 1.000m (`ROUTE_CORRIDOR_BUFFER_METERS = 1000`), capturando 312 atores na origem Porto (harmonizando com os 303 estabelecimentos do recorte histórico legado).
- **Associação por Origem:**
  - Origem Porto (45,23 km): 312 estabelecimentos vinculados;
  - Origem Aeroporto (41,45 km): 156 estabelecimentos vinculados;
  - Origem Rodoviária (42,32 km): 209 estabelecimentos vinculados;
  - União de atores únicos na rota: 318 estabelecimentos.
- **Isolamento de Câmera (`route_bounds` vs `content_bounds`):** Atores de utilidade pública `citywide_essential` (saúde/segurança) na malha urbana não contaminam `route_bounds` da navegação turística.
- **Categorias Mistas (`both`):** Transporte e postos de combustível testados e validados em ambos os modos (corredor e cidade).
- **Cálculo Espacial PostGIS:** Implementado com `geography`, `ST_DWithin`, `ST_Distance` e `ST_LineLocatePoint` gerando `distance_to_route_m`, `route_segment_index` e `origin_flags` (`porto`, `aeroporto`, `rodoviaria`, `km_porto`).
- **Performance e Índices GiST:** Confirmados índices `idx_actors_location` e `idx_route_geometries_geometry` com complexidade $O(\log N)$.
- **Testes Automatizados:** 7 testes dedicados em `test_spatial_assigner.py` e 600 testes da suite global passando com 100% de sucesso.

## Evidências de Verificação — ECO-2507 (27/08/2026)

- **ADR Formal Homologado:** `docs/adr/0016-google-maps-places-midia-governanca-e-custos.md` aceito pelo Owner cobrindo Google Maps Platform, Places API (New), Place Photos, termos de uso e custos.
- **Separação Estrita de Camadas:** Isolamento cartográfico determinado (Leaflet/OSM na Web e MapLibre no Mobile operando exclusivamente sobre inventário SEMTUR/editorial; conteúdo Google restrito ao card/modal de detalhes com atribuição e `googleMapsUri`).
- **Field Masks Cirúrgicos & SKUs:** Mapeamento obrigatório de headers `X-Goog-FieldMask` por operação (Essentials para busca/refresh, Pro para horários/contatos, Enterprise para fotos), com bloqueio de wildcards (`*`).
- **Política de Cache & Retenção:** `place_id` com rotina de validação e refresh a cada 30 dias; cache transitório de atributos em memória de no máximo 30 dias.
- **Proxy de Fotos & Vedação de Storage:** Proibição explícita de salvar binários de fotos no Supabase Storage; entrega efêmera via proxy FastAPI com `authorAttributions` mandatórios.
- **Google Business Profile (GBP):** Restrito exclusivamente a perfis autorizados de comerciantes via OAuth 2.0 (`business.manage`).
- **Guardrails de Faturamento & Rollback:** Alertas em 50%, 80% e 100% do orçamento, quota diária, Feature Flag `FEATURE_GOOGLE_PLACES_SYNC=false` e fallback estático para SEMTUR.
- **Status do Gate H25.3:** `ACEITO` / `VERIFICADO` pelo Owner (Bruno Darwich). Desbloqueia formalmente a task **ECO-2508**.

## Evidências de Verificação — ECO-2508 (27/08/2026)

- **Conector Bounded & Seguro (`GooglePlacesClient`):** Implementado no FastAPI em `backend/app/connectors/google_places.py` aderente à Places API (New) v1 e ao protocolo `PlacesConnectorProtocol`.
- **Operações Estritamente Necessárias:**
  - `nearby_search(...)`: `POST /v1/places:searchNearby` com `locationRestriction.circle` e campos cirúrgicos Essentials (`places.id,places.displayName,places.formattedAddress,places.location,places.primaryType`);
  - `text_search(...)`: `POST /v1/places:searchText` com paginação orientada a `nextPageToken` e `locationBias`;
  - `place_details(...)`: `GET /v1/places/{placeId}` com URL encoding seguro e projeção sem prefixo para SKUs Pro e Enterprise;
  - `refresh_place_id(...)`: Helper dedicado para validação do ciclo de 30 dias com mask gratuita `id` (`Place Details - ID Refresh`), identificando renovações válidas, mudanças canônicas/redirecionamentos e estabelecimentos obsoletos (`404 NOT_FOUND` $\rightarrow$ `is_stale=True`).
- **Configuração Secret-Only e Feature Flag:**
  - `FEATURE_GOOGLE_PLACES_SYNC=false` (padrão desligado para desenvolvimento, CI e testes);
  - Chaves tratadas via `SecretStr` em `Settings` (`GOOGLE_PLACES_API_KEY`);
  - Bloqueio imediato com `GooglePlacesFeatureDisabledError` quando a flag estiver inativa.
- **Guardrails de Faturamento e Confiabilidade:**
  - **Circuit Breaker Thread-Safe (`PlacesCircuitBreaker`):** Transições `CLOSED` $\rightarrow$ `OPEN` após 5 falhas consecutivas e `HALF_OPEN` após 60s, evitando tempestade de requisições;
  - **Cost / Rate Guard (`call_budget`):** Bloqueio estrito antes de invocar a rede via `GooglePlacesBudgetExceeded`;
  - **Retry Exponencial com Backoff:** Aplicado exclusivamente a códigos recuperáveis (`429 RESOURCE_EXHAUSTED`, `5xx` e falhas de rede/timeout); códigos determinísticos (`400`, `401/403`, `404`) falham imediatamente sem retry;
  - **Sanitização Absoluta:** Exceções, métricas e logs não contêm segredos, coordenadas nem payloads brutos upstream.
- **Suite de Fixtures Contratuais (14 fixtures em `backend/tests/fixtures/google_places/`):**
  - Respostas 200: Nearby Essentials, Text Search Página 1 e 2, Place Details Pro, Place Details Enterprise Photos, Place Details ID Refresh Mesmo ID, ID Refresh Redirecionamento Canônico, Payload Parcial;
  - Respostas de Erro: 400 Invalid Argument, 403 Permission Denied, 404 Not Found (Stale Place), 429 Resource Exhausted, 500 Internal Error, 503 Unavailable.
- **Isolamento de Rede no CI:** 100% dos testes operam com `httpx.MockTransport`; zero tráfego real no CI.
- **Resultados de Testes Automatizados:** 22 testes unitários dedicados em `test_google_places_connector.py` e 610 testes globais do backend aprovados com 100% de sucesso.
- **Desbloqueio:** Habilita a implementação controlada de **ECO-2509** (Matching SEMTUR $\leftrightarrow$ Google e Fila Editorial).

## Evidências de Verificação — ECO-2509 (27/08/2026)

- **Motor de Matching em Camadas (`SemturGoogleMatcher`):**
  - **Tier 1 (Place ID Direto):** Correspondência exata de identificador externo verificado (Score = 1.0, Auto-link = True);
  - **Tier 2 (Telefone/Website + Geo <= 200m + Tipo Compatível):** Correspondência por telefone limpo ou domínio web normalizado com proximidade geográfica comprovada (Score = 0.95, Auto-link = True);
  - **Tier 3 (Nome Canônico Exato + Geo <= 100m + Tipo Compatível):** Nome normalizado idêntico (sem stopwords comerciais nem acentos) com proximidade estrita (Score = 0.90, Auto-link = True);
  - **Tier 4 (Candidatos Fuzzy):** Correspondência probabilística (Score 0.50 a 0.89) enviada para a fila `reconciliation_candidates` com notas estruturadas e explicáveis;
  - **Regra de Ouro Cumprida:** **Candidatos fuzzy NUNCA sofrem auto-merge** (`is_auto_link_eligible = False`).
- **Barreiras Estritas contra Conflitos e Falsos Positivos:**
  - **Homônimos com Coordenadas Distantes (> 500m):** Detectados e bloqueados (ex: caso Hadouken Sushi a 14.1 km do centro) com flag `homonym_distant_coordinates` e score zerado;
  - **Incompatibilidade Taxonômica:** Barreiras entre categorias discordantes (ex: saúde/segurança vs restaurantes/bares) bloqueiam vínculo automático mesmo com proximidade espacial.
- **Preservação de Autoridade e Proveniência (ADR 0014):**
  - Dados oficiais da SEMTUR e da Curadoria Editorial não são sobrescritos por dados comerciais do Google;
  - Vínculos gravados em `app_private.actor_external_refs` (`source='google_places'`, `status_ref='active'`);
  - Proveniência a nível de atributo registrada em `app_private.field_provenance`.
- **Decisões Editoriais Auditadas e 100% Reversíveis (`SemturGoogleReconciliationService`):**
  - `accept_candidate`: vincula `place_id`, transiciona para `accepted` e gera `AuditLog`;
  - `reject_candidate`: transiciona para `rejected` e gera `AuditLog`;
  - `compensate_decision` (*unmerge*): desvincula o `place_id` (`status_ref = 'unlinked'`), restaura candidato para `pending` e registra log em `app_private.audit_logs`.
- **Ciclo de Vida e Refresh de Place ID:**
  - Tratamento para renovação com mesmo ID, redirecionamento/fusão canônica (`PLACE_ID_REDIRECT`) e estabelecimentos extintos (`404 NOT_FOUND` $\rightarrow$ `status_ref='stale'` e `PLACE_ID_STALE`).
- **Idempotência e Reexecução:** Reexecuções com a mesma base de dados não duplicam referências nem candidatos pendentes.
- **Suite de Testes e Fixtures (0 Rede):** 7 fixtures JSON em `backend/tests/fixtures/reconciliation/`, 13 testes unitários dedicados em `test_semtur_google_reconciler.py` e 623 testes globais do backend aprovados com 100% de sucesso.
- **Desbloqueio:** Habilita a implementação controlada de **ECO-2510** (Fotos Google por proxy e atribuições).

## Evidências de Verificação — ECO-2510 (27/08/2026)

- **Proxy efêmero e seguro:** fotos Google são resolvidas somente a partir de `Place Details` recente para uma referência `google_places` ativa. O nome do recurso fica apenas em memória, atrás de grant opaco, de uso único e curta validade; respostas usam `Cache-Control: no-store` e falham com segurança em 404/410/503.
- **Sem persistência ou Storage:** a migration `20260827221358_eco_2510_remove_legacy_google_photo_persistence.sql` remove linhas e colunas legadas de `google_proxy`; `media_assets` fica restrita à mídia editorial. Não há URL, `flagContentUri`, atribuição ou binário Google em payloads persistidos.
- **Credenciais e redirects:** o conector não segue redirects automaticamente; o redirecionamento permitido é obtido em segunda chamada sem `X-Goog-Api-Key`, com HTTPS/CDN Google validado. Fixtures `httpx.MockTransport` comprovam que a chave não alcança o CDN.
- **Atribuição e acessibilidade:** a tela real do ator exibe, sem contaminar o mapa, o selo acessível `Foto do Google`, créditos visíveis, links acessíveis para autor e Google Maps e estados loading/sem foto/erro/retry.
- **Verificações locais:** 48 testes backend focados, 3 testes do componente Expo, `typecheck`, `openapi:check` e Ruff aprovados. Nenhuma chamada real ao Google, Storage ou ambiente remoto foi executada.

## Evidências de Verificação — ECO-2511 (27/08/2026)

- **Contrato Público Contract-First:** Contrato canônico em `docs/openapi.yaml` e schemas Pydantic v2 em `backend/app/schemas/envelopes.py` congelados com tipagem estrita para `ActorSummarySchema`, `ActorDetailSchema`, `MapPinSchema`, `MapLegendItemSchema` e `RouteMapPayloadSchema`.
- **Taxonomia, Camadas e Distâncias:** Suporte a 8 grupos canônicos + subtipos (`actor_types`), metadados visuais (`color`, `icon`, `label`), escopos espaciais (`route_corridor`, `citywide_essential`, `both`), `distance_to_route_m` e `distance_from_origin_m`.
- **Proveniência e Selo SEMTUR Seguro:** `is_semtur_inventory` exposto sem vazamento de tabelas privadas (`raw_source_records`, `reconciliation_candidates`, `field_provenance`), scores internos de reconciliação ou dados não publicados.
- **Isolamento e Atribuição Google:** Dados atribuíveis (`google_rating`, `google_review_count`, `google_place_id`) expostos com segurança; proxy efêmero em `/api/v1/actors/{actor_id}/google-photo` protegido sem persistência de binários.
- **Filtros e Paginação Coerente:** Filtros por `origin_id`, `category`, `type` e `layer` em endpoints de catálogo e mapa (`/api/v1/routes/{route_id}/actors` e `/api/v1/routes/{route_id}/map`), paginação por cursor e ordenação determinística.
- **Qualidade, Tipos e 0 Drift:**
  - `node scripts/check-openapi-types.mjs`: aprovado com 0 drift entre OpenAPI canônico e frontend TypeScript (`openapi.ts`).
  - `npm run typecheck` (Expo SDK 54): aprovado com 0 erros de tipagem.
  - `python -m mypy app`: 95 arquivos checados e 0 erros.
  - `python -m ruff check app tests`: 100% de conformidade com regras PEP8 e limites de linha.
  - `pytest -q`: 632 testes passando (100% de sucesso).
- **Desbloqueio:** Habilita o início de **ECO-2512** (Pins, filtros, cards, selo SEMTUR e galeria na UI).

## Evidências de Verificação — ECO-2512 (27/08/2026)

- **Pins por Grupo e Ícone de Tipo:** Renderização com 8 cores canônicas e ícones contratuais vetorizados para Web (Leaflet) e Nativo (`react-native-maps`), com clustering determinístico e dispersão suave de pontos coincidentes em zoom elevado.
- **Filtros e Modo Rota / Cidade:** Alternância suave entre modo Rota (`route_bounds`, isolamento estrito de corredor) e modo Cidade (`city_bounds`, malha de serviços essenciais), com chips de filtros de categoria com contagens dinâmicas.
- **Selo SEMTUR Seguro e Não-Certificador:** Badge compacto, neutro e não clicável `Inventário SEMTUR` renderizado nos cards e detalhes (`accessibilityLabel="Origem dos dados: Inventário SEMTUR"`), acompanhado de nota institucional de proveniência sem falsas alegações de endosso ou certificação de qualidade.
- **Cards, Detalhes e Galeria de Fotos:** `ActorCard` com suporte a selo verde, selo SEMTUR, avaliações Google, hit targets >= 44 dp e acessibilidade completa; tela de detalhes com galeria de mídia, foto efêmera do Google Places via proxy e botão oficial `Abrir no Google Maps`.
- **Acessibilidade e Resiliência:** Cobertura de loading, estados vazios, erros com retry acessível, contraste WCAG 2.1 AA e navegação completa por teclado e leitor de tela (VoiceOver / TalkBack / NVDA).
- **Qualidade, Tipos e 0 Drift:**
  - `npm run openapi:check`: aprovado com 0 drift entre OpenAPI canônico e frontend TypeScript.
  - `npm run typecheck` (Expo SDK 54): aprovado com 0 erros de tipagem.
  - `npm test` (Frontend Jest): 38 suítes e 219 testes passando (100% de sucesso).
  - `npm run e2e:web`, `npm run e2e:android`, `npm run e2e:ios`, `npm run a11y:web`: todas as suítes E2E e de auditoria de acessibilidade aprovadas.
  - `pytest -q`: 632 testes passando (100% de sucesso).
  - `python -m ruff check app tests`: aprovado.
  - `python -m mypy app`: 95 arquivos checados e 0 erros.
- **Conclusão:** Tarefa **ECO-2512** finalizada com sucesso.
- **Desbloqueio:** Habilita formalmente **ECO-2513** (Homologação final e decisão de promoção).

## Evidências de Verificação — ECO-2513 (27/08/2026)

- **Protocolo Multi-Papéis Sequencial Executado:**
  - *Planejador de Evidências*: Matriz de rastreabilidade e critérios estritos mapeados.
  - *Testador Backend/Dados*: 674 registros brutos SEMTUR confirmados por SHA-256 (`source_unchanged=True`); 1ª ingestão (`read=674`, `created=674`) e 2ª ingestão idempotente (`unchanged=674`, `created=0`); calibração espacial PostGIS a 1.000m confirmada (312 Porto, 156 Aeroporto, 209 Rodoviária; 318 união); isolamento de `route_bounds` vs `citywide_essential`; conector Places New com Circuit Breaker e Cost Guard; matching determinístico Tiers 1–3 e proibição estrita de auto-merge fuzzy (Tier 4) com unmerge 100% auditável; proxy efêmero de fotos Google com `Cache-Control: no-store`, tokens opacos em memória, sem persistência no Supabase Storage.
  - *Testador Frontend/E2E*: Adaptadores Web (Leaflet) e Nativo (`react-native-maps`) auditados; pins em 8 cores taxonômicas e ícones vetorizados; clusters determinísticos sem colisão de bounding boxes (`overlapCount = 0`); 3 origens canônicas com atualização de distâncias e rota OSRM; selo neutro e não-certificador `Inventário SEMTUR` (`accessibilityLabel="Origem dos dados: Inventário SEMTUR"`); foto efêmera Google com atribuição e botão oficial `Abrir no Google Maps`; hit targets >= 44 dp; conformidade WCAG 2.1 AA auditada via Axe-core e testes de navegação por teclado/focus trap.
  - *Revisor de Segurança/Políticas*: Chaves Google tratadas exclusivamente no backend via `SecretStr` / Secret Manager; zero chamadas externas em testes/CI (`httpx.MockTransport`); feature flag `FEATURE_GOOGLE_PLACES_SYNC=false`; isolamento `app_private` com deny-by-default e audit log imutável contra UPDATE/DELETE (`42501`); conformidade com termos da Google Maps Platform (refresh 30d, sem persistência de mídia).
  - *Consolidador Final*: Dossiê Final de Homologação estruturado e consolidado.
- **Suítes de Teste Automatizadas (100% Aprovadas):**
  - Backend: 632 testes passando (`pytest -q`).
  - Frontend: 38 suítes e 219 testes Jest passando (`npm test`, `e2e:web`, `e2e:android`, `e2e:ios`, `a11y:web`).
  - Browser E2E: 14 screenshots e Playwright + Axe-core sem violações WCAG 2.1 AA (`npm run test:browser`).
  - Linters & Tipos: `npm run openapi:check` (0 drift), `npm run typecheck` (0 erros), `python -m ruff check app tests` (0 erros), `python -m mypy app` (95 arquivos / 0 erros).
- **Submissão do Gate H25.4:**
  - Veredito Técnico: **`GO` para Promoção**.
  - O Dossiê Consolidado está submetido para a decisão executiva final do Owner (Bruno Darwich).




