# Runbook: Deploy de Produção, Verificação de CORS/TLS e Smoke Sintético (ECO-2203)

Este documento orienta a publicação controlada da API FastAPI (Render) e do Frontend Web (Expo Web / CDN), além de estabelecer as validações contratuais de segurança, domínio e deep links.

---

## 1. Topologia de Infraestrutura

- **Backend:** Render Web Service (Native Python 3.13, sem Docker, plano starter ou superior).
- **Frontend Web:** Expo Web exportado estaticamente para CDN/Hosting com suporte a HTTPS e rewrite SPA.
- **Banco de Dados:** Supabase PostgreSQL 17 gerenciado com extensão PostGIS ativa.
- **Autenticação & Storage:** Supabase Auth e Supabase Storage (buckets `public-media`, `curator-media`, `avatars`).

---

## 2. Parâmetros de Configuração e Blueprint Render

O arquivo [`render.yaml`](file:///c:/Users/Bruno/Downloads/eco-nexao-v3/render.yaml) é o modelo declarativo para provisionamento do backend.

### Variáveis Obrigatórias no Cofre Render:
| Variável | Descrição | Exemplo / Formato |
|---|---|---|
| `PYTHON_VERSION` | Versão do runtime Python | `3.13.0` |
| `APP_NAME` | Nome do serviço | `ECOnexão API` |
| `APP_ENV` | Ambiente | `production` ou `staging` |
| `LOG_LEVEL` | Nível de log estruturado | `INFO` |
| `SUPABASE_URL` | Endpoint da API Supabase | `https://<ID>.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | Publishable Anon Key | `eyJ...` |
| `SUPABASE_SECRET_KEY` | Secret Key restrita | `eyJ...` (somente no backend) |
| `SUPABASE_JWT_SECRET` | Segredo para validação de JWTs | Segredo alfanumérico |
| `DATABASE_URL` | DSN de conexão ao PostgreSQL | `postgresql://...` |
| `CORS_ORIGINS` | Lista JSON de origens permitidas | `["https://econexao.app","https://staging.econexao.app","http://localhost:8081","https://eco-nexao-v3.vercel.app","https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app"]` |

---

## 3. Verificações Pré-Deploy e Pós-Deploy

### 3.1. Validação de Deep Links e Universal Links
Garantir que a raiz pública ou CDN do domínio responda aos endpoints de associação de aplicativos móveis:
- **Android App Links:** `GET https://econexao.app/.well-known/assetlinks.json` (Content-Type: `application/json`)
- **iOS Universal Links:** `GET https://econexao.app/.well-known/apple-app-site-association` (Content-Type: `application/json`)

### 3.2. Validação de Cabeçalhos de Segurança (HTTPS/TLS)
Executar teste de cabeçalhos de resposta:
```bash
curl -I https://api.econexao.app/api/v1/health/live
```
**Critérios:**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: ...`

### 3.3. Teste de CORS
Executar preflight request (OPTIONS):
```bash
curl -I -X OPTIONS https://api.econexao.app/api/v1/actors \
  -H "Origin: https://econexao.app" \
  -H "Access-Control-Request-Method: GET"
```
**Critério:** Retornar `Access-Control-Allow-Origin: https://econexao.app` com status 200/204.

---

## 4. Suíte de Smoke Sintético Pós-Deploy

Executar verificação de saúde dos endpoints essenciais:
1. `GET /api/v1/health/live` -> 200 `{"status": "ok"}`
2. `GET /api/v1/health/ready` -> 200 `{"status": "ready", "database": "connected", "auth": "connected"}`
3. `GET /api/v1/actors?limit=5` -> 200 com lista de atores públicos retornados.
4. `GET /api/v1/routes` -> 200 com rotas disponíveis.

---

## 5. Procedimento Determinístico de Rollback e Redeploy da API

Se qualquer smoke test, probe de prontidão ou verificação de CORS falhar após um deploy:

### 5.1. Rollback via Git / CI/CD (Recomendado e Determinístico)
1. Identifique o último commit estável conhecido (ex: `06456398772af10a814b0d6cfbb6e927d70dde24`).
2. Execute o rollback da branch ou cherry-pick de reversão:
   ```powershell
   git revert --no-edit <COMMIT_COM_REGRESSAO>
   git push origin staging
   ```
3. O GitHub Actions executará a esteira completa e disparará o webhook de deploy do Render.
4. Execute o smoke test exigindo o commit de rollback:
   ```powershell
   python backend/scripts/staging_smoke.py --base-url "https://econexao-backend-staging.onrender.com" --expected-commit "<SHA_DO_ROLLBACK>"
   ```

### 5.2. Rollback via Render Dashboard / API
1. Acesse o serviço `econexao-backend-staging` no Render.
2. Na aba **Events / Deploys**, localize o deploy correspondente à revisão estável.
3. Clique em **Rollback to this deploy**.
4. O Render restaurará a imagem e o commit da revisão selecionada.
5. Valide a conclusão do rollback via CLI:
   ```powershell
   python backend/scripts/staging_smoke.py --base-url "https://econexao-backend-staging.onrender.com" --expected-commit "<SHA_DO_DEPLOY_RESTAURADO>"
   ```

### 5.3. Redeploy e Validação Final Pós-Correção
1. Após corrigir o defeito e comitar a nova revisão (ex: `76c826fe57b616af1a8c28469c9fda082ee7c9e4`), realize o push para `staging`.
2. Acompanhe o workflow no GitHub Actions (`Staging Deployment & Migration Gate`).
3. Execute o smoke test final:
   ```powershell
   python backend/scripts/staging_smoke.py --base-url "https://econexao-backend-staging.onrender.com" --expected-commit "76c826fe57b616af1a8c28469c9fda082ee7c9e4"
   ```
4. Confirme que o cabeçalho `X-Commit-SHA` e o payload `/health/live` apresentam o novo SHA.
