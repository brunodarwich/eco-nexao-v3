# Critérios de aceite ponta a ponta

Estes cenários complementam as tasks. Cada fluxo deve ser testado em todas as plataformas aprovadas pelo ADR 0003.

## Global e sessão

### AC-GLOBAL-01 — Primeira abertura

- Sem sessão, o app cria identidade anônima no Supabase Auth.
- O JWT é enviado ao FastAPI e `/bootstrap` retorna perfil, preferências e regiões.
- Falha de Auth ou bootstrap exibe erro recuperável; não carrega mock silencioso.

### AC-GLOBAL-02 — Trocar região

- Header e hero abrem o mesmo seletor.
- Escolha persiste em preferências e atualiza rotas/salvos sem misturar caches.
- Cancelar mantém a região anterior.

## Início

### AC-HOME-01 — Rotas salvas

- Lista corresponde ao usuário atual.
- Card abre a rota correta.
- Remoção por coração é otimista; falha restaura o item e anuncia o erro.
- Estado vazio oferece ação para explorar rotas.

## Rotas

### AC-ROUTES-01 — Busca e filtros

- Busca tem debounce/cancelamento e aceita nome, cidade e resumo.
- Todas, Salvas e Verificadas combinam-se conforme contrato.
- Limpar restaura consulta padrão.
- Paginação não duplica cards.

### AC-ROUTES-02 — Navegação e favorito

- Card e coração são alvos independentes.
- Deep link de rota válida funciona; inexistente mostra 404 e retry real.

## Perfil

### AC-PROFILE-01 — Avatar

- Toque abre seletor; cancelamento não altera perfil.
- Arquivo inválido é rejeitado.
- Upload respeita policy de ownership; falha faz rollback.

### AC-PROFILE-02 — Menu

- Rotas salvas, atores favoritos, histórico, acessibilidade, região e suporte abrem destinos corretos.
- O perfil não exibe painel de impacto ecológico, estimativa de CO₂ ou selo pessoal.
- Sem nome cadastrado, a sessão anônima exibe o fallback neutro “Visitante”.
- Histórico de viagens/visitas continua acessível sem atribuir impacto ambiental.
- Nenhum item mantém semântica de botão sem ação.

## Detalhe da rota

### AC-ROUTE-01 — Pindobal

- Hero, alertas e atores vêm da API.
- A tela atual não exibe a seção `RouteStats` nem placeholders de melhor época,
  conectividade, acesso ou pagamentos; esses campos permanecem no contrato para
  possível uso futuro.
- Retry repete request; Voltar não é usado como retry.

### AC-ROUTE-02 — Origem

- Porto, Aeroporto e Rodoviária atualizam distância, geometria, bounds e descrição.
- Valores respeitam tolerâncias do contrato Pindobal.
- Origem selecionada é preservada ao abrir mapa e catálogo.

### AC-ROUTE-03 — Preview

- O detalhe exibe um preview real do mapa para a origem selecionada e permite
  ocultar/mostrar o bloco sem perder a seleção.
- “Expandir mapa” abre a experiência em tela cheia preservando `originId`.
- Pin abre mapa com `actorId` selecionado.
- Links/CTAs abrem mapa ou catálogo da mesma rota.
- O catálogo local exibe total retornado pela API, filtros reais e até três cards
  compactos; foto ausente usa placeholder explícito, nunca imagem fabricada.
- Foto disponível usa o derivado `card`/URL resolvida e o `alt_text` editorial.

## Mapa

### AC-MAP-01 — Câmera

- `+` e `−` alteram zoom real e ficam indisponíveis nos limites.
- Linha e bounds correspondem à origem.

### AC-MAP-02 — Pins e filtros

- Categoria filtra pins sem alterar dados persistidos.
- Pin abre sheet correta; X/backdrop fecha sem acionar conteúdo abaixo.
- “Ver no catálogo” preserva `actorId` e foco.

## Catálogo e ator

### AC-CATALOG-01 — Lista

- Busca, limpar, categorias, contagem e paginação usam API.
- Empty state limpa filtros.
- Favorito é persistente e isolado por usuário.

### AC-CATALOG-02 — Detalhe e contato

- Card abre URL endereçável `/actor/[actorId]`.
- Detalhe mostra somente campos disponíveis, acessibilidade e atribuições.
- Telefone/site/Instagram/mapa validam URL e tratam ausência/erro.

## Segurança por usuário

### AC-SEC-01 — Isolamento

- Usuário A não lê nem altera perfil, favoritos, viagens, visitas ou avatar do usuário B.
- Anonymous user não obtém privilégio editorial por estar no papel `authenticated`.
- Chaves secret/service role não aparecem no bundle, logs ou erros.

## Estados comuns

Para cada consulta: loading, sucesso, vazio, 401/refresh, 403, 404, 422, 5xx, timeout, offline e retry. Para cada mutation: sucesso, toque duplicado, falha com rollback e sessão expirada.
