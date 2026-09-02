# Runbook: Promoção Segura da Fatia Pindobal para Staging (ECO-2005)

**Status:** `APPROVED FOR LOCAL IMPLEMENTATION ONLY` (Fase 1 Concluída)
**Ambiente Alvo:** Staging exclusivamente (`kchzucvrnzwzehfdwzwi`)
**Data da Versão:** 02/09/2026
**Responsável Operacional:** Engenharia de Dados & Infraestrutura (Google Antigravity / Codex)

---

## 1. Objetivo e Escopo

Este runbook estabelece o protocolo de promoção controlada da fatia territorial da Rota Pindobal para o ambiente de **Staging**, garantindo:
1. **Target Guard Fail-Closed:** O runner aceita única e exclusivamente o Supabase Project Ref `kchzucvrnzwzehfdwzwi`.
2. **Execução em Duas Fases:**
   - **Fase 1 (Atual):** Verificação offline de integridade, dry-run com validação de contagens canônicas, testes unitários e alinhamento normativo. Nenhuma escrita remota é realizada.
   - **Fase 2 (Remota):** Escrita atômica no banco de staging sob exclusão mútua (`pg_try_advisory_lock`), estritamente condicionada a um **novo GO formal e explícito do Human Owner**.
3. **Bloqueio Absoluto de Produção:** O projeto de produção (`hjtkcmbfndbgyurfhsuo`) é inalcançável por este runner; a promoção de produção é reservada à **ECO-2202** (Marco 22) sob o Gate 7.
4. **Governança do Gate 4:** A execução da promoção de dados NÃO conclui o Gate 4 por si só. Ela supre o banco de staging com os dados territoriais necessários para habilitar o Gate 3 e a homologação E2E (ECO-2101).

---

## 2. Parâmetros Canônicos do Ambiente Staging

| Parâmetro | Valor Autorizado | Notas de Segurança |
|---|---|---|
| **Ambiente (`APP_ENV`)** | `staging` | Rejeita qualquer outro valor |
| **Project Ref** | `kchzucvrnzwzehfdwzwi` | Allowlist unária (fail-closed) |
| **Supabase REST URL** | `https://kchzucvrnzwzehfdwzwi.supabase.co` | Validado via HTTPS estrito |
| **Database Host** | `db.kchzucvrnzwzehfdwzwi.supabase.co` | Porta 5432 (direto) ou 6543 (pooler) |
| **Advisory Lock ID** | `3779311896921572133` | 64-bit int (`econexao:staging_promotion:pindobal`) |
| **Diretório Snapshot** | `C:\Users\Bruno\Downloads\teste-rota` | Fonte externa estritamente somente leitura |

> [!CAUTION]
> **Bloqueio de Targets Não Autorizados:**
> Qualquer tentativa de apontar para refs obsoletos (`rgfuqmwxjuceqpxcraxm`), refs de teste (`backend/.env.test`) ou refs de produção (`hjtkcmbfndbgyurfhsuo`) resultará em abort imediato com código 1 (`TargetValidationError`).

---

## 3. Pré-Requisitos e Checagens de Integridade (Preflight)

Antes de qualquer operação, o runner executa 4 validações determinísticas locais:

### 3.1. Verificação Offline de Hashes do Snapshot (9 Arquivos)
O runner confere os checksums SHA-256 de todos os 9 arquivos normativos do pacote Pindobal v1:
- `inventario_semtur.csv` (`9b4bdf68...`)
- `data_semtur.json` (`0a384b8b...`)
- `santarem-pindobal.csv.csv` (`75e05523...`)
- `data.json` (`b597eb1e...`)
- `empresas_infraestrutura_rotas.csv` (`23c7a8c0...`)
- `pois_data.json` (`8875a1ea...`)
- `rota_porto_OSRM_01.csv` (`15c557a4...`)
- `rota_aeroporto_OSRM_01.csv` (`8cae67ad...`)
- `rota_rodoviaria_OSRM_01.csv` (`fd21e0df...`)

### 3.2. Dry-Run e Verificação das Contagens Canônicas
O dry-run local com o dataset `teste-rota` deve reproduzir exatamente os números homologados:
- **Lidos:** 1.714 registros
- **Potenciais/Criáveis:** 1.661 registros
- **Candidatos fuzzy:** 53 registros (bloqueados para persistência sem curadoria)
- **Rejeitados:** 0 registros
- **Place IDs inventados:** 0 (todos os 737 registros Google legados sem Place ID são preservados como raw sem inventar ID sintético)

### 3.3. Verificação de Alinhamento das 25 Migrations SQL
O schema oficial conta com exatamente 25 migrations em `supabase/migrations/`:
- De `20260811000000_init_postgis_and_base_schemas.sql` a `20260827221358_eco_2510_remove_legacy_google_photo_persistence.sql`.
- O runner verifica a ausência de novas migrations locais não versionadas e confere que nenhuma migration de schema é criada durante a carga de dados.

