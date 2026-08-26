# ECOnexão — Especificação de backend e integração das telas

Versão: 1.1
Data: 22/08/2026
Status: proposta para implementação

## 1. Objetivo

Transformar o protótipo Expo da ECOnexão em uma aplicação integrada, com backend Python, Supabase gerenciado, banco geoespacial, autenticação, persistência por usuário e conectores externos. Ao final, todo elemento apresentado ao leitor de tela como botão, campo, filtro ou link deverá executar a ação definida nesta especificação; elementos puramente informativos não deverão anunciar uma ação inexistente.

O primeiro conjunto de dados de produção será a Rota Pindobal, importado e normalizado a partir de `C:\Users\Bruno\Downloads\teste-rota`.

## 2. Critério de sucesso do produto

O incremento estará concluído quando:

1. As seis telas atuais carregarem dados da API, sem dependência funcional de `mockData.ts`.
2. Favoritos, perfil, preferências e histórico forem persistidos por usuário.
3. A região ativa puder ser realmente selecionada e restaurada entre sessões.
4. A Rota Pindobal exibir suas três origens, geometrias, distâncias e atores reais.
5. O mapa tiver zoom funcional, filtros, pins e navegação preservando o ator selecionado.
6. Cards de atores abrirem detalhes e contatos reais.
7. Todos os fluxos tiverem estados de carregamento, vazio, erro, repetição e indisponibilidade offline.
8. O contrato OpenAPI, migrations, testes e observabilidade fizerem parte da entrega.
9. Nenhum segredo de Google, banco ou storage estiver embutido no aplicativo.
10. A matriz de cobertura da seção 11 estiver integralmente aprovada.

## 3. Estado atual e dados disponíveis

### 3.1 Aplicativo

- Expo SDK 54, React Native 0.81 e Expo Router 6.
- Dados carregados de `src/data/mockData.ts`.
- `AppContext` acumula dados de servidor e estado de interface.
- Favoritos e preferências existem somente em memória.
- O mapa é uma imagem raster com pins posicionados por porcentagem.
- Alguns controles têm aparência ou semântica de botão, mas não possuem ação.

Conforme o ADR 0001, o aplicativo permanece no Expo SDK 54 durante a integração. A documentação normativa é a versão 54; upgrade será uma iniciativa separada, com ADR e regressão próprios.

### 3.2 Auditoria inicial de `teste-rota`

| Artefato | Volume | Papel proposto |
|---|---:|---|
| `inventario_semtur.csv` / `data_semtur.json` | 674 | Fonte institucional SEMTUR |
| `santarem-pindobal.csv.csv` / `data.json` | 303 | Recorte enriquecido relacionado à rota |
| `empresas_infraestrutura_rotas.csv` / `pois_data.json` | 737 | POIs coletados/enriquecidos pelo Google Places |
| `rota_porto_OSRM_01.csv` | 884 pontos / 45,229 km | Geometria Porto → Pindobal |
| `rota_aeroporto_OSRM_01.csv` | 777 pontos / 41,452 km | Geometria Aeroporto → Pindobal |
| `rota_rodoviaria_OSRM_01.csv` | 866 pontos / 42,319 km | Geometria Rodoviária → Pindobal |

Os 303 registros do recorte possuem coordenadas válidas segundo o campo `status_coord`. O arquivo consolidado de POIs tem 593 registros de apoio turístico/comercial e 144 de emergência/infraestrutura.

### 3.3 Correções obrigatórias no pipeline existente

- Migrar chamadas de Places Legacy (`nearbysearch/json` e `details/json`) para Places API (New).
- Preservar `google_place_id`; o script atual usa o ID para desduplicar em memória, mas não o exporta no CSV final.
- Guardar proveniência por campo e por execução de ingestão.
- Separar o ID interno estável da ECOnexão do identificador do fornecedor.
- Tratar `segmento_rota` como índice/posição derivada da geometria, não como categoria de negócio.
- Não considerar dados do Google como equivalentes a dados validados pela SEMTUR.
- Implementar reconciliação e fila editorial para possíveis duplicatas SEMTUR × Google.
- Registrar data de coleta, versão do conector, parâmetros, custo estimado e resultado da execução.
- Atualizar Place IDs antigos conforme a política vigente do fornecedor.

