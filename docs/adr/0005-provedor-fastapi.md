# ADR 0005: Provedor de Contêiner e Topologia FastAPI

- **Status:** aceito
- **Data:** 12/08/2026
- **Autores:** Codex / Antigravity (IA assistida)
- **Decisor:** Proprietário do Produto (Owner)
- **Task relacionada:** ECO-1302

---

## 1. Contexto e Problema

O backend do projeto ECOnexão é desenvolvido em Python com **FastAPI** e atua como a única fronteira de domínio para acesso ao banco de dados Supabase PostgreSQL 17/PostGIS, Supabase Storage, serviços externos (Google Places/GBP, OSRM) e rotas de ingestão de dados.

Conforme a arquitetura definida no `AGENTS.md` e na spec de integração, o FastAPI deve ser implantado como uma aplicação empacotada em container imutável. É necessário escolher um provedor de hospedagem gerenciado que atenda aos requisitos de infraestrutura, segurança, operabilidade e viabilidade financeira.

---

## 2. Opções Comparadas

Foram avaliadas quatro alternativas concretas de hospedagem de contêineres gerenciados:

1. **Render** (Web Service gerenciado)
2. **Fly.io** (App micro-VMs / Firecracker)
3. **Railway** (Containers gerenciados)
4. **Google Cloud Run** (Container Serverless gerenciado)

---

## 3. Matriz Comparativa Detalhada

| Critério | Render | Fly.io | Railway | Google Cloud Run |
|---|---|---|---|---|
| **Região e Egress Supabase** | `us-east-1` / `sa-east-1` (são paulo); egress direto com baixa latência se mesma região | `gru` (São Paulo) / `iad`; baixa latência | `us-east-1` / europe; sem região nativa no Brasil no plano padrão | `southamerica-east1` (São Paulo); altíssima integração e baixa latência |
| **Modelo de Custo** | Fixo por instância/mês (a partir de \$7/mês) + egress | Por uso fino (CPU/RAM/segundo) + egress | Por uso (RAM/vCPU por hora) + egress | Serverless puro (paga por 100ms de execução / CPU alocada no request + escala a zero) |
| **Suporte a Container Imutável** | Dockerfile / OCI Registry | Dockerfile / Fly Registry | Dockerfile / Railway Buildpack | OCI Container via Artifact Registry |
| **Health & Readiness Checks** | HTTP Health Check nativo (`/ready`, `/live`) | Health checks HTTP/TCP configuráveis em `fly.toml` | Healthcheck HTTP nativo com path configurável | Startup e Liveness Probes HTTP nativos |
| **Background Jobs / Workers** | Background Workers dedicados (\$7/mês cada) | Process groups independentes na mesma app | Services dedicados na mesma canvas | Cloud Tasks / Cloud Run Jobs para tarefas em segundo plano |
| **Gestão de Segredos** | Environment Variables & Secret Files nativos | Encrypted Secrets via CLI (`fly secrets`) | Variables e Shared Shared Variables | Google Secret Manager integrado nativamente |
| **Logs & Observabilidade** | Logs nativos em tempo real + export Logtail | Logs agregados (`fly logs`) + Nats stream | Log tail nativo + Datadog integration | Cloud Logging / Cloud Monitoring com retenção e estruturação JSON |
| **Domínio TLS & Custom Domain** | SSL automático (Let's Encrypt) e gerenciamento de DNS | SSL automático e terminação Anycast | SSL automático para domínios customizados | SSL automático via Google Managed Certificates |
| **Deploy & Rollback** | Zero-downtime deploys + rollback via dashboard/API | Blue/Green ou Canary deploys com `fly deploy` + rollback imediato | Rollback por commit/deployment digest | Revisioning imutável com Instant Traffic Splitting / Rollback em < 1s |
| **SLA e Alta Disponibilidade** | 99,9% uptime garantido em planos pagos | SLA de infraestrutura global | SLA de 99,9% em planos Pro | SLA de 99,95% gerenciado pelo Google |

---

## 4. Análise e Recomendação Técnica

### Opção Recomendada: **Google Cloud Run** (`southamerica-east1` - São Paulo)

#### Raciocínio Técnico:
1. **Região Local (São Paulo):** Permite menor latência para os usuários finais no Brasil e proximidade com o projeto Supabase (se alocado em São Paulo).
2. **Modelo Serverless com Escala a Zero:** Para a fase de lançamento e homologação, minimiza os custos fixos quando o tráfego for baixo, permitindo escalar automaticamente sob pico sem ajustes manuais.
3. **Revisões Imutáveis e Rollback Instantâneo:** Cada novo deploy gera uma revisão fechada e imutável. Caso ocorra qualquer problema pós-deploy, a reversão de tráfego (traffic splitting) é instantânea (0 segundos de latência para rollback).
4. **Isolamento de Segredos e Logs:** Integração nativa e segura com o Secret Manager (evitando segredos em texto puro) e logs JSON estruturados nativos.

---

## 5. Decisão para Aprovação do Owner

Decisão formal registrada pelo proprietário:

- [x] **Opção A (Aprovada):** Google Cloud Run (Região `southamerica-east1` - São Paulo, modelo serverless).
- [ ] **Opção B:** Render (Região São Paulo / US, instância fixa a partir de \$7/mês).
- [ ] **Opção C:** Fly.io (Região `gru` - São Paulo, micro-VMs).
- [ ] **Opção D:** Railway.

---

## 6. Consequências da Decisão

- A opção escolhida guiará a criação da task **ECO-2001** (Dockerfile e scripts de startup/readiness/shutdown).
- Nenhum código de infraestrutura ou conta paga será criado nesta fase (ECO-1302).
- O arquivo de ADR será mantido em `docs/adr/0005-provedor-fastapi.md` com o status atualizado para `aceito` após a confirmação.
