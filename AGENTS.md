# ECOnexão — Instruções para agentes de desenvolvimento

## Missão

Implementar a integração definida em `docs/backend_integration_spec.md`, uma tarefa `ECO-XXXX` por vez, preservando o aplicativo funcional. O alvo é Expo + FastAPI + Supabase PostgreSQL/PostGIS/Auth/Storage.

## Leia antes de alterar código

Na ordem:

1. Este arquivo.
2. `docs/README.md` para localizar a fonte normativa.
3. `docs/backend_integration_spec.md` para comportamento final.
4. A tarefa em `docs/backend_integration_tasks.md`.
5. `docs/ai_task_playbook.md` para o protocolo de execução.
6. Referências específicas indicadas pela tarefa: ADR, contrato Pindobal, aceites e testes.

Não implemente uma decisão marcada como aberta. Pare e solicite uma decisão ou conclua primeiro a task de ADR correspondente.

## Fonte de verdade

Em caso de divergência, use esta precedência:

1. ADR aceito em `docs/adr/`.
2. `docs/backend_integration_spec.md`.
3. Contrato OpenAPI versionado.
4. Contratos de dados em `docs/data/`.
5. Critérios em `docs/acceptance_criteria.md`.
6. `docs/backend_integration_tasks.md`.
7. `docs/elementos_interativos_telas.txt`, que descreve principalmente o estado atual.
8. Design specs.
9. Código atual e mocks, que podem representar apenas o protótipo.

Não use a cópia `elementos_interativos_telas.txt` da raiz como fonte normativa; a cópia canônica está em `docs/`.

## Decisões fixadas

- O app permanece em Expo SDK 54 durante a integração. Upgrade é trabalho separado.
- O backend é FastAPI em Python.
- O banco é Supabase PostgreSQL 17 com PostGIS.
- Supabase Auth gerencia identidades e JWTs.
- Supabase Storage guarda avatares e mídia.
- Docker não é pré-requisito.
- Projetos Supabase de development, test, staging e production são separados.
- FastAPI é a API de domínio e a única fronteira para Google Places, GBP, OSRM e ingestão.
- Migrations SQL em `supabase/migrations` são a única fonte de verdade do schema. Não introduza Alembic.
- Dados remotos não devem permanecer duplicados no `AppContext`.

## Regras Supabase

- Antes de implementar uma feature Supabase, consulte changelog e documentação atuais.
- Nunca exponha secret key ou `service_role` no Expo. Somente URL e publishable key podem estar em variáveis `EXPO_PUBLIC_*`.
- Não crie objetos customizados em `auth`, `storage` ou `realtime`.
- Tabelas expostas exigem `GRANT` explícito, RLS e testes negativos. RLS e exposição à Data API são controles diferentes.
- Não use `auth.role()`; anonymous users também assumem o papel `authenticated`.
- Ownership usa `(select auth.uid()) = user_id` ou equivalente aprovado.
- UPDATE com RLS exige políticas de SELECT, `USING` e `WITH CHECK`.
- Views expostas usam `security_invoker = true`.
- Não adicione `SECURITY DEFINER` para contornar erro de permissão.
- Storage upsert exige teste de INSERT, SELECT e UPDATE.
- Rode advisors antes de promover uma migration.
- Descubra comandos da CLI com `supabase --help`; não adivinhe flags.
- Crie migrations pelo comando oficial da versão instalada; não invente timestamps/nomes manualmente.

## Dados e conectores

- `C:\Users\Bruno\Downloads\teste-rota` é fonte externa somente leitura.
- Nunca altere os arquivos originais dessa pasta.
- Toda importação deve ser reproduzível, idempotente e produzir relatório de contagens/rejeições.
- Não invente `google_place_id` ausente.
- Chaves Google ficam somente no backend/secret manager.
- Não faça chamadas Google em testes ou CI; use fixtures e mocks contratuais.
- Não leia CSV em runtime da API.

## Regras de implementação

- Trabalhe apenas no escopo da task ativa e suas dependências diretas.
- Antes de editar, escreva o mini-brief exigido por `docs/ai_task_playbook.md`.
- Preserve alterações do usuário e não faça refactors oportunistas.
- Não deixe fallback silencioso para `mockData.ts` em código de produção.
- Todo controle com semântica interativa deve funcionar por toque, teclado e leitor de tela.
- Toda consulta remota precisa de loading, vazio, erro e retry.
- Toda mutation otimista precisa de rollback e anúncio acessível de falha.
- Não acesse Supabase diretamente de componentes React; use a camada de serviços/hooks definida pela arquitetura.
- Não faça SQL direto nas rotas FastAPI; use service/repository.
- Não altere schema pelo Dashboard sem migration versionada/reconciliada.

## Comandos atuais

Frontend:

```powershell
cd econexao-app
npm install
npm run web
npm run android
```

O backend e os comandos Supabase ainda serão criados pelos Marcos 1–3. Até existirem, não declare tasks dependentes como verificadas. Os comandos normativos planejados estão em `DEVELOPMENT.md` e devem ser atualizados quando os scripts reais forem adicionados.

## Definition of Done por task

- Critérios da task e da spec atendidos.
- Tipos/contratos sincronizados.
- Migration versionada e verificada, quando aplicável.
- RLS/grants/policies com testes positivos e negativos, quando aplicável.
- Testes relevantes executados e resultados registrados.
- Loading/vazio/erro/retry e acessibilidade cobertos quando houver UI.
- Nenhum segredo, dado pessoal indevido ou chamada externa em teste.
- Documentação e checklist da task atualizados.
- Entrega lista arquivos alterados, comandos executados, resultados, riscos e pendências.

## Paradas obrigatórias

Pare e peça decisão quando:

- Uma task depender de ADR não aceito.
- For necessário acessar production.
- A ação puder apagar ou sobrescrever dados remotos.
- Faltar credencial ou autorização externa.
- A política Google/Supabase não permitir o desenho proposto.
- A alteração exigir upgrade de Expo ou mudança de provedor.