## 4. Arquitetura alvo

```text
Expo App
  │ HTTPS/JSON + Bearer token
  ▼
FastAPI /api/v1
  ├── autenticação e autorização
  ├── serviços de domínio
  ├── consultas geoespaciais
  ├── jobs de ingestão
  └── adaptadores de conectores
        ├── Google Places API (New)
        ├── Google Business Profile (somente perfis autorizados)
        ├── Google Routes API
        └── Supabase Storage
  │
  └── Supabase
        ├── PostgreSQL 17 + PostGIS
        ├── Auth
        └── Storage
```

O projeto não exige Docker. Desenvolvimento, homologação e produção utilizarão projetos Supabase separados. Docker/Supabase local poderá ser introduzido posteriormente como opção de isolamento, sem se tornar pré-requisito.

### 4.1 Stack do backend

- Python 3.13.
- FastAPI e Uvicorn.
- Pydantic Settings para configuração.
- SQLAlchemy 2 e psycopg para acesso do FastAPI ao PostgreSQL gerenciado.
- Supabase PostgreSQL 17 com PostGIS.
- GeoAlchemy2 para geometrias.
- Supabase CLI e migrations SQL versionadas como fonte única do schema.
- Supabase Auth e `@supabase/supabase-js` no Expo.
- Supabase Storage para avatar e mídia editorial.
- HTTPX para conectores HTTP.
- pytest, pytest-asyncio e factories para testes.
- Ruff e mypy para qualidade estática.
- OpenTelemetry/Sentry compatível para erros e rastreamento.

### 4.2 Estrutura de diretórios

```text
backend/
  app/
    main.py
    api/v1/
    core/
    db/
    models/
    schemas/
    repositories/
    services/
    connectors/
    ingestion/
    jobs/
  scripts/
  tests/
  pyproject.toml
  .env.example
supabase/
  config.toml
  migrations/
  seed.sql                 # somente fixture mínima; Pindobal usa comando Python
```

As rotas HTTP não devem conter regra de negócio ou SQL direto. A dependência será `API → service → repository/connector`. Alterações de schema, extensões, grants, RLS, policies e funções SQL existirão exclusivamente em `supabase/migrations`; Alembic não será usado em paralelo.

## 5. Estados e responsabilidades

### 5.1 Estado local do aplicativo

- Navegação e abertura/fechamento de modal.
- Texto temporário de busca.
- Chip/filtro selecionado.
- Câmera e nível de zoom do mapa.
- Formulários ainda não enviados.
- Atualização otimista e rollback visual.

### 5.2 Estado remoto

- Regiões, rotas, origens, geometrias, alertas, atores e categorias.
- Usuário, preferências, favoritos, viagens e visitas.
- Conteúdo editorial, suporte, selos e verificação.

O `AppContext` deverá ficar restrito a sessão, região/preferências efetivas e estado global de acessibilidade. Dados remotos deverão usar uma camada de consultas com cache e invalidação; recomenda-se TanStack Query ou uma abstração equivalente, sem duplicar listas completas no reducer.

## 6. Modelo de dados

Todas as tabelas operacionais terão `id UUID`, `created_at`, `updated_at` e, quando aplicável, `deleted_at` para exclusão lógica.

### 6.1 Conteúdo territorial

| Tabela | Campos essenciais |
|---|---|
| `regions` | `slug`, `name`, `state_code`, `center geography(Point)`, `is_active` |
| `routes` | `region_id`, `slug`, `title`, `summary`, `city`, `state_code`, `status`, `is_verified`, `verified_at`, `best_season`, `connectivity`, `road_access`, `payment_info`, `cover_media_id` |
| `route_origins` | `route_id`, `code`, `name`, `description`, `location geography(Point)`, `distance_m`, `duration_s`, `sort_order` |
| `route_geometries` | `route_origin_id`, `provider`, `geometry geography(LineString)`, `encoded_polyline`, `distance_m`, `duration_s`, `source_collected_at` |
| `route_alerts` | `route_id`, `title`, `message`, `severity`, `starts_at`, `ends_at`, `published_at`, `source`, `is_active` |
| `actor_categories` | `slug`, `label`, `icon`, `color`, `sort_order` |
| `actors` | `slug`, `name`, `description`, `category_id`, `sub_category`, `address`, `city`, `state_code`, `phone`, `email`, `instagram`, `website`, `opening_hours JSONB`, `payment_methods JSONB`, `location geography(Point)`, `green_badge_status`, `verification_status` |
| `route_actors` | `route_id`, `actor_id`, `distance_to_route_m`, `route_segment_index`, `origin_flags JSONB`, `is_featured`, `sort_order` |
| `accessibility_features` | `slug`, `label`, `description`, `icon` |
| `actor_accessibility_features` | `actor_id`, `feature_id`, `verification_status`, `verified_at` |
| `media_assets` | `owner_type`, `owner_id`, `storage_key`, `mime_type`, `alt_text`, `credit`, `sort_order` |

