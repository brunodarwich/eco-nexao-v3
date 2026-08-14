# Runbook: Resposta a Incidentes, Diagnóstico e Rollback

Este documento estabelece o protocolo operacional de triagem, diagnóstico e resolução de incidentes nos ambientes de Staging e Produção do backend e frontend ECOnexão.

---

## 1. Níveis de Severidade

| Nível | Descrição | Tempo de Resposta | Ações Imediatas |
|---|---|---|---|
| **SEV-1 (Crítico)** | API indisponível (500/503 generalizado), falha total de autenticação ou violação de segurança/dados. | < 15 minutos | Acionar equipe, executar rollback imediato se pós-deploy, isolar serviços afetados. |
| **SEV-2 (Alto)** | Degradação de rota específica, falha no conector Google Places, lentidão severa ou picos de 429. | < 1 hora | Inspecionar logs sanitizados, ajustar rate limits ou habilitar circuit breakers. |
| **SEV-3 (Médio/Baixo)** | Inconsistência cosmética, erro esporádico em endpoint não crítico. | Próximo ciclo ágil | Abrir issue no backlog, priorizar no Marco correspondente. |

---

## 2. Diagnóstico de Saúde e Liveness

### 2.1. Endpoints de Verificação
- **Liveness Probe**: `GET /api/v1/health/live` (Retorna 200 `{ "status": "ok" }`).
- **Readiness Probe**: `GET /api/v1/health/ready` (Verifica conectividade PostgreSQL/PostGIS e Supabase Auth).
- **Global Health**: `GET /api/v1/health` (Exibe status de todos os subsistemas).

### 2.2. Execução de Smoke Probe Local/Remoto
```powershell
python -m backend.scripts.staging_smoke --base-url https://staging.econexao.app
```

---

## 3. Análise de Logs Estruturados e Redação de Segredos

- Todos os logs do FastAPI são emitidos em formato JSON no `stdout`.
- Cada requisição possui um `request_id` (`X-Request-ID: req_...`) rastreável de ponta a ponta.
- **Redação Automática Ativa**:
  - DSNs de banco de dados (`postgres://...:***@...`).
  - Bearer tokens e JWTs (`eyJ***.***.***`).
  - Chaves de API Google (`AIza***`) e Supabase Service Keys (`sb_secret_***`).
  - Campos de senha em payloads JSON (`password: ***`).

---

## 4. Procedimento de Rollback no Render (FastAPI)

1. Acessar o Dashboard do Render na aba do serviço `econexao-backend`.
2. Navegar até a aba **Deploys**.
3. Localizar o último deploy estável e selecionar **Rollback to this deploy**.
4. Confirmar que o healthcheck `/api/v1/health/ready` retornou `status: 200`.
5. Notificar a equipe e registrar a ocorrência no log de incidentes.

---

## 5. Procedimento de Mitigação de Ataques ou Abuso de Tráfego

- O middleware de Rate Limiting bloqueia IPs ou tokens que excedam o limite configurado (padrão: 120 req/min).
- Resposta padrão: `HTTP 429 Too Many Requests` com cabeçalho `Retry-After: <segundos>`.
- Caso seja necessário bloquear um IP abusivo na borda, aplicar regras no WAF / DNS Cloudflare/Render.
