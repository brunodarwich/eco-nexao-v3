# Runbook: Promoção Controlada de Migrations e Carga Pindobal (ECO-2202)

Este runbook define o protocolo operacional estrito e sequencial para aplicação de migrations e execução do pipeline de ingestão Pindobal no ambiente de produção/staging do Supabase.

---

## 1. Pré-Requisitos e Janela de Execução

- **Aprovação Explícita:** Gate 6 e ECO-2201 assinados (`VERIFIED` e `GO`).
- **Janela Operacional:** Janela de manutenção aprovada com presença do Human Owner e operador técnico.
- **Backups e PITR:** Point-in-Time Recovery (PITR) e snapshot manual do Supabase gerados antes do início.
- **Zero Segredos:** Nenhuma credencial em texto puro em logs ou terminais compartilhados.

---

## 2. Passo a Passo de Execução

### Passo 1: Validação Pré-Voo (Preflight)
Verificar a conectividade e integridade do banco alvo sem aplicar escritas:
```powershell
# Verificar se as variáveis obrigatórias estão presentes na sessão
$env:SUPABASE_URL = "https://<PROJECT_ID>.supabase.co"
$env:DATABASE_URL = "postgresql://postgres.<PROJECT_ID>:[REDACTED]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"

# Validar health e conexão (entrypoint real: scripts/check_environment.py)
python -m scripts.check_environment --target production
```

### Passo 2: Registro do Estado Anterior
Executar query de auditoria para registrar contagens atuais e confirmar que a tabela de controle de migrations está acessível.

### Passo 3: Aplicação Sequencial das Migrations
Aplicar as migrations na ordem exata e imutável pelo comando oficial do Supabase CLI:
```powershell
# Via Supabase CLI oficial vinculado ao projeto remoto
supabase db push --linked
```

### Passo 4: Verificação de Advisors e RLS
- Executar os advisors de segurança do Supabase.
- Confirmar que todas as tabelas possuem `ENABLE ROW LEVEL SECURITY`.
- Validar que views expostas utilizam `security_invoker = true`.
- Zero alertas críticos de segurança.

### Passo 5: Ingestão de Atores Pindobal (Dry-Run & Execução Real)
Executar o pipeline atômico de ingestão via entrypoint oficial `app.ingestion.seed_pindobal`:

1. **Simulação (Dry-Run):**
```powershell
python -m app.ingestion.seed_pindobal --dry-run
```
*Critério:* Validar que contagens e hashes conferem com o manifesto aprovado em `docs/finalization/artifacts/pindobal-v1/`.

2. **Carga Efetiva (Idempotente):**
```powershell
python -m app.ingestion.seed_pindobal --apply
```

3. **Teste de Idempotência (Segunda Execução):**
```powershell
python -m app.ingestion.seed_pindobal --apply
```
*Critério:* A segunda execução deve resultar em **0 novos registros inseridos** e **0 duplicidades criadas**.

---

## 3. Matriz de Reconciliação e Smoke Pós-Migração

| Verificação | Critério de Aceite |
|---|---|
| Contagem de Atores Públicos | Exatamente correspondente ao catálogo validado |
| RLS Negativo | Usuário anônimo/autenticado sem permissão não pode criar/editar atores |
| Soft-Delete e Publish Guard | Atores em rascunho invisíveis para a rota pública `/api/v1/actors` |
| Performance de Busca Geoespacial | Queries `ST_DWithin` executando abaixo de 50ms com índice espacial GIST |

---

## 4. Critérios de Abort e Protocolo de Rollback

### Critérios de Abort Imediato:
- Falha de sintaxe ou erro de constraint em qualquer migration.
- Divergência no checksum de arquivos de migração.
- Falha no teste de idempotência da ingestão.
- Advisory crítico de segurança não resolvido.

### Procedimento de Restauração (Rollback):
1. **Interrupção:** Parar imediatamente o pipeline.
2. **Notificação:** Alertar os stakeholders sobre o disparo do abort.
3. **Restauração via PITR:**
   - No Dashboard do Supabase: Navegar em *Database* -> *Backups* -> *Point in Time Recovery*.
   - Selecionar o timestamp gravado imediatamente antes do início da janela de manutenção.
   - Confirmar a restauração e aguardar o status `Active`.
4. **Validação:** Executar suite de healthcheck para confirmar que o banco retornou ao estado íntegro pré-janela.