Não armazenar avaliação Google como se fosse avaliação própria. Caso exibida, usar campos separados (`google_rating`, `google_review_count`, `google_data_refreshed_at`) e atribuição exigida.

### 6.2 Proveniência e ingestão

| Tabela | Finalidade |
|---|---|
| `external_sources` | Cadastro de SEMTUR, Google Places, GBP e OSRM |
| `actor_external_refs` | `actor_id`, `source_id`, `external_id`, `source_url`, `last_seen_at` |
| `ingestion_runs` | Execução, parâmetros, status, contadores, erros e custos |
| `raw_source_records` | Payload bruto controlado, hash, licença/política e retenção |
| `reconciliation_candidates` | Duplicatas prováveis, score e decisão editorial |
| `field_provenance` | Origem, data e confiança de campos editoriais relevantes |

### 6.3 Usuário

| Tabela | Campos essenciais |
|---|---|
| `profiles` | `id UUID` referenciando `auth.users.id`, `name`, `location`, `avatar_media_id`, `status` |
| `user_preferences` | `user_id`, `active_region_id`, `screen_reader_mode`, `high_contrast`, `text_scale`, `locale` |
| `favorite_routes` | `user_id`, `route_id`, `created_at`; unique composto |
| `favorite_actors` | `user_id`, `actor_id`, `created_at`; unique composto |
| `trips` | `user_id`, `route_id`, `started_at`, `completed_at`, `status` |
| `trip_actor_visits` | `trip_id`, `actor_id`, `visited_at`, `confirmation_method` |

Conforme o ADR 0009, não existem pontuação, CO₂ estimado ou selos pessoais. `trips` e
`trip_actor_visits` permanecem como histórico factual do usuário; selos territoriais
editoriais continuam representados por `green_badge_status` nos atores.

## 7. Contrato HTTP `/api/v1`

### 7.1 Sessão e bootstrap

| Método | Endpoint | Uso |
|---|---|---|
| Supabase Auth | `signInAnonymously` | Criar identidade guest quando habilitada |
| Supabase Auth | Login/cadastro/refresh/logout | Gerenciar sessão no cliente com a SDK oficial |
| `GET` | `/bootstrap` | Perfil, preferências, regiões e feature flags iniciais; exige JWT Supabase |

O Expo obtém o JWT no Supabase Auth e o envia ao FastAPI como Bearer token. O FastAPI valida assinatura, emissor, audiência, expiração e identidade antes de acessar dados do usuário. O MVP começa com anonymous sign-in do Supabase; a mesma identidade poderá ser vinculada a email ou provedor posteriormente. Favoritos nunca serão globais.

### 7.2 Regiões e rotas

| Método | Endpoint | Parâmetros/resultado |
|---|---|---|
| `GET` | `/regions` | Regiões ativas |
| `GET` | `/routes` | `region_id`, `q`, `saved`, `verified`, `cursor`, `limit` |
| `GET` | `/routes/{route_id}` | Hero, overview, stats, origens e resumo de alertas/atores |
| `GET` | `/routes/{route_id}/origins` | Origens disponíveis |
| `GET` | `/routes/{route_id}/geometry` | `origin_id`; GeoJSON/polyline, distância e duração |
| `GET` | `/routes/{route_id}/alerts` | Alertas ativos |
| `GET` | `/routes/{route_id}/actors` | `q`, `category`, `origin_id`, `cursor`, `limit` |
| `GET` | `/routes/{route_id}/map` | Payload enxuto para mapa: geometria, bounds, pins e legenda |

