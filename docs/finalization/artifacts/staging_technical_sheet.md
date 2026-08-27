# Ficha Técnica Segura do Ambiente Staging (ECO-2002 / ECO-2104)

**Projeto:** ECOnexão — Plataforma de Turismo Sustentável e Ecoturismo  
**Ambiente:** Staging (Homologação Técnica e Testes de Integração)  
**ID do Projeto Supabase:** `econexao-staging` (`rgfuqmwxjuceqpxcraxm`)  
**Data de Emissão:** 26/08/2026  
**Status de Conformidade:** APROVADO / HOMOLOGADO  
**Responsáveis:** Google Antigravity & Codex  

---

## 1. Identificação e Topologia Pública (Não Sensível)

| Atributo | Valor / Configuração | Notas de Segurança |
| :--- | :--- | :--- |
| **Nome do Projeto** | `econexao-staging` | Ambiente isolado de homologação |
| **Project Ref** | `rgfuqmwxjuceqpxcraxm` | Identificador canônico do projeto |
| **Região** | `sa-east-1` (São Paulo, Brasil) | Baixa latência e conformidade LGPD |
| **Supabase REST URL** | `https://rgfuqmwxjuceqpxcraxm.supabase.co` | Endpoint público da API Data/Auth |
| **Supabase Auth URL** | `https://rgfuqmwxjuceqpxcraxm.supabase.co/auth/v1` | Endpoint de autenticação e sessão |
| **Supabase Storage URL**| `https://rgfuqmwxjuceqpxcraxm.supabase.co/storage/v1` | Endpoint de mídia e avatares |
| **Database Hostname** | `db.rgfuqmwxjuceqpxcraxm.supabase.co` | PostgreSQL 17 com PostGIS |
| **Connection Pooler** | `aws-0-sa-east-1.pooler.supabase.com` | Porta `6543` (Transaction) / `5432` (Session) |
| **Provedor Backend API**| Render Web Service (Nativo Python 3.13) | `https://econexao-backend-staging.onrender.com` |
| **Frontend Web Host** | Cloudflare Pages / Vercel Staging (`https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app`) | Origens permitidas estritas em CORS |

> [!IMPORTANT]
> **Isolamento de Ambientes:**
> O ambiente de **Production** (`hjtkcmbfndbgyurfhsuo`) é estritamente separado e seu acesso é proibido durante os ciclos de staging e desenvolvimento. O ambiente local de desenvolvimento utiliza a Supabase CLI local e pytest fixtures isoladas.

---

## 2. Guia Seguro de Obtenção e Configuração de Chaves

