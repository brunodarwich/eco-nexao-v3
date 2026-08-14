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
| `SUPABASE_SERVICE_ROLE_KEY` | Service Role Key restrita | `eyJ...` (somente no backend) |
| `SUPABASE_JWT_SECRET` | Segredo para validação de JWTs | Segredo alfanumérico |
| `DATABASE_URL` | DSN de conexão ao PostgreSQL | `postgresql://...` |
| `CORS_ORIGINS` | Lista JSON de origens permitidas | `["https://econexao.app","https://staging.econexao.app"]` |

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

## 5. Procedimento de Rollback Imediato da API

Se qualquer probe de prontidão falhar ou a taxa de erro 5xx exceder 0.1%:
1. No dashboard do Render: Clicar no commit / deploy anterior e acionar **Rollback**.
2. Revalidar `/api/v1/health/ready` até normalização.
