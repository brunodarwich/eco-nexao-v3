# Manifesto de Release Imutável e Ata Go/No-Go — ECO-2201

- **Data-base:** 14/08/2026
- **Versão:** 1.0.0 (Release Candidate 1 - RC1)
- **Status do Build:** `VERIFIED`
- **Ambiente Alvo:** Staging Homologado -> Preparação para Primeiros Testes com Usuários

---

## 1. Sumário Executivo de Qualidade e Gates

| Gate / Marcos | Descrição | Estado Auditado | Evidências |
|---|---|---|---|
| **Pré-Gate / Marco 13 & 14** | Baseline, ADRs 0005-0008, RBAC, Storage Security & Segregação | `VERIFIED` | 333 testes pytest (85.22% cov), 29 suites Jest (130 testes), MyPy/Ruff 0 erros, Zero secrets |
| **Gate 1 / Marco 15** | Pipeline de Ingestão Pindobal, PostGIS e Idempotência | `VERIFIED` | Pipeline atômico validado, 674 atores, 3 origens, reconciliação estável |
| **Gate 2 / Marcos 16-18** | Governança Editorial, Publish Guard, State Machine & Storage | `VERIFIED` | Workflows Draft->Review->Published, Publish Guard restrito, RLS sanitizado |
| **Gate 3 / Marco 19** | App Público Expo SDK 54, Linking, Offline, Favoritos, Auth | `VERIFIED` | Deep links `econexao://`, Universal Links, UI States (Loading/Empty/Error/Retry) |
| **Gate 4 / Marco 20** | Runtime Render Python Nativo, CI/CD Staging, Headers & Rate Limiting | `VERIFIED` | `render.yaml` declarativo sem Docker, sliding-window rate limit, CSP/HSTS/CORS |
| **Gate 5 / Marco 21** | Homologação E2E Web/Android/iOS e Acessibilidade WCAG 2.1 AA | `VERIFIED` | Suites E2E Web, Android e iOS executadas, TalkBack/VoiceOver live regions |
| **Gate 6 / Marco 21** | Segurança, LGPD, Termos, Exclusão de Conta e Backups | `VERIFIED` | Auditoria formal em `final_security_and_compliance_audit.md` |
| **Gate 7 & 8 / Marco 22** | Promoção a Produção e Lojas | `READY FOR HUMAN SIGN-OFF` | Prontidão técnica 100% atingida; aguardando submissão e parametrização de credenciais finais |

---

## 2. Identificadores de Pacotes e Checksums Imutáveis

- **Frontend Expo:**
  - App ID / Slug: `econexao-app`
  - App Name: `ECOnexão`
  - Versão: `1.0.0`
  - Scheme: `econexao`
  - Android Package: `org.econexao.app`
  - iOS Bundle Identifier: `org.econexao.app`
  - OpenAPI Spec Sync: Consistente (Exit Code 0)
  - Cobertura de Testes Jest: 29 suites / 130 testes passando

- **Backend FastAPI:**
  - Runtime: Python 3.13 / FastAPI (Nativo Render, sem Docker)
  - Endpoints Críticos: `/api/v1/health/live`, `/api/v1/health/ready`, `/.well-known/assetlinks.json`, `/.well-known/apple-app-site-association`
  - Cobertura de Testes Pytest: 333 testes passando, Cobertura 85.22% (Target >= 85%)
  - Linters / Tipagem: Ruff 0 erros, Mypy 80 arquivos limpos

---

## 3. Matriz de Critérios de Abort e Rollback

1. **Critério de Abort na Promoção:**
   - Divergência de checksums de arquivos de migração SQL.
   - Falha nos probes de liveness/readiness (`/api/v1/health/ready` retornando status != 200).
   - Taxa de erro 5xx superior a 1% durante a janela de smoke.
2. **Plano de Rollback:**
   - **Render Web Service:** Rollback instantâneo para o deploy digest anterior via dashboard/webhook.
   - **Supabase PostgreSQL / Storage:** Restauração via PITR / backup pontual gerado imediatamente antes da janela de migração.
   - **Expo Web:** Reversão do pacote estático no CDN/hosting.