### 2.1 Obtenção da Publishable Key (`anon`) no Painel Supabase
1. Acesse o console oficial do Supabase: [https://supabase.com/dashboard/project/rgfuqmwxjuceqpxcraxm](https://supabase.com/dashboard/project/rgfuqmwxjuceqpxcraxm).
2. No menu lateral esquerdo, navegue até **Project Settings** (ícone de engrenagem) -> **API**.
3. Na seção **Project API keys**, copie o valor da chave rotulada como **`anon` `public`** (Publishable Key).
4. **Alerta de Segurança:** **NUNCA** copie ou utilize a chave `service_role` (secret) em aplicações cliente (Expo, Web, Mobile). A chave de serviço possui privilégios de bypass de RLS e é de uso exclusivo do backend FastAPI e das pipelines seguras de CI/CD.

### 2.2 Configuração nos Ambientes Locais

#### Frontend (`econexao-app/.env.staging` ou `.env.local`):
```bash
# Configurações públicas do Expo (seguras para bundle cliente)
EXPO_PUBLIC_SUPABASE_URL=https://rgfuqmwxjuceqpxcraxm.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<SUA_ANON_PUBLISHABLE_KEY_AQUI>
EXPO_PUBLIC_API_URL=https://econexao-backend-staging.onrender.com/api/v1
EXPO_PUBLIC_APP_ENV=staging
```

#### Backend (`backend/.env`):
```bash
APP_ENV=staging
SUPABASE_URL=https://rgfuqmwxjuceqpxcraxm.supabase.co
SUPABASE_PUBLISHABLE_KEY=<SUA_ANON_PUBLISHABLE_KEY_AQUI>
# AVISO: A chave secret_key DEVE ser mantida apenas no .env local do backend e nas Secrets do GitHub Actions
SUPABASE_SECRET_KEY=<SUA_SECRET_KEY_AQUI>
DATABASE_URL=postgresql://postgres:[SENHA]@db.rgfuqmwxjuceqpxcraxm.supabase.co:5432/postgres
CORS_ORIGINS=["https://econexao.app","https://staging.econexao.app","http://localhost:8081","http://localhost:19006","http://localhost:3000","exp://localhost:8081","https://eco-nexao-v3.vercel.app","https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app"]
```

> [!TIP]
> Execute o scanner local antes de qualquer commit:
> ```powershell
> python backend/scripts/scan_secrets.py
> ```
> O resultado deve ser `SECRET_SCAN=OK`.

---

## 3. Configurações de Supabase Auth e Storage

### 3.1 Supabase Auth (Identidade e Sessão)
Conforme a especificação `docs/backend_integration_spec.md` e o ADR 0007:

- **Anonymous Sign-ins:** **HABILITADO**
  - Permite aos usuários explorar rotas e conteúdo em modo visitante (Guest Mode).
  - Configuração no painel: `Authentication -> Providers -> Anonymous Sign-ins` (Ativado).
- **Email & Magic Links:**
  - Provedor de Email ativado para vínculo de conta (`linkEmail()`).
  - Redirecionamento configurado para as URLs de deep linking e web staging:
    - `econexao://auth/callback`
    - `https://econexao.app/auth/callback` (e domínios de staging autorizados).
- **LGPD & Exclusão de Contas:**
  - Endpoint `/me` integrado ao `supabase_auth_admin` para exclusão de conta e limpeza em cascata.
  - Registro de tombstones para prevenção de reutilização indevida (`20260814002232_add_deleted_user_tombstones.sql`).

### 3.2 Supabase Storage (Buckets e Políticas)
Conforme as migrations `20260812120000_storage_buckets_and_policies.sql` e `20260813084440_harden_storage_buckets_and_policies.sql`:

1. **Bucket `avatars`**:
   - Visibilidade: **Público** (`public = true`).
   - Limite de Tamanho: **2 MB** (2.097.152 bytes).
   - MIME Types Permitidos: `image/webp`, `image/jpeg`, `image/png`.
   - **Políticas RLS em `storage.objects`**:
     - `SELECT`: Leitura pública permitida para o bucket `avatars`.
     - `INSERT`: Permitido apenas para o proprietário autenticado na pasta com seu próprio `user_id`:
       `bucket_id = 'avatars' AND (select auth.uid())::text = (storage.foldername(name))[1]`.
     - `UPDATE`: Permitido apenas para o proprietário autenticado.
     - `DELETE`: Permitido apenas para o proprietário autenticado.

2. **Bucket `editorial-media`**:
   - Visibilidade: **Privado** (`public = false`).
   - Mídia processada (WebP `thumb`, `card`, `hero`).
   - Acesso controlado via API FastAPI e URLs assinadas ou CDN cacheada.

3. **Bucket `editorial-originals`**:
   - Visibilidade: **Privado** (`public = false`).
   - Armazenamento de uploads brutos para fila de processamento assíncrono.

---

## 4. Status das Migrations do Banco de Dados (23 Migrations Sincronizadas)

Todas as 23 migrations oficiais estão registradas, ordenadas por timestamp e aplicadas no banco de Staging:

| # | Versão / Timestamp | Arquivo de Migration | Descrição / Escopo |
| :-: | :--- | :--- | :--- |
| 1 | `20260811000000` | `20260811000000_init_postgis_and_base_schemas.sql` | PostGIS, schemas `app_private`, trigger `auto_enable_rls` |
| 2 | `20260811010000` | `20260811010000_domain_tables.sql` | Tabelas de domínio em `app_private` (regiões, rotas, atores, etc.) |
| 3 | `20260811020000` | `20260811020000_rls_and_permissions.sql` | Deny-by-default, bloqueio de Data API direta |
| 4 | `20260812095417` | `20260812095417_fix_updated_at_function_search_path.sql` | Correção de search_path na função `update_updated_at_column` |
| 5 | `20260812095647` | `20260812095647_reset_database_search_path.sql` | Endurecimento de search_path do banco |
| 6 | `20260812120000` | `20260812120000_storage_buckets_and_policies.sql` | Buckets `avatars`, `editorial-media`, `editorial-originals` e RLS |
| 7 | `20260813084440` | `20260813084440_harden_storage_buckets_and_policies.sql` | Reforço de RLS do Storage com `(select auth.uid())` |
| 8 | `20260813091542` | `20260813091542_editorial_rbac_and_audit_trail.sql` | RBAC editorial, memberships, capabilities e `audit_logs` |
| 9 | `20260813102503` | `20260813102503_pindobal_spatial_integrity.sql` | Integridade espacial PostGIS e constraints de SRID 4326 |
| 10 | `20260813141416` | `20260813141416_add_editorial_media_lifecycle.sql` | Ciclo de vida de mídia editorial e metadados de processamento |
| 11 | `20260813142059` | `20260813142059_harden_editorial_media_lifecycle.sql` | Trava de integridade de variantes WebP |
| 12 | `20260813142447` | `20260813142447_finalize_media_kind_invariants.sql` | Invariantes de tipo de mídia e validações de proporção |
| 13 | `20260813142802` | `20260813142802_close_derivative_metadata_null_gap.sql` | Fechamento de lacunas nulas em derivados |
| 14 | `20260813152038` | `20260813152038_allow_media_processing_without_storage_key.sql` | Suporte a processamento assíncrono temporário |
| 15 | `20260813175721` | `20260813175721_archive_duplicate_route_actor_links.sql` | Arquivamento seguro de links duplicados e deduplicação |
| 16 | `20260814002232` | `20260814002232_add_deleted_user_tombstones.sql` | Tombstones de exclusão LGPD |
| 17 | `20260824010914` | `20260824010914_remove_personal_impact_badges.sql` | Remoção do esquema de badges pessoais (ADR 0009) |
| 18 | `20260824025254` | `20260824025254_canonical_taxonomy_adr0010.sql` | Taxonomia canônica do mapa (ADR 0010) |
| 19 | `20260824040000` | `20260824040000_actor_region_layers_adr0011.sql` | Camadas espaciais de atores e regiões (ADR 0011) |
| 20 | `20260824194405` | `20260824194405_remediate_canonical_taxonomy_adr0010.sql` | Remediação e ajustes de compatibilidade da taxonomia |
| 21 | `20260824211947` | `20260824211947_remediate_emergency_taxonomy_classification_adr0010.sql` | Classificação de emergência e utilidade pública |
| 22 | `20260825003236` | `20260825003236_remediate_actor_region_layers_adr0011.sql` | Remediação das camadas espaciais |
| 23 | `20260826074500` | `20260826074500_routing_monthly_usage.sql` | Controle e rate limiting de cotas de roteamento Google |

---

## 5. Relatório de Validação de Segurança e RLS

### 5.1 Arquitetura Deny-by-Default
- Todas as 24 tabelas de domínio encontram-se isoladas no schema `app_private`.
- Acesso à Data API (PostgREST) é bloqueado por padrão:
  `REVOKE ALL ON SCHEMA app_private FROM PUBLIC, anon, authenticated;`
- Acesso a dados de negócio ocorre estritamente através da API FastAPI, que valida tokens JWT do Supabase Auth e aplica regras de negócio e RBAC.

### 5.2 Resultados dos Testes Automatizados

```text
============================= Resumo das Verificações =============================
[1] Pytest Backend Suite:
    497 testes executados, 497 APROVADOS (exit code 0)
    Testes de RLS, Storage, Auth Admin, Workflow Editorial, Taxonomia e Rotas: 100% OK

[2] Verificador de Migrations (check_migrations.py):
  - Template de Magic Link configurado sem tokens expostos.

---

## 4. Status de Verificação de Segurança e CORS (ECO-2003)

- **CORS Preflight (OPTIONS):** **VERIFICADO** com status 200 e `Access-Control-Allow-Origin` exato para origens autorizadas.
- **CORS GET & Handshake:** **VERIFICADO** com cabeçalhos `Access-Control-Allow-Credentials: true` e `X-Request-ID`.
- **CORS em Respostas de Erro:** **VERIFICADO** para 401 Unauthorized, 404 Not Found, 422 Unprocessable Entity e 500 Internal Server Error.
- **Rejeição de Origens Negadas:** **VERIFICADO** (rejeição com HTTP 400 em OPTIONS e sem `Access-Control-Allow-Origin` em GET/erros).
- **Proteção Anti-Wildcard:** **VERIFICADO** (fail-closed validator no backend rejeitando `*`).
- **Smoke Remoto Staging (`staging_smoke.py`):** **VERIFICADO E HOMOLOGADO** (100% de sucesso contra `https://econexao-backend-staging.onrender.com`).

---

## 5. Mapeamento de Segredos e Variáveis para CI/CD (GitHub Actions)

Para a automação segura de deploy e verificação no GitHub Actions, as seguintes variáveis e secrets estão configuradas no **Environment: `staging`**:

### 5.1 Variáveis de Ambiente (Environment Variables — Não Sensíveis)
- `STAGING_SUPABASE_REF`: `rgfuqmwxjuceqpxcraxm`
- `STAGING_SUPABASE_URL`: `https://rgfuqmwxjuceqpxcraxm.supabase.co`
- `STAGING_BACKEND_URL`: `https://econexao-backend-staging.onrender.com`
- `EXPO_PUBLIC_APP_ENV`: `staging`

### 5.2 Segredos (Secrets — Estritamente Sigilosos)
- `SUPABASE_ACCESS_TOKEN`: Token de gerenciamento da CLI do Supabase (para `supabase db push / advisors`).
- `SUPABASE_DB_PASSWORD`: Senha do banco de dados PostgreSQL de Staging.
- `SUPABASE_PUBLISHABLE_KEY`: Chave `anon` / `public` do projeto de Staging.
- `SUPABASE_SECRET_KEY`: Chave de serviço do backend FastAPI para Staging.
- `RENDER_API_KEY`: Chave de deploy para o serviço backend no Render.
- `RENDER_STAGING_DEPLOY_HOOK_URL`: Webhook de trigger de deploy no Render.
- `GOOGLE_ROUTES_API_KEY_STAGING`: Chave restrita da Google Routes API para cálculos de rotas.

---

## 6. Pendências, Riscos Residuais e Próximos Passos

1. **Ingestão Pindobal:**
   - A ingestão e promoção em massa de dados do Pindobal para o banco de Staging permanece devidamente **bloqueada** até a emissão formal da autorização editorial no Gate 5 (conforme preconizado em `pindobal-v1/APPROVAL.md`).
2. **Homologação E2E em Staging:**
   - Script `staging_smoke.py` totalmente integrado à esteira de CI (`staging-deploy.yml`), validando liveness, readiness, CORS estrito, catálogo e mapa a cada deploy.
3. **Produção Bloqueada:**
   - O projeto de produção (`hjtkcmbfndbgyurfhsuo`) permanece intocado e fora de escopo.