---

## 4. Protocolo de Dupla Confirmação Humana

Para evitar acionamentos acidentais ou automações não autorizadas, a transição para qualquer escrita futura exige confirmação humana em dois fatores:

1. **Fator 1 (Digitação Exata do Ref):**
   - O operador deve digitar manualmente o Project Ref: `kchzucvrnzwzehfdwzwi`.
   - Caso haja qualquer caractere incorreto, o processo é abortado imediatamente.
2. **Fator 2 (Confirmação Explícita de Ação):**
   - O operador deve responder afirmativamente à pergunta `[y/N]`.
   - Respostas vazias ou diferentes de `y`/`yes` resultam em abort imediato.

> [!IMPORTANT]
> Nenhuma conexão com privilégio de escrita ou transação remota é aberta antes da conclusão bem-sucedida de ambos os fatores de confirmação.

---

## 5. Controle de Concorrência: `pg_try_advisory_lock`

A exclusão mútua em nível de banco de dados previne corridas concorrentes entre múltiplos operadores ou pipelines:
- O runner invoca `SELECT pg_try_advisory_lock(3779311896921572133)`.
- **Comportamento não bloqueante:** Se o lock estiver detido por outro processo, o runner NÃO entra em espera indefinida; ele aborta imediatamente com erro claro: `AdvisoryLockBusyError`.
- **Liberação Obrigatória:** O lock é obrigatoriamente liberado no bloco `finally` da sessão assíncrona (`SELECT pg_advisory_unlock(3779311896921572133)`), mesmo se ocorrer exceção ou cancelamento.

---

## 6. Procedimento de Rollback

### 6.1. Rollback de Schema
- **Princípio:** Não existem migrations de rollback (down migrations) automáticas.
- **Procedimento:** Em caso de corrupção estrutural ou falha crítica de schema, o procedimento normativo é a restauração via **Point-in-Time Recovery (PITR)** ou snapshot gerenciado do Supabase no dashboard do projeto `kchzucvrnzwzehfdwzwi`.

### 6.2. Rollback de Dados (Lógico)
- **Princípio:** Proibida deleção cega (`DELETE FROM actors`).
- **Procedimento:**
  1. Alterar o status editorial da rota e atores para `draft` ou `unpublished`.
  2. Preservar intactos os registros de auditoria em `app_private.audit_logs`, os payloads brutos em `raw_source_records` e o histórico da execução em `ingestion_runs`.
  3. Emitir novo pacote imutável supersedendo a versão anterior caso sejam necessárias correções.

---

## 7. Instruções de Execução Local (Fase 1)

Na raiz do repositório ou no worktree de staging:

```powershell
# Executar suíte de testes unitários do runner (37 testes)
python -m pytest backend/tests/test_staging_promotion_runner.py

# Executar preflight offline completo com teste-rota
python -m app.ingestion.staging_promotion_runner --snapshot-dir "C:\Users\Bruno\Downloads\teste-rota" --non-interactive

# Verificar scanner de segredos (deve retornar SECRET_SCAN=OK)
python backend/scripts/scan_secrets.py
```

### Saída Esperada do Preflight:
```json
{
  "status": "phase1_success",
  "phase": 1,
  "mode": "local_preflight_and_validation_only",
  "remote_write_performed": false,
  "target_project_ref": "kchzucvrnzwzehfdwzwi",
  "manifest": {
    "status": "valid",
    "total_files": 9,
    "valid_files": 9
  },
  "canonical_counts": {
    "status": "verified",
    "counts": {
      "read": 1714,
      "created": 1661,
      "updated": 0,
      "unchanged": 0,
      "rejected": 0,
      "candidates": 53,
      "reconciled": true
    },
    "google_records_without_place_id": 737,
    "invented_place_ids": 0
  },
  "migrations": {
    "status": "aligned",
    "count": 25
  },
  "governance": {
    "advisory_lock_id": 3779311896921572133,
    "lock_mechanism": "pg_try_advisory_lock",
    "schema_rollback": "PITR_snapshot_only",
    "data_rollback": "logical_unpublish_draft_only",
    "phase2_remote_write": "BLOCKED_PENDING_EXPLICIT_OWNER_GO"
  }
}
```

---

## 8. Parada Obrigatória: Rito para a Fase 2 (Promoção Remota)

A transição para a **Fase 2** (conexão e carga real no Supabase de Staging `kchzucvrnzwzehfdwzwi`) exige:
1. Conclusão e revisão completa do PR da Fase 1 contra a branch `staging`.
2. Emissão de autorização formal e explícita pelo Human Owner (Bruno Darwich):
   > "Eu autorizo a execução da Fase 2 da ECO-2005 para carga da fatia Pindobal no banco de staging kchzucvrnzwzehfdwzwi."
3. Disponibilização segura de credenciais de staging via cofre ou variável controlada, sem nunca expô-las em terminal ou commit.
