# ECOnexão — Guia de desenvolvimento

## Estado do repositório

O aplicativo Expo está em `econexao-app/` e o scaffold FastAPI está em
`backend/`. O diretório `supabase/` contém migrations ainda não verificadas em
um projeto remoto. Comandos Supabase continuam planejados até a conclusão das
tasks ECO-0102, ECO-0103 e ECO-0107.

## Pré-requisitos

- Node.js compatível com Expo SDK 54.
- npm.
- Python 3.13 e ambiente virtual.
- Supabase CLI na versão aprovada pelo projeto.
- Acesso somente aos projetos Supabase do ambiente necessário.
- Android Studio/emulador para Android; ambiente Apple para iOS; navegador para web.

Docker não é obrigatório.

## Frontend atual

```powershell
cd econexao-app
npm install
npm run web
```

Para Android:

```powershell
cd econexao-app
npm run android
```

Não execute upgrade do Expo durante tasks de integração.

### Sessão Supabase no Expo

- Android/iOS persistem a sessão no Keychain/Keystore por `expo-secure-store`.
- Web mantém a sessão somente em memória. Recarregar a página cria uma nova
  identidade guest; persistência durável segura exige um BFF com cookie
  `HttpOnly` e permanece como decisão da ECO-0706.
- O bootstrap de Auth restaura uma sessão existente ou executa
  `signInAnonymously()` uma única vez, mesmo sob inicializações concorrentes.
- O cliente HTTP envia o access token ao FastAPI e faz no máximo uma repetição
  após 401, com refresh compartilhado entre requests concorrentes.
- Logout de guest é irreversível para aquela identidade. O aplicativo fica sem
  sessão até a ação explícita de tentar novamente criar um novo guest.
- Vínculo por email está preparado com `updateUser`. OAuth, PKCE, redirects e
  resolução de conflito com conta existente continuam pendentes de definição.

Verificação local:

```powershell
cd econexao-app
npm run typecheck
npm test -- --watch=false --forceExit
npx expo-doctor
```

### Contrato OpenAPI e tipos TypeScript

`docs/openapi.yaml` é a fonte normativa HTTP. O arquivo
`econexao-app/src/api/generated/openapi.ts` é gerado e não deve ser editado à
mão. `src/api/types.ts` contém apenas aliases estáveis para os schemas gerados.

```powershell
cd econexao-app
npm run openapi:generate
npm run openapi:check
npm run typecheck
```

O workflow `frontend-contract.yml` executa o check de drift, typecheck e testes
quando o OpenAPI, o backend ou o aplicativo forem alterados. O workflow de
backend também executa o teste offline que compara paths e parâmetros FastAPI
com o contrato canônico.

### Cache de dados do servidor

O aplicativo usa TanStack Query por meio de `ServerStateProvider`. As query
keys incluem todos os identificadores e filtros que mudam o resultado; listas
salvas também incluem a identidade. Ao adicionar mutations, use esta matriz:

- troca de região: ativa outra chave, sem limpar o cache territorial anterior;
- favorito de rota: invalida listas de rotas e o detalhe afetado;
- favorito de ator: invalida listas de atores e o detalhe afetado;
- logout/troca de usuário: remove todas as queries marcadas como autenticadas.

Não persista esse cache em AsyncStorage/SecureStore sem uma task e análise de
privacidade próprias.

O `AppContext` não aceita dados de servidor. Seu contrato atual contém apenas
o ID da região ativa e preferências globais de acessibilidade. O teste
`runtimeArchitecture.test.ts` bloqueia a reintrodução de `mockData.ts` no
runtime; fixtures continuam permitidas exclusivamente em testes e stories.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

O liveness responde em `/api/v1/health/live` e a documentação interativa em
`/docs`. O readiness ainda não comprova dependências externas enquanto a
integração Supabase não estiver concluída.

Verificação sanitizada de baseline local (ECO-1301):

```powershell
cd backend
python -m pytest tests/test_check_environment.py
python -m pytest --cov=app --cov-report=term --cov-fail-under=85
python -m ruff check app tests
python -m mypy app
python -m scripts.check_environment
```

### Runtime e Deploy no Render (Nativo Python sem Docker — ADR 0005)

O backend é executado como Web Service nativo Python no Render, sem dependência de Docker.