Listas usarão paginação por cursor. Respostas terão envelope uniforme com `data`, `meta` e `error`; erros incluirão `code`, `message`, `request_id` e detalhes seguros.

### 7.3 Atores

| Método | Endpoint | Uso |
|---|---|---|
| `GET` | `/actor-categories` | Chips e legenda |
| `GET` | `/actors/{actor_id}` | Detalhes, contato, horários, acessibilidade, mídia e proveniência pública |
| `POST` | `/actors/{actor_id}/contact-events` | Telemetria consentida de clique em telefone/site/mapa |

### 7.4 Usuário e ações

| Método | Endpoint | Uso |
|---|---|---|
| `GET/PATCH` | `/me` | Perfil |
| `POST` | `/me/avatar-upload` | Upload validado ou URL pré-assinada |
| `GET/PATCH` | `/me/preferences` | Região e acessibilidade |
| `GET` | `/me/favorite-routes` | Rotas salvas |
| `PUT/DELETE` | `/me/favorite-routes/{route_id}` | Idempotente |
| `GET` | `/me/favorite-actors` | Atores salvos |
| `PUT/DELETE` | `/me/favorite-actors/{actor_id}` | Idempotente |
| `GET/POST` | `/me/trips` | Histórico e início de viagem |
| `GET/PATCH` | `/me/trips/{trip_id}` | Concluir/cancelar viagem |
| `POST` | `/me/trips/{trip_id}/visits/{actor_id}` | Registrar visita |
| `GET` | `/content/support` | Ajuda, contatos, termos e operação editorial |

Mutations aceitarão `Idempotency-Key` onde houver risco de repetição por rede móvel.

## 8. Conectores

### 8.1 Google Places API (New)

- Executado somente no backend/job, nunca com chave secreta no Expo.
- Usar Nearby Search (New), Text Search (New) e Place Details (New).
- Usar `X-Goog-FieldMask` mínimo por chamada para controlar custo e dados.
- Persistir `google_place_id` e renovar IDs antigos de acordo com a política vigente.
- Aplicar retries exponenciais, timeout, limites de concorrência, orçamento e circuit breaker.
- Guardar atribuições e separar dado Google de dado editorial ECOnexão.
- Não executar nova varredura a cada abertura de tela; o aplicativo consulta o banco normalizado.

Referências:  
https://developers.google.com/maps/documentation/places/web-service/nearby-search  
https://developers.google.com/maps/documentation/places/web-service/place-id  
https://developers.google.com/maps/documentation/places/web-service/data-fields

### 8.2 Google Business Profile

O conector GBP será opcional e restrito a empreendimentos que autorizarem a ECOnexão a administrar ou sincronizar seus perfis. Ele não substitui o Places para descoberta territorial. A API exige projeto Google Cloud, finalidade legítima, site e aprovação; acesso de terceiros usa OAuth e permissões do cliente.

Referência: https://developers.google.com/my-business/content/overview

### 8.3 Roteamento dinâmico

- Preservar as três geometrias OSRM existentes como origens oficiais importadas;
  elas não autorizam um serviço OSRM em runtime.
- Conforme ADR 0013 e Gate H3 revisado, previews dinâmicos usam exclusivamente
  Google Routes API v2 `ComputeRoutes Essentials`, via FastAPI e field mask mínima.
- Provider, quota, custo, latência e resultado são observados sem coordenadas.
- Provider desconhecido ou indisponível falha fechado; o cliente restaura uma origem
  oficial e nunca usa Fake automaticamente fora de development/test.
- Permitir trocar o fornecedor sem mudar o contrato do aplicativo.

### 8.4 Mapas no aplicativo

Manter `MapAdapter` como abstração. No nativo, usar um mapa compatível com a versão Expo escolhida e provedor configurado; no web, usar adaptador Leaflet/MapLibre. O domínio não dependerá do SDK visual. A chave pública de renderização, se necessária, terá restrições por bundle/package, assinatura e API.

### 8.5 Supabase Storage

