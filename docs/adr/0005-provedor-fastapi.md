# ADR 0005: Provedor de Hospedagem e Runtime FastAPI (Render Native Python)

- **Status:** aceito
- **Data:** 12/08/2026 (Atualizado: 14/08/2026)
- **Autores:** Codex / Antigravity (IA assistida)
- **Decisor:** Proprietário do Produto (Owner)
- **Task relacionada:** ECO-1302

---

## 1. Contexto e Problema

O backend do projeto ECOnexão é desenvolvido em Python com **FastAPI** e atua como a única fronteira de domínio para acesso ao banco de dados Supabase PostgreSQL 17/PostGIS, Supabase Storage, serviços externos (Google Places/GBP, OSRM) e rotas de ingestão de dados.

Conforme a diretriz do projeto fixada em `AGENTS.md` e `DEVELOPMENT.md` (*"Docker não é pré-requisito"*), o proprietário do projeto optou expressamente por **não utilizar Docker** nem ferramentas de contêineres locais ou remotos. É necessário escolher e configurar um provedor de hospedagem gerenciado (PaaS) que execute o runtime Python nativamente a partir do repositório, com segurança, health checks e zero-downtime deploy.

---

## 2. Opções Comparadas

Foram avaliadas quatro alternativas de plataformas gerenciadas com suporte a runtime Python nativo / PaaS:

1. **Render** (Web Service Nativo Python gerenciado)
2. **Fly.io** (App micro-VMs)
3. **Railway** (Python Nixpacks/Buildpack)
4. **Google Cloud Run** (Container Serverless)

---

## 3. Matriz Comparativa Detalhada

| Critério | Render (Nativo Python) | Fly.io | Railway | Google Cloud Run |
|---|---|---|---|---|
| **Dependência de Docker** | **NENHUMA (Deploy nativo via `pyproject.toml`/`pip`)** | Opcional via buildpack | Opcional via Nixpack | Obrigatório (Exige OCI Image) |
| **Região e Egress Supabase** | `us-east-1` / `sa-east-1` (São Paulo); baixa latência | `gru` (São Paulo) / `iad` | `us-east-1` / europe | `southamerica-east1` (São Paulo) |
| **Modelo de Custo** | Fixo por instância/mês (a partir de \$7/mês) + egress | Por uso (CPU/RAM/segundo) + egress | Por uso (RAM/vCPU por hora) + egress | Serverless puro por requisição |
| **Health & Readiness Checks** | HTTP Health Check nativo configurável (`/api/v1/health`) | Health checks HTTP/TCP em `fly.toml` | Healthcheck HTTP nativo | Startup/Liveness probes |
| **Background Jobs / Workers** | Background Workers nativos Python (\$7/mês) | Process groups na mesma app | Services dedicados | Cloud Run Jobs |
| **Gestão de Segredos** | Environment Variables & Secret Files nativos no Dashboard | Encrypted Secrets via CLI | Variables compartilhadas | Google Secret Manager |
| **Logs & Observabilidade** | Logs nativos em tempo real no Dashboard Render | Logs agregados (`fly logs`) | Log tail nativo | Cloud Logging |
| **Domínio TLS & Custom Domain** | SSL automático (Let's Encrypt) e gerenciamento de DNS | SSL automático | SSL automático | SSL gerenciado |
| **Deploy & Rollback** | Zero-downtime deploys automáticos via Git push + rollback 1-clique | Deploys via CLI + rollback | Rollback por commit/digest | Revisioning imutável |
| **SLA e Alta Disponibilidade** | 99,9% uptime garantido em planos pagos | SLA global | SLA 99,9% em planos Pro | SLA 99,95% |

---

## 4. Análise e Recomendação Técnica

### Opção Escolhida: **Render** (Web Service Nativo Python — Sem Docker)

#### Raciocínio Técnico & Operacional:
1. **Zero Dependência de Docker:** O deploy é realizado diretamente a partir do repositório Git. O Render detecta o `pyproject.toml`, executa a instalação das dependências via `pip` e inicia o servidor com o comando `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. **Simplicidade de Operação e Deploy Contínuo:** Cada push na branch autorizada aciona o build e deploy com zero-downtime de forma totalmente automatizada.
3. **Health Checks Nativos:** Suporte direto ao monitoramento de disponibilidade e integridade via `/api/v1/health`.
4. **Isolamento de Segredos e HTTPS Automático:** Variáveis de ambiente gerenciadas de forma criptografada via painel do Render, com certificados SSL/TLS provisionados e renovados automaticamente.

---

## 5. Decisão para Aprovação do Owner

Decisão formal registrada pelo proprietário:

- [ ] **Opção A:** Google Cloud Run.
- [x] **Opção B (Aprovada pelo Owner):** Render (Web Service Nativo Python sem Docker, SSL automático, zero-downtime deploys e health checks).
- [ ] **Opção C:** Fly.io.
- [ ] **Opção D:** Railway.

---

## 6. Consequências da Decisão

- A escolha do Render guiará a task **ECO-2001** (Configuração do runtime nativo Python, script de startup, healthcheck HTTP `/api/v1/health` e manifesto declarativo de serviço `render.yaml` opcional, **sem necessidade de Dockerfile**).
- As tasks do **Marco 20 (ECO-2001, ECO-2002 e ECO-2003)** implementarão a esteira e configuração direcionadas ao Render Web Service Nativo.
- Nenhum segredo ou credencial será versionado no Git; as chaves serão injetadas exclusivamente nas Environment Variables do serviço no Render.