- **Blueprint declarativo:** [`render.yaml`](../render.yaml) na raiz do repositório.
- **Root Directory:** `backend`
- **Build Command:** `pip install .`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check:** `/api/v1/health` (e `/api/v1/health/live`)
- **Graceful Shutdown:** Gerenciado nativamente via `lifespan` com descarte de conexões do pool PostgreSQL.
- **Variáveis de ambiente:** Configuradas com `sync: false` no blueprint e injetadas de forma criptografada no Dashboard do Render (sem expor segredos no repositório).

## Supabase remoto sem Docker

Ambientes obrigatoriamente separados:

| Ambiente | Dados | Uso por IA |
|---|---|---|
| development | descartáveis/controlados | permitido |
| test | fixtures e limpeza automatizada | permitido |
| staging | Pindobal homologada | leitura e deploy aprovado |
| production | usuários reais | proibido sem autorização explícita |

Antes de usar a CLI:

```powershell
npx --yes supabase@2.113.0 --version
npx --yes supabase@2.113.0 --help
npx --yes supabase@2.113.0 migration --help
npx --yes supabase@2.113.0 db --help
```

A versão 2.113.0 foi verificada na ECO-0103. Não troque a versão sem revisar
o changelog e os comandos. O fluxo remoto definitivo permanece pendente de um
projeto Supabase `test` descartável.

Para o ambiente de test, copie `backend/.env.test.example` para
`backend/.env.test` e preencha somente com credenciais do projeto `test`:

```powershell
Copy-Item backend/.env.test.example backend/.env.test
```

Valide antes de qualquer comando remoto. O gate confere separação e também se o
project ref gerenciado da URL coincide com o tenant/host do `DATABASE_URL`; nomes
humanos ou URLs apenas plausíveis falham fechado:

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.check_test_isolation
```

Após migrations de Storage em test, execute a matriz funcional sanitizada. Ela
cria duas sessões anônimas e um objeto WebP descartável, testa owner/cross-user,
upsert, leitura pública, listagem e exclusão, e remove o objeto ao final:

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.verify_storage_policies
```

Para verificar RBAC editorial, revogação, isolamento de papéis e imutabilidade do
audit trail em Supabase test, use a transação com rollback:

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.verify_editorial_rbac
```

Para verificar o arquivamento reversível de vínculos usado pela reconciliação
editorial, incluindo a constraint de metadados e a restauração da identidade do
vínculo, execute no mesmo ambiente isolado (todas as escritas sofrem rollback):

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.verify_editorial_workflow
```

Para verificar as camadas espaciais estáticas da ECO-2306 no Supabase `test`,
incluindo corredor, isolamento regional, prioridade, categorias incompatíveis e
índices, execute a matriz transacional (todas as fixtures sofrem rollback):

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.check_test_isolation
.\.venv\Scripts\python.exe -m scripts.verify_actor_region_layers --env-file .env.test
```

## Variáveis de ambiente

Copie `econexao-app/.env.example` para `econexao-app/.env.local` e
`backend/.env.example` para `backend/.env`. Os arquivos locais são ignorados
pelo Git e nunca devem ser enviados por chat, commit ou log.

Frontend, públicas:

```env
EXPO_PUBLIC_API_URL=
EXPO_PUBLIC_SUPABASE_URL=
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

Backend, secretas:

```env
APP_ENV=development
DATABASE_URL=
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_JWKS_URL=
GOOGLE_PLACES_API_KEY=
ROUTING_PROVIDER=fake_deterministic
ENABLE_DYNAMIC_ROUTING=false
GOOGLE_ROUTES_API_KEY=
SENTRY_DSN=
```

`SUPABASE_SECRET_KEY`, service role, `DATABASE_URL` e chaves Google nunca usam prefixo `EXPO_PUBLIC_`.

Use uma credencial diferente em cada ambiente. No Supabase atual, prefira
`sb_publishable_...` no Expo e, somente quando uma operação administrativa
realmente precisar, uma chave `sb_secret_...` exclusiva no backend. A chave
secreta ignora RLS e não deve ser usada como Bearer token do usuário.

Para configurar sem imprimir os valores no terminal:

```powershell
Copy-Item econexao-app/.env.example econexao-app/.env.local
Copy-Item backend/.env.example backend/.env
```

