# Runbook: Promoção Segura da Fatia Pindobal para Staging (ECO-2005)

**Status:** `APPROVED FOR LOCAL IMPLEMENTATION ONLY` (Fase 1 Concluída)
**Ambiente Alvo:** Staging exclusivamente (`kchzucvrnzwzehfdwzwi`)
**Data da Versão:** 02/09/2026
**Responsável Operacional:** Engenharia de Dados & Infraestrutura (Google Antigravity / Codex)

---

## 1. Objetivo e Escopo

Este runbook estabelece o protocolo de promoção controlada da fatia territorial da Rota Pindobal para o ambiente de **Staging**, garantindo:
1. **Target Guard Fail-Closed:** O runner aceita única e exclusivamente o Supabase Project Ref `kchzucvrnzwzehfdwzwi`. Qualquer outro target é rejeitado imediatamente.
2. **Execução em Duas Fases:**
   - **Fase 1 (Atual):** Verificação offline de integridade, dry-run com validação de contagens canônicas, testes unitários e alinhamento normativo. Nenhuma escrita remota é realizada.
   - **Fase 2 (Remota):** Escrita atômica no banco de staging sob exclusão mútua (`pg_try_advisory_xact_lock`), estritamente condicionada a um **novo GO formal e explícito do Human Owner**.
3. **Bloqueio Absoluto de Targets Não Autorizados:** Qualquer ambiente fora da allowlist unária de staging é terminantemente inalcançável por este runner; a promoção de produção é de governança exclusiva da **ECO-2202** (Marco 22) sob o Gate 7.
4. **Governança do Gate 4:** A execução da promoção de dados NÃO conclui o Gate 4 por si só. Ela supre o banco de staging com os dados territoriais necessários para habilitar o Gate 3 e a homologação E2E (ECO-2101).

---

## 2. Parâmetros Canônicos do Ambiente Staging

| Parâmetro | Valor Autorizado | Notas de Segurança |
|---|---|---|
| **Ambiente (`APP_ENV`)** | `staging` | Rejeita qualquer outro valor |
| **Project Ref** | `kchzucvrnzwzehfdwzwi` | Allowlist unária (fail-closed) |
| **Supabase REST URL** | `https://kchzucvrnzwzehfdwzwi.supabase.co` | Validado via HTTPS estrito |
| **Database Host** | `db.kchzucvrnzwzehfdwzwi.supabase.co:5432` ou `*.pooler.supabase.com:5432` | Porta 5432 exclusivamente (direto ou session pooler); porta 6543 é proibida |
| **Advisory Lock ID** | `3779311896921572133` | 64-bit int (`econexao:staging_promotion:pindobal`) |
| **Diretório Snapshot** | `C:\Users\Bruno\Downloads\teste-rota` | Fonte externa estritamente somente leitura |

> [!CAUTION]
> **Bloqueio de Targets Não Autorizados:**
> Qualquer tentativa de apontar para refs obsoletos, refs de teste (`backend/.env.test`) ou qualquer outro target diferente da allowlist staging (`kchzucvrnzwzehfdwzwi`) resultará em abort imediato com código 1 (`TargetValidationError`).

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
- **Candidatos (dry-run):** 53 registros (bloqueados para persistência sem curadoria)
- **Rejeitados:** 0 registros
- **Place IDs inventados:** 0 (todos os 737 registros Google legados sem Place ID são preservados como raw sem inventar ID sintético)
- **Métricas do Reconciliador (registradas separadamente):** 89 matches, sendo 57 candidatos classificados como fuzzy pelo classificador de similaridade.

### 3.3. Verificação de Alinhamento das 25 Migrations SQL (Fonte Única Normativa)
O schema oficial conta com exatamente 25 migrations em `supabase/migrations/`:
- De `20260811000000_init_postgis_and_base_schemas.sql` a `20260827221358_eco_2510_remove_legacy_google_photo_persistence.sql`.
- **Fonte Única Normativa:** O runner resolve e valida o manifesto canônico exclusivamente em `docs/finalization/artifacts/staging_migrations_manifest.json`, extraído do baseline `origin/staging`. Não há duplicidade de cópias nem fallback silencioso.
- **Validação Estrutural:** O runner valida a estrutura JSON (`schema_version=1`, `total_migrations=25`, campos obrigatórios, hashes de 64 hexadecimais, correspondência estrita de timestamps e nomes de arquivos).
- **Escopo Fase 1:** O runner verifica estritamente de forma local a integridade das 25 migrations no repositório.
- **Diferimento Fase 2:** A verificação remota de migration list, ausência de drift de schema e execução de Supabase advisors contra o projeto de staging (`kchzucvrnzwzehfdwzwi`) é parte integrante do preflight read-only da Fase 2, antes de qualquer escrita remota.

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

## 5. Controle de Concorrência e Boundary Transacional

