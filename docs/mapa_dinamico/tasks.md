# Backlog proposto — ECO-2301 a ECO-2315

> **Registro histórico de aceites e evidências.** O cadastro completo, status e ordem
> atuais estão em [project_status.md](../project_status.md). O novo desenho sem clusters
> e a homologação Web são definidos ali. Os estados abaixo são snapshots históricos.

Status do backlog: `PROPOSED`  
Regra: uma task só fica ativa quando suas dependências e gates estiverem registrados.

Este arquivo torna as tasks localizáveis pelo playbook. O detalhe operacional e os
aceites estão no prompt correspondente. Um prompt não substitui decisão humana.

| Task | Título | Tamanho | Dependências | Condição de conclusão |
|---|---|---:|---|---|
| ECO-2301 | Decisão de taxonomia visual | S | nenhuma nova | ADR 0010 aceito pelo owner (Concluído em 2026-08-24) |
| ECO-2302 | Schema e normalização da taxonomia | M | ECO-2301 | VERIFIED em 2026-08-24 no Supabase test: 21/21 migrations alinhadas, dry-run final vazio, oito categorias/metadados exatos, remediação auditável e reversível aplicada, testes SQL positivos/negativos aprovados e advisors sem findings |
| ECO-2303 | Contrato visual do mapa v2 | M | ECO-2302 | OpenAPI/backend/tipos sem drift (Concluído em 2026-08-24) |
| ECO-2304 | Pins e legenda no frontend | M | ECO-2303 | web verificada; nativo conforme ambiente (Concluído em 2026-08-24) |
| ECO-2305 | Decisão de camadas espaciais | S | ECO-2301 | ADR 0011 aceito pelo owner (Concluído em 2026-08-24) |
| ECO-2306 | Backend das camadas estáticas | L | ECO-2303, ECO-2305 | VERIFIED em 2026-08-25 no Supabase test: migration forward 20260825003236 aplicada sem editar a migration registrada, 22 versões alinhadas, matriz PostGIS/negativos com rollback aprovada, advisors sem findings e 370 testes backend aprovados |
| ECO-2307 | Interface Rota × Cidade | M | ECO-2304, ECO-2306 | câmera/densidade/acessibilidade verificadas (Concluído em 2026-08-24) |
| ECO-2308 | ADR de origens dinâmicas | S | ADR 0003 | ADR 0012 aceito pelo owner (Concluído em 2026-08-24) |
| ECO-2309 | Preview dinâmico com fake | M | ECO-2308 | endpoint/contrato/fake sem escrita nem rede (VERIFIED em 2026-08-24) |
| ECO-2310 | Minha localização | M | ECO-2309 | Remediação concluída em 2026-08-26: integração de feature_flags.dynamic_routing via AppContext com fail-closed estrito; ocultação e bloqueio de request de GPS quando flag for false; preservação de fluxo e acessibilidade quando flag for true; 3 origens fixas perenes; Web VERIFIED; Android/iOS mantido PARTIAL por ausência de device físico/emulador |
| ECO-2311 | Escolher no mapa | M | ECO-2309 | Remediação concluída em 2026-08-26: consumo estrito de feature_flags.dynamic_routing via AppContext e fail-closed; ocultação e bloqueio de "Escolher no mapa" e seleção de origem quando flag for false; preservação integral de seleção interativa, dragend, preview efêmero via TanStack Query memory cache, WCAG (foco, aria-live, teclado web) e 3 origens fixas quando flag for true; fallback com preservação de rota oficial válida em caso de erro/timeout; zero coordenadas em URLs ou persistência; Web VERIFIED; Android/iOS mantido PARTIAL por ausência de device físico/emulador |
| ECO-2312 | Pins na geometria dinâmica | L | ECO-2306, ECO-2309 | VERIFIED em 2026-08-25: isolamento estrito por region_id em find_corridor_actors_by_geometry, semântica canônica de camadas ADR 0011 (route_corridor, citywide_essential, both), ordenação estável e limite STATIC_MAP_MAX_PINS (200), consumo e repasse de pins/legend/city_bounds pelo RouteMapPreview, expansão de mapa com preservação de contexto efêmero via TanStack Query cache, zero persistência em banco e 387 testes backend + 182 testes frontend aprovados |
| ECO-2313 | Benchmark e decisão de provedor | M | ECO-2308, ECO-2309 | Gate H3 revisado pelo Owner em 2026-08-25: Google Routes API v2 `ComputeRoutes Essentials` substitui OSRM Self-Hosted; gasto variável pago não autorizado; ADR 0013 aceito (VERIFIED) |
| ECO-2314 | Conector real e guardrails | L | ECO-2313, H3 | PARTIAL em 2026-08-25: GoogleRoutesConnector e guardas offline implementados; 407 testes backend aprovados; staging permanece desligado e bloqueado por secret manager, termos/privacidade, validação Google Maps e smoke explicitamente autorizado |
| ECO-2315 | Verificação final | L | ECO-2301–ECO-2314 | evidência separada local/staging/device e GO/NO-GO humano |

## Gates de ativação

- **H1:** ADR 0012 aceito [ATINGIDO em 2026-08-24]; desbloqueia ECO-2309.
- **H2a:** ADR 0010 aceito [ATINGIDO em 2026-08-24]; desbloqueia ECO-2302 para próxima sessão.
- **H2b:** ADR 0011 aceito [ATINGIDO em 2026-08-24]; desbloqueia ECO-2306.
- **H3 revisado:** Google Routes API v2 `ComputeRoutes Essentials`, quota de
  10 previews/min, bloqueio antes da franquia gratuita, nenhum gasto variável pago,
  nenhum fallback Fake e Owner registrados [ATINGIDO em 2026-08-25]. ECO-2314 fica
  bloqueada até reconciliar a implementação com o ADR 0013.

## Status permitidos

- `PROPOSED`: definida, ainda não ativada.
- `BLOCKED`: gate ou dependência faltante.
- `IN_PROGRESS`: uma única sessão/executor possui a task.
- `PARTIAL`: incremento implementado, mas falta evidência obrigatória.
- `NOT_VERIFIABLE`: ambiente necessário indisponível.
- `VERIFIED`: evidência material reproduzida por testador/revisor independente.

Não usar `DONE` como substituto de evidência.