Avatares e mídia editorial irão para Supabase Storage. O banco guardará metadados e chaves, não binários. Uploads terão MIME allowlist, limite de tamanho, remoção de EXIF, redimensionamento, antivírus quando aplicável e URLs com política adequada. Policies de Storage serão versionadas; upsert só será usado quando as permissões `INSERT`, `SELECT` e `UPDATE` estiverem explicitamente testadas.

### 8.6 Limites de exposição do Supabase

- O Expo usa diretamente apenas Auth e operações de Storage expressamente definidas.
- Dados de domínio passam pelo FastAPI; tabelas de domínio devem ficar em schema privado/não exposto sempre que possível.
- Se uma tabela precisar da Data API, `GRANT` e RLS serão explícitos na migration; criação em `public` não implica exposição automática.
- RLS será habilitado em toda tabela exposta e também aplicado como defesa em profundidade a dados por usuário.
- Policies de proprietário usarão `(select auth.uid()) = user_id`; `TO authenticated` isolado não é autorização suficiente.
- Views expostas usarão `security_invoker = true` no PostgreSQL 15+.
- Funções `SECURITY DEFINER` não serão usadas para contornar falhas de policy; quando inevitáveis, ficarão em schema privado, validarão `auth.uid()` e terão grants mínimos.
- Nenhum objeto customizado será criado nos schemas gerenciados `auth`, `storage` ou `realtime`.
- `service_role`/secret key nunca será enviado ao Expo. O aplicativo recebe apenas URL e publishable key.

## 9. Pipeline Pindobal

1. Copiar fontes aprovadas para uma área controlada de importação, preservando hash e nome original.
2. Importar região e rota Pindobal.
3. Importar as três origens e converter os pontos OSRM em `LineString`.
4. Importar SEMTUR como fonte institucional.
5. Importar POIs Google existentes como snapshot legado, marcando data e limitações.
6. Normalizar telefone, URLs, horários, categorias, coordenadas e formas de pagamento.
7. Executar deduplicação determinística por identificador externo e fuzzy por nome/distância/telefone.
8. Criar candidatos de reconciliação; não mesclar automaticamente casos ambíguos.
9. Relacionar atores à rota via PostGIS (`ST_DWithin`, projeção/posição na linha e origem aplicável).
10. Validar contagens, distâncias, endpoints e amostras visuais.
11. Publicar somente registros aprovados e manter relatório de rejeitados.

O CSV/JSON será entrada de uma migration de dados ou comando de seed reproduzível, nunca lido diretamente pela API em produção.

## 10. Comportamento transversal da interface

- Toda consulta terá loading/skeleton, vazio, erro e retry.
- Busca remota terá debounce de 300–500 ms, cancelamento da requisição anterior e query na URL quando útil.
- Favoritos usarão atualização otimista com rollback e mensagem acessível em falha.
- Foco será movido corretamente ao abrir/fechar modais e navegar por deep link.
- Região selecionada invalidará consultas de rotas e será persistida em `/me/preferences`.
- Parâmetros `actorId`, `originId`, `category` e `saved` serão serializáveis na navegação.
- Ausência de rede mostrará cache identificado como possivelmente desatualizado; mutations ficarão bloqueadas ou em fila explícita, nunca silenciosamente perdidas.
- Ações de telefone, site, Instagram e Google Maps abrirão links externos após validação.

## 11. Matriz de integração por tela

### 11.1 Global

| Elemento | Comportamento final | Backend |
|---|---|---|
| Voltar | `router.back()` com fallback seguro | Não |
| Chip de região | Abre seletor; salva escolha; recarrega contexto | `GET /regions`, `PATCH /me/preferences` |
| Abas | Navegação local e estado de foco | Não |
| Inicialização | Carrega fontes, sessão Supabase, bootstrap e cache | Supabase Auth; `GET /bootstrap` |

### 11.2 Início

| Elemento | Comportamento final | Backend |
|---|---|---|
| Badge da região | Mesmo seletor global, sem valor fixo | Regiões/preferências |
| Descobrir Rotas | Abre `/routes` na região ativa | Não; tela destino consulta API |
| Ver todas | Abre rotas com `saved=true` | Não; filtro serializado |
| Card salvo | Abre detalhe da rota | `GET /routes/{id}` |
| Coração | Remove/adiciona favorito com rollback | `PUT/DELETE /me/favorite-routes/{id}` |
| Estado vazio | CTA adicional para explorar rotas | Não |

