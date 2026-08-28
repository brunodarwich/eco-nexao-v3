# Fluxo Principal – Jornada de Valor

**Jornada principal** (valor imediato ao usuário):

1. **Entrada:** Usuário abre o aplicativo Expo → App carrega sessão anônima via Supabase Auth (`signInAnonymously`).
   - Evidência: `docs/backend_integration_spec.md` §7.1 (linhas 208‑212) descreve o uso do **Supabase Auth** para criar identidade guest.
   - Evidência: `docs/backend_integration_spec.md` §7.2 (linhas 210‑211) descreve o endpoint `/bootstrap` que devolve perfil, preferências e região ativa.
2. **Ação:** App solicita **bootstrap** ao backend (`GET /bootstrap`).
   - Evidência: `docs/backend_integration_spec.md` linha 210‑211.
3. **Ação:** Usuário seleciona a **região** ativa (ou aceita padrão) → App exibe lista de **rotas** (`GET /routes`).
   - Evidência: `docs/backend_integration_spec.md` §7.2 tabela de rotas (linhas 218‑220).
4. **Resultado:** Usuário escolhe uma rota (ex.: *Rota Pindobal*) → App carrega **detalhes da rota** (`GET /routes/{route_id}`) incluindo três origens, geometria, atores, alertas.
   - Evidência: `docs/backend_integration_spec.md` linha 220‑224 (detalhes da rota e origens).
5. **Ação:** Usuário interage com o **mapa** (zoom, troca de origem) → App requisita payload de mapa (`GET /routes/{route_id}/map`).
   - Evidência: `docs/backend_integration_spec.md` linha 225 (payload enxuto para mapa).
6. **Resultado:** Mapa exibe pins de **atores**; ao tocar num pin, app abre **detalhes do ator** (`GET /actors/{actor_id}`).
   - Evidência: `docs/backend_integration_spec.md` §7.3 linha 233‑235 (endpoint de ator e evento de contato).
7. **Ação (opcional, mas parte do fluxo de valor):** Usuário pode **favoritar** rota ou ator (`PUT /me/favorite-routes/{id}` ou `PUT /me/favorite-actors/{id}`).
   - Evidência: `docs/backend_integration_spec.md` linhas 354‑357 (favoritar rotas) e 416‑418 (favoritar atores).
8. **Resultado final:** Usuário tem a rota selecionada com mapa funcional, visualiza atores relevantes e pode salvar favoritos para uso futuro – entrega valor imediato de descoberta e planejamento de visita.

---
## Funcionalidades obrigatórias (necessárias para o fluxo acima)
- **Supabase Auth – login anônimo** (`signInAnonymously`).
- **Endpoint `/bootstrap`** para inicialização de sessão e obtenção de região ativa.
- **Endpoints de rotas**: `GET /routes`, `GET /routes/{id}`, `GET /routes/{id}/origins`, `GET /routes/{id}/map`.
- **Endpoints de atores**: `GET /actors/{id}` e `POST /actors/{actor_id}/contact-events` (para registro de interação).
- **Endpoints de favoritos**: `PUT/DELETE /me/favorite-routes/{id}` e `PUT/DELETE /me/favorite-actors/{id}`.
- **Cliente Expo** com integração Supabase JS (`@supabase/supabase-js`) para autenticação e chamadas HTTP autenticadas.
- **MapAdapter** (abstração de mapa) que consome payload `/routes/{id}/map`.
- **Gerenciamento de estado** (region, selected route, selected origin, selected actor) no `AppContext` conforme especificado em `backend_integration_spec.md` §5.1‑5.2.

---
## Funcionalidades secundárias (podem ser adiadas sem impedir testes iniciais)
- **Busca avançada** (texto, filtros por cidade, categoria) – endpoint `GET /routes?q=` está presente, mas a lista simples de rotas já satisfaz o fluxo.
- **Filtros de atores** (chips por categoria, origem) – uso opcional das queries `GET /routes/{id}/actors` com parâmetros.
- **Alertas de rota** – endpoint `/routes/{id}/alerts` pode ser ignorado nos primeiros testes.
- **Perfil de usuário avançado** (edição de avatar, preferências de acessibilidade) – não essencial para descoberta de rotas.
- **Suporte e conteúdo estático** (`GET /content/support`).
- **Integração com Google Business Profile** – opcional, documento §8.2; não impacta o fluxo principal.
- **Exportação de CSV/Exportação de dados** – fora do escopo de UI inicial.
- **Teste de acessibilidade avançado** – já coberto por requisitos de estado mas pode ser postergado.

---
**Arquivos consultados como evidência**
- `docs/backend_integration_spec.md` (linhas ~208‑224, 233‑235, 354‑357) – define endpoints e fluxo de dados.
- `docs/README.md` – indica documentos de referência e visão geral do produto.
- `docs/elementos_interativos_telas.txt` (não usado diretamente aqui, mas lista de telas que confirmam existência das UI mencionadas).
