# Auditoria 24h – Estrutura Geral

## Branch atual
- `staging`

## Git status (resumo)
```
 M docs/README.md
 M docs/finalization/artifacts/e2e_web_and_a11y_report.md
 M econexao-app/app/_layout.tsx
 M econexao-app/app/route/[routeId]/map.tsx
 M econexao-app/package-lock.json
 M econexao-app/package.json
 M econexao-app/src/components/admin/WorkflowReviewQueue.tsx
 M econexao-app/src/components/common/AppHeader.tsx
 M econexao-app/src/components/common/ErrorBoundary.tsx
 M econexao-app/src/components/common/RegionSelectorModal.tsx
 M econexao-app/src/components/map/MapAdapter.helpers.test.ts
 M econexao-app/src/components/map/MapAdapter.helpers.ts
 M econexao-app/src/components/map/MapAdapter.native.tsx
 M econexao-app/src/components/map/MapAdapter.types.ts
 M econexao-app/src/components/map/MapAdapter.web.tsx
 M econexao-app/src/components/profile/AccountDeletionModal.tsx
 M econexao-app/src/components/profile/AuthModal.tsx
 M econexao-app/src/components/profile/EditProfileModal.tsx
 M econexao-app/src/components/routes/OriginSelector.tsx
 M econexao-app/e2e/accessibilityAudit.e2e.test.tsx
 M econexao-app/tsconfig.json
?? docs/repository_health/
?? econexao-app/e2e/
?? econexao-app/playwright-report/
?? econexao-app/playwright.config.ts
?? econexao-app/screenshots/
?? econexao-app/scripts/serve-dist.mjs
?? econexao-app/src/components/common/AccessibleModal.native.tsx
?? econexao-app/src/components/common/AccessibleModal.tsx
?? econexao-app/src/components/common/AccessibleModal.web.tsx
?? econexao-app/src/utils/focusManager.dom.test.tsx
?? econexao-app/src/utils/focusManager.test.tsx
?? econexao-app/src/utils/focusManager.ts
?? econexao-app/test-results/
?? package-lock.json
``` 

## Principais diretórios
- `docs/` – documentação e especificações do projeto.
- `backend/` – API FastAPI (Python) e código do domínio.
- `econexao-app/` – frontend Expo (React Native) e código da aplicação móvel/web.
- `supabase/` – migrações e configuração do banco Supabase/PostGIS.
- `landing-page/` – página estática de apresentação.
- `docker-compose.osrm.yml` – configuração do roteamento OSRM.
- `vercel.json` / `render.yaml` – arquivos de deploy.

## Frontend
- Tecnologias: **Expo SDK 54**, React Native, TypeScript.
- Estrutura típica de app Expo (`app/`, `src/`, `e2e/`).
- Integrações: chamadas ao backend FastAPI, Supabase Auth/Storage, Google Places/GBP via backend.

## Backend
- **FastAPI** (Python) – pontos de entrada da API de domínio.
- Organização: `app/` (rotas, serviços), `tests/`, `scripts/`.
- Configuração via arquivos `.env*`.

## Banco de Dados
- **Supabase** (PostgreSQL 17 + PostGIS).
- Migrações em `supabase/migrations/` (única fonte de verdade).
- Controle de acesso via RLS e policies.

## Deploy
- Vercel (`vercel.json`) para o frontend.
- Render (`render.yaml`) para backend (?)
- Docker Compose para OSRM (`docker‑compose.osrm.yml`).
- Possíveis pipelines CI definidas em `DEVELOPMENT.md`.

## Integrações externas
- **Google Places / Google Business Profile** – chamadas feitas pelo backend.
- **OSRM** – serviço de roteamento hospedado via Docker.
- **Supabase** – Auth, Storage, Data API.

## Documentos que definem o estado atual
- `AGENTS.md` – regras e diretrizes de desenvolvimento.
- `README.md` (raiz) e `docs/README.md` – visão geral.
- `docs/backend_integration_spec.md` – especificação da integração backend.
- `docs/backend_integration_tasks.md` – lista de tarefas.
- `docs/ai_task_playbook.md` – protocolo de execução.
- `openapi.yaml` – contrato API OpenAPI.
- `docs/acceptance_criteria.md` – critérios de aceitação.
- `docs/deployment_google_routes.md` & `docs/deployment_osrm.md` – detalhes de deployments externos.
- `supabase/migrations/` – esquema de banco.

## Próximos passos (arquivos a analisar)
- **Especificação de integração**: `docs/backend_integration_spec.md`
- **Contrato OpenAPI**: `openapi.yaml`
- **Migrações do banco**: `supabase/migrations/`
- **Código do backend**: `backend/app/` e `backend/tests/`
- **Código do frontend**: `econexao-app/` (especialmente `src/` e `e2e/`)
- **Arquivos de deploy**: `vercel.json`, `render.yaml`, `docker-compose.osrm.yml`
- **Diretrizes adicionais**: `AGENTS.md`, `docs/ai_task_playbook.md`

> **Nota**: Esta auditoria ainda é superficial – foco apenas em mapear a estrutura do projeto. Análises detalhadas (lógica de negócios, políticas RLS, cobertura de testes, etc.) virão nos próximos passos.