### 11.3 Rotas

| Elemento | Comportamento final | Backend |
|---|---|---|
| Busca e limpar | Busca paginada por nome/cidade/resumo | `GET /routes?q=` |
| Todas/Salvas/Verificadas | Filtros combináveis e acessíveis | `GET /routes?saved=&verified=` |
| Card | Deep link para detalhe | `GET /routes/{id}` |
| Coração | Favorito persistente | Endpoint de favorito |
| Limpar filtros | Limpa busca/filtros e recarrega | `GET /routes` |

### 11.4 Perfil

| Elemento | Comportamento final | Backend |
|---|---|---|
| Avatar | Abre edição, seleciona imagem e envia | `POST /me/avatar-upload`, `PATCH /me` |
| Rotas concluídas | Abre histórico filtrado | `GET /me/trips?status=completed` |
| Rotas salvas | Navega para rotas com `saved=true` | Favoritos de rota |
| Atores favoritos | Abre nova tela/lista de atores salvos | Favoritos de atores |
| Histórico | Abre nova tela de viagens | Trips |
| Leitor/alto contraste | Abre configurações e aplica imediatamente | Preferências |
| Configurações regionais | Abre seletor de região | Regiões/preferências |
| Suporte | Abre conteúdo, contatos e termos | `GET /content/support` |

### 11.5 Detalhes da rota

| Elemento | Comportamento final | Backend |
|---|---|---|
| Origem | Atualiza distância, duração, geometria e atores aplicáveis | Geometry/map por `origin_id` |
| Informações práticas (`RouteStats`) | Não são exibidas nesta versão; o componente e os campos permanecem preparados para futuras experiências | `GET /routes/{id}` mantém `best_season`, `connectivity`, `road_access` e `payment_info` |
| Expandir mapa/overlay | Abre mapa com `originId` | `GET /routes/{id}/map` |
| Pin do preview | Abre mapa preservando `actorId` | Map payload |
| Alertas | Lista apenas alertas ativos; tipo visual correto | Alerts |
| Ver todos/CTA catálogo | Abre catálogo contextual | Actors |
| Card resumido de ator | Abre detalhe do ator | `GET /actors/{id}` |
| Tentar novamente | Repete a consulta; voltar fica separado | `GET /routes/{id}` |

Decisão de produto registrada em 22/08/2026: a tela atual de detalhe prioriza origem,
mapa, catálogo, alertas e atores. A retirada visual de `RouteStats` não remove nem
deprecia os quatro campos do contrato HTTP, que poderão ser reutilizados em uma
experiência futura mediante atualização desta matriz e dos critérios de aceite.

### 11.6 Mapa

| Elemento | Comportamento final | Backend |
|---|---|---|
| Zoom +/− | Controla câmera real respeitando limites | Não |
| Pins | Selecionam ator e abrem bottom sheet | Dados do map payload |
| Chips | Filtram pins; categorias completas com rolagem | Payload/categoria; nova consulta se necessário |
| Fechar sheet/backdrop | Fecha sem propagar toque | Não |
| Ver no catálogo | Abre catálogo com `actorId` focado | Actors |
| Abrir externamente | Abre navegação/mapa externo quando oferecido | URL validada |

### 11.7 Catálogo e ator

| Elemento | Comportamento final | Backend |
|---|---|---|
| Busca/limpar | Busca por nome, subcategoria e descrição | Actors com `q` |
| Categorias | Filtro real, contagem e paginação | Actors com `category` |
| Card | Abre nova rota `/actor/[actorId]` ou modal endereçável | `GET /actors/{id}` |
| Coração | Favorito persistente | Endpoint de favorito |
| Limpar filtros | Restaura consulta padrão | Actors |
| Telefone/site/Instagram/mapa | Abre destino e registra evento consentido | Actor/contact-events |

## 12. Segurança, privacidade e políticas