Abra os dois arquivos localmente no editor. Não use comandos como `echo` para
exibir chaves e não coloque credenciais de production na máquina de
desenvolvimento.

## Migrations

- Fonte única: `supabase/migrations/*.sql`.
- Não usar Alembic.
- Não alterar schema apenas pelo Dashboard.
- Antes de promover: revisar SQL, executar testes RLS, rodar advisors, aplicar em development e staging, executar smoke tests.
- Não criar objetos customizados nos schemas `auth`, `storage` ou `realtime`.
- Grants e RLS são explícitos e testados separadamente.

## CI/CD de Staging e Migration Gate (GitHub Actions)

O pipeline `.github/workflows/staging-deploy.yml` executa a validação contínua e o deploy automático em Staging:

1. **Backend Quality Gate**: Ruff, Mypy, validação de migrations, testes de segurança de RLS e cobertura pytest (mínimo 85%).
2. **Frontend Quality Gate**: Sincronização OpenAPI, Typecheck TypeScript e suíte Jest.
3. **Migration & Secret Gate**: Varredura anti-vazamento de segredos e verificação de ordem de migrations.
4. **Deploy Staging (Render)**: Disparo do Deploy Hook autenticado e execução de smoke test (`scripts.staging_smoke`) contra os endpoints `/api/v1/health/live` e `/api/v1/health/ready`.

### Secrets requeridos no GitHub Repository / Environment `staging`:
- `RENDER_STAGING_DEPLOY_HOOK_URL`: URL do Deploy Hook do Web Service no Render.
- `STAGING_API_BASE_URL`: URL base pública do serviço em staging (ex: `https://api-staging.econexao.org`).

## Dados Pindobal

- Fonte externa: `C:\Users\Bruno\Downloads\teste-rota`.
- A pasta é somente leitura.
- O contrato está em `docs/data/pindobal_data_contract.md`.
- O comando de importação deve oferecer `--dry-run`, ser idempotente e gerar relatório.
- O backend nunca lê esses CSVs durante uma request de produção.

Validação sem banco:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.ingestion.seed_pindobal --snapshot-dir "C:\Users\Bruno\Downloads\teste-rota"
```

Aplicação é permitida somente com arquivo de ambiente test explícito:

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.check_test_isolation
.\.venv\Scripts\python.exe -m scripts.verify_pindobal_transaction
.\.venv\Scripts\python.exe -m app.ingestion.seed_pindobal --apply --env-file .env.test --snapshot-dir "C:\Users\Bruno\Downloads\teste-rota"
.\.venv\Scripts\python.exe -m scripts.verify_pindobal_apply
```

A ECO-1502 implementa upsert por chaves confiáveis e preserva timestamps de conteúdo
inalterado. A prova de duas execuções no Supabase test continua obrigatória antes de
promover a task: confirme a autorização para enviar o snapshot, rode os comandos de
isolamento e verificação e nunca use staging/production para essa prova.

## Conectores

O provider real aprovado para previews dinâmicos é `google_routes`. A flag
`ENABLE_DYNAMIC_ROUTING` permanece `false` por padrão; `fake_deterministic` é
permitido somente em development/test. OSRM runtime foi revogado pelo ADR 0013;
as geometrias OSRM importadas continuam válidas como snapshots oficiais.

O conector Google usa `ComputeRoutes Essentials`, POST, field mask mínima,
timeout/retries limitados, circuit breaker e guardas de 10 previews/minuto,
alerta em 7.500 e bloqueio em 9.000 chamadas mensais. Respostas não são cacheadas
até homologação jurídica específica. Consulte `docs/deployment_google_routes.md`.

O `GooglePlacesClient` usa exclusivamente Places API (New), field masks
allowlisted, timeout, retries limitados e orçamento de chamadas por job. Seus
testes também usam `httpx.MockTransport`; chaves Google nunca são carregadas
por testes ou pelo Expo.

## Testes

Leia `docs/testing_strategy.md`. Até os scripts existirem, registre claramente verificações indisponíveis; não simule resultados.

## Execução de uma task

1. Escolha uma task desbloqueada.
2. Leia dependências e referências.
3. Produza o mini-brief do playbook.
4. Faça uma alteração pequena e vertical.
5. Verifique com testes proporcionais ao risco.
6. Atualize docs/checklist.
7. Entregue evidências e pendências.