A robustez da promoção decorre da arquitetura do banco e de uma demarcação transacional rigorosa:
- **Exclusão Mútua via `pg_try_advisory_xact_lock`:** O runner adquire o lock transacional `SELECT pg_try_advisory_xact_lock(3779311896921572133)` dentro de uma transação aberta exclusivamente pelo runner (`async with session.begin():`). Se o lock estiver ocupado, aborta imediatamente com `AdvisoryLockBusyError`.
- **Atomicidade por Unit of Work Proprietária:** A atomicidade da carga decorre de uma única camada proprietária da transação:
  1. `session.begin()`;
  2. Aquisição imediata do lock transacional;
  3. Execução das operações de persistência via `persist_in_transaction`;
  4. Validação do State Guard pós-execução;
  5. Commit único ao final do bloco (ou rollback automático em caso de exceção).
- **Separação de Responsabilidade no Repository:** A classe `PindobalPersistenceRepository` separa formalmente:
  - O wrapper transacional público (`persist`), que gerencia o próprio ciclo de vida para compatibilidade com o pipeline de teste (`seed_pindobal.py`); e
  - As operações que assumem uma transação já aberta (`persist_in_transaction`), utilizadas pelo runner sob o lock.
- **Helper contra Uso Acidental (`LockedAsyncSessionProxy`):** O proxy de sessão atua exclusivamente como um redutor de erros acidentais (proibindo `commit()` ou `rollback()` explícitos pelo corpo da carga). A segurança e atomicidade residem na arquitetura de Unit of Work única, não em proteções de runtime do Python.
- **Liberação Garantida no PostgreSQL:** O lock transacional é liberado deterministicamente pelo próprio servidor PostgreSQL (`ResourceOwner`) no encerramento da transação (`COMMIT` ou `ROLLBACK`) ou término da conexão socket. Não se presume que um comando explícito de rede de rollback sempre chegue ao banco durante partições de rede.
- **Rejeição do Transaction Pooler:** O runner rejeita terminantemente conexões na porta 6543 (Supavisor Transaction Pooler), aceitando apenas a porta 5432 (conexão direta ou session pooler), onde o ciclo de vida transacional é preservado.

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
# Executar suíte de testes unitários do runner
python -m pytest backend/tests/test_staging_promotion_runner.py

# Executar preflight offline completo com teste-rota
python -m app.ingestion.staging_promotion_runner --snapshot-dir "C:\Users\Bruno\Downloads\teste-rota" --non-interactive

# Verificar scanner de segredos (deve retornar SECRET_SCAN=OK)
python backend/scripts/scan_secrets.py
```

> [!NOTE]
> **Modo `--non-interactive`:** Este modo é exclusivo do preflight offline da Fase 1 (onde `remote_write_performed: false`). Ele é estritamente proibido e incapaz de autorizar qualquer operação de escrita remota presente ou futura.

### Codificação e Exibição no Terminal Windows (Code Page vs UTF-8)
Em terminais Windows (PowerShell ou `cmd.exe`), a página de código padrão do console frequentemente opera em OEM 850 ou Windows-1252 em vez de UTF-8 (Code Page 65001). Caracteres acentuados emitidos como UTF-8 podem parecer corrompidos na exibição visual do terminal caso o console esteja em codificação legada.
- O runner reconfigura explicitamente `sys.stdout` e `sys.stderr` para UTF-8 (`reconfigure(encoding="utf-8")`), garantindo que o stream de saída emita sempre JSON UTF-8 válido e parseável por qualquer ferramenta padrão (`json.loads`, `jq`, etc.).
- Para exibir caracteres acentuados corretamente na tela do console interativo no Windows, execute previamente: `chcp 65001` ou `$OutputEncoding = [System.Text.Encoding]::UTF8`.

### Saída Esperada do Preflight (Dry-Run Offline):
```json
{
  "status": "phase1_success",
  "phase": 1,
  "mode": "local_preflight_and_validation_only",
  "remote_write_performed": false,
  "target_project_ref": null,
  "remote_configuration": {
    "validated": false,
    "status": "offline_dry_run_no_remote_config_validated",
    "details": "Nenhuma configuração remota foi fornecida ou validada no modo dry-run offline."
  },
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
    "invented_place_ids": 0,
    "reconciliation": {
      "matches_count": 89,
      "fuzzy_candidate_count": 57
    }
  },
  "migrations": {
    "status": "aligned_locally",
    "scope": "local_directory_only",
    "count": 25,
    "first_migration": "20260811000000_init_postgis_and_base_schemas.sql",
    "latest_migration": "20260827221358_eco_2510_remove_legacy_google_photo_persistence.sql",
    "baseline_ref": "origin/staging",
    "manifest_verified": true,
    "remote_drift_and_advisors_check": "deferred_to_phase2_preflight"
  },
  "governance": {
    "advisory_lock_id": 3779311896921572133,
    "lock_mechanism": "pg_try_advisory_xact_lock",
    "transaction_ownership": "single_unit_of_work_transaction",
    "lock_release_guarantee": "postgresql_server_resource_owner_on_disconnect_or_termination",
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