- Segredos somente no backend/secret manager.
- Tokens Supabase no dispositivo em armazenamento seguro, nunca em AsyncStorage puro sem proteção.
- Senhas com algoritmo moderno e parâmetros revisados; preferir provedor de identidade quando adequado.
- Autorização por objeto em todos os endpoints `/me`.
- Rate limit em login, busca cara, contato e ingestão.
- FastAPI valida JWT Supabase em toda rota protegida; dados de `user_metadata` não autorizam acesso.
- CORS com origens explícitas no web; CORS não substitui autenticação.
- Logs sem tokens, senhas, chaves, payloads pessoais ou URLs assinadas.
- Consentimento e política de privacidade para telemetria e localização.
- LGPD: finalidade, minimização, retenção, exportação e exclusão do usuário.
- Revisão das políticas Google antes de armazenar/exibir dados, fotos, avaliações e atribuições.

## 13. Testes e observabilidade

### Backend

- Testes unitários de normalização, deduplicação, distância e permissões.
- Testes de integração em PostgreSQL/PostGIS real.
- Testes de contrato de todos os endpoints.
- Fixtures Pindobal pequenas e determinísticas; testes completos do importador separados.
- Testes de idempotência e concorrência de favoritos.

### Aplicativo

- Testes de componentes para loading, vazio, erro e acessibilidade.
- Testes de integração dos hooks/client HTTP.
- E2E dos fluxos críticos em Android, iOS e web conforme escopo suportado.
- Verificação de deep links, restauração de sessão e perda de rede.

### Observabilidade

- `request_id` ponta a ponta.
- Métricas de latência, taxa de erro, cache, ingestão e custo por conector.
- Alertas para falha de login, aumento de 5xx, pipeline incompleto e orçamento Google.
- Health endpoints distintos para processo vivo e dependências prontas.

## 14. Ambientes e entrega

- `development`: projeto Supabase exclusivo de desenvolvimento; conectores externos desligados por padrão.
- `test`: projeto Supabase exclusivo de testes automatizados, dados descartáveis e conectores simulados.
- `staging`: projeto Supabase separado com dados Pindobal aprovados, chaves restritas e build de homologação.
- `production`: projeto Supabase de produção, migrations controladas, backups, HTTPS, secrets e observabilidade.

Agentes e testes nunca poderão receber credenciais de produção. Migrations deverão ser promovidas na ordem development → staging → production, com verificação de advisors e consultas de smoke test em cada etapa.

CI deverá executar lint, tipos, testes, validação de migrations e build do Expo. Deploy de schema deve ser compatível com a versão anterior durante a janela de publicação do aplicativo.

## 15. Fora do escopo inicial

- Painel editorial completo. A API e o modelo devem permitir sua criação posterior.
- Navegação curva a curva em tempo real.
- Pagamentos e reservas.
- Avaliação própria de atores por usuários.
- Sincronização GBP para empresas sem autorização explícita.

## 16. Decisões registradas

1. Supabase PostgreSQL + PostGIS desde o início, pois proximidade e geometria são parte central do domínio.
2. Pindobal será importada por pipeline reproduzível, não por leitura de CSV em runtime.
3. Chamadas Google serão server-side e assíncronas/editoriais.
4. OSRM e Google serão adaptadores substituíveis.
5. A interface terá atualização otimista somente em mutations idempotentes.
6. Todo falso botão atual será implementado ou perderá a semântica de botão antes da entrega.
7. Docker não é pré-requisito; projetos Supabase separados fornecem os ambientes remotos.
8. Supabase Auth e Storage substituem autenticação e storage próprios.
9. Migrations SQL em `supabase/migrations` são a única fonte de verdade do schema.
10. O FastAPI permanece como API de domínio e fronteira para Google Places, GBP, OSRM e ingestão.

## 17. Referências normativas externas

Consultar novamente antes de implementar, pois os produtos mudam:

- Supabase changelog: https://supabase.com/changelog
- Exposição explícita da Data API: https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically
- Segurança da Data API/RLS: https://supabase.com/docs/guides/api/securing-your-api
- Supabase Auth: https://supabase.com/docs/guides/auth
- PostGIS no Supabase: https://supabase.com/docs/guides/database/extensions/postgis
- Supabase Storage: https://supabase.com/docs/guides/storage
- Expo SDK 54: https://docs.expo.dev/versions/v54.0.0/
- Places API (New): https://developers.google.com/maps/documentation/places/web-service
- Google Business Profile: https://developers.google.com/my-business/content/overview
- OSRM API: https://project-osrm.org/docs/v5.24.0/api/
