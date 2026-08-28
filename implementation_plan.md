# Auditoria 24h – Plano de Análise Detalhada

## Goal
Realizar uma auditoria rápida (≤ 24 h) para confirmar se o EcoNexão pode ser usado em testes iniciais. O foco será validar a estrutura, integrações e configuração de deploy, identificando bloqueios críticos.

## User Review Required
- **Escopo**: Este plano cobre apenas revisão de código, configuração e documentação listados abaixo. Não inclui testes de carga, análise de performance ou avaliação de UI detalhada.
- **Tempo estimado**: ~3 h de leitura/documentação + ~2 h de revisão de código + ~1 h de síntese de resultados (total ≤ 6 h).
- **Limitações**: Não vamos executar o backend nem iniciar o banco Supabase; assumimos que as migrações já foram aplicadas.

## Open Questions
> [!IMPORTANT]
> **1.** O backend está atualmente configurado para **Render** ou **Vercel**? Preciso saber qual serviço está ativo para validar variáveis de ambiente.
>
> > [!NOTE]
> > Se houver múltiplos ambientes, indique qual deve ser auditado.
>
> **2.** Existem credenciais locais para Supabase (`SUPABASE_URL`, `SUPABASE_ANON_KEY`) configuradas em `.env`? Se sim, elas podem ser usadas para checar conectividade.
>
> **3.** O projeto possui pipelines CI/CD (GitHub Actions, etc.)? Se houver, indique onde estão os arquivos de workflow.

## Proposed Changes
### 1. Documentação & Especificação
- **[MODIFY] docs/backend_integration_spec.md** – extrair sumário de fluxos críticos (auth, storage, Google Places, OSRM).
- **[MODIFY] openapi.yaml** – listar endpoints públicos, requisitos de JWT e scopes.
- **[MODIFY] docs/deployment_google_routes.md & docs/deployment_osrm.md** – validar URLs de serviços externos.

### 2. Banco de Dados
- **[MODIFY] supabase/migrations/** – listar migrações recentes, verificar presença de políticas RLS e `GRANT`.
- **[NEW] docs/auditoria-24h/02-banco.md** – resumo das tabelas principais, políticas de acesso.

### 3. Backend (FastAPI)
- **[MODIFY] backend/app/** – mapear routers, dependências de Supabase, uso de variáveis de ambiente.
- **[NEW] docs/auditoria-24h/03-backend.md** – checklist de pontos críticos (auth, validação, tratamento de erros).

### 4. Frontend (Expo)
- **[MODIFY] econexao-app/src/** – identificar chamadas ao serviço `api/` (hooks), uso de `expo-secure-store` para tokens.
- **[NEW] docs/auditoria-24h/04-frontend.md** – resumo de pacotes críticos, configuração de Supabase client, variáveis `EXPO_PUBLIC_*`.

### 5. Deploy & Infraestrutura
- **[MODIFY] vercel.json** – validar redirecionamentos, builds e rotas.
- **[MODIFY] render.yaml** – confirmar comando de start, dependências.
- **[MODIFY] docker-compose.osrm.yml** – garantir que o serviço OSRM está configurado como `depends_on`.
- **[NEW] docs/auditoria-24h/05-deploy.md** – checklist de variáveis de ambiente, estratégias de build.

### 6. Integrações Externas
- **[MODIFY] backend/app/services/google_* .py** – revisar chaves API (dev vs prod) e uso de `httpx`.
- **[NEW] docs/auditoria-24h/06-integracoes.md** – lista de endpoints externos, requisitos de credenciais.

## Verification Plan
### Automated Checks
- Run `git status` para garantir que não há mudanças inesperadas.
- Execute `python -m pip list` dentro do backend venv para confirmar dependências.
- Run `npm ls` in `econexao-app` to validate package tree.
- Validate OpenAPI schema with `speccy lint openapi.yaml` (if installed).

### Manual Verification
- Peça ao usuário para confirmar quais variáveis de ambiente de produção estão disponíveis.
- Revisar rapidamente logs de CI (se houver) para garantir builds bem‑sucedidos.
- Confirmar se o backend pode ser iniciado localmente (`uvicorn backend.app.main:app`).

---
*Este plano será salvo como `implementation_plan.md`. Após sua aprovação, prosseguirei com a auditoria detalhada.*
