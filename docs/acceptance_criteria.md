# Critérios de aceite ponta a ponta

Estes cenários complementam as tasks. Cada fluxo deve ser testado em todas as plataformas aprovadas pelo ADR 0003.

## Global e sessão

### AC-GLOBAL-01 — Primeira abertura e persistência de sessão

- Sem sessão, o app cria identidade anônima no Supabase Auth.
- Na Web, a sessão persiste em `localStorage` com rotação de refresh token (ADR 0007); recarregar a página (F5) não perde o contexto nem gera novo UUID órfão.
- O JWT é enviado ao FastAPI e `/bootstrap` retorna perfil, preferências e regiões.
- Falha de Auth ou bootstrap exibe erro recuperável; não carrega mock silencioso.

### AC-GLOBAL-02 — Trocar região

- Header e hero abrem o mesmo seletor.
- Escolha persiste em preferências e atualiza rotas/salvos sem misturar caches.
- Cancelar mantém a região anterior.

### AC-GLOBAL-03 — Login Google e Account Linking

- Usuário guest pode efetuar login/vínculo com conta Google (`ECO-2606`).
- Vinculação com nova conta preserva favoritos e histórico da sessão anônima sem perda de dados.
- Conflito com conta existente que já possui e-mail registrado informa o usuário e oferece login seguro (Opção 1 do ADR 0007).

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

### AC-PROFILE-02 — Menu e histórico de viagens

- Rotas salvas, atores favoritos, histórico de viagens, acessibilidade, região e suporte abrem destinos corretos.
- O perfil não exibe painel de impacto ecológico, estimativa de CO₂ ou selo pessoal (ADR 0009).
- Sem nome cadastrado, a sessão anônima exibe o fallback neutro “Visitante”.
- Histórico de viagens permite iniciar, pausar, retomar e concluir viagem (`ECO-2607`), persistido no backend sem telemetria contínua gravada.
- Nenhum item mantém semântica de botão sem ação.

## Detalhe da rota

### AC-ROUTE-01 — Informações da rota

- Hero, alertas e atores vêm da API.
- A tela atual não exibe a seção `RouteStats` nem placeholders de melhor época,
  conectividade, acesso ou pagamentos; esses campos permanecem no contrato para
  possível uso futuro.
- Retry repete request; Voltar não é usado como retry.

### AC-ROUTE-02 — Origens e posição do usuário

- Seletor compacto permite escolher entre as origens oficiais homologadas (Porto, Aeroporto, Rodoviária), atualizando distância, geometria e corredor de atores.
- Acompanhamento da posição do usuário em primeiro plano no mapa opera sob consentimento/permissão GPS (`ECO-2609`).
- Exibir a posição atual não força recálculo dinâmico da rota; falha ou negação de GPS mantém a origem fixa selecionada com anúncio acessível; sem navegação por voz ou curva a curva.

### AC-ROUTE-03 — Preview e catálogo contextual

- O detalhe exibe um preview real do mapa para a origem selecionada e permite
  ocultar/mostrar o bloco sem perder a seleção.
- “Expandir mapa” abre a experiência em tela cheia preservando `originId`.
- Pin abre mapa com `actorId` selecionado.
- Links/CTAs abrem mapa ou catálogo da mesma rota.
- O catálogo exibe carrosséis por categoria (ADR 0015 / `ECO-2610`) e filtros por tags de experiência (`ECO-2611`).
- Foto disponível usa o derivado `card`/URL resolvida e o `alt_text` editorial; foto ausente usa placeholder explícito, nunca imagem fabricada.

## Mapa

### AC-MAP-01 — Câmera e camadas

- `+` e `−` alteram zoom real e ficam indisponíveis nos limites.
- Linha e bounds correspondem à origem (`route_bounds` estrito conforme ADR 0011).
- Serviços municipais de saúde/segurança não distorcem o enquadramento do corredor turístico da rota.

### AC-MAP-02 — Pins sem clusters e filtros

- Marcadores (pins) são exibidos sem agrupamentos numéricos (clusters), com cor e ícone por categoria canônica (ADR 0010 / `ECO-2608`).
- Densidade visual é controlada por nível de zoom e filtragem ativa, sem deslocar coordenadas nem gerar localizações falsas.
- O estabelecimento selecionado permanece visível com destaque visual e prioridade de z-index.
- Pin abre sheet correspondente; X/backdrop fecha sem acionar conteúdo abaixo.
- “Ver no catálogo” preserva `actorId` e foco acessível.

## Catálogo e ator

### AC-CATALOG-01 — Lista e carrosséis

- Busca, limpar, categorias em seções, contagem e paginação usam API.
- Relevância editorial padrão por completude cadastral com opção alfabética (`ECO-2612`).
- Empty state oferece ação clara para limpar filtros.
- Favorito é persistente e isolado por usuário.

### AC-CATALOG-02 — Detalhe, contato e fotos Google sob demanda

- Card abre URL endereçável `/actor/[actorId]`.
- Detalhe mostra campos disponíveis, acessibilidade, selo SEMTUR quando aplicável (ADR 0014) e atribuições.
- Fotos do Google Places (quando disponíveis) são carregadas sob demanda via proxy efêmero no FastAPI (ADR 0016 / `ECO-2613`), com atribuição de autoria e link ao Google Maps (`googleMapsUri`), sem armazenamento de binários em Storage e com fallback elegante em caso de indisponibilidade ou ausência de imagem.
- Telefone/site/Instagram/mapa validam URL e tratam ausência/erro.

## Segurança por usuário

### AC-SEC-01 — Isolamento

- Usuário A não lê nem altera perfil, favoritos, viagens, visitas ou avatar do usuário B.
- Anonymous user não obtém privilégio editorial por estar no papel `authenticated`.
- Chaves secret/service role não aparecem no bundle, logs ou erros.

## Estados comuns

Para cada consulta: loading, sucesso, vazio, 401/refresh, 403, 404, 422, 5xx, timeout, offline e retry. Para cada mutation: sucesso, toque duplicado, falha com rollback e sessão expirada.
