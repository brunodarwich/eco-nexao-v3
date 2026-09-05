# Relatório de Verificação e Evidências — ECO-2604: Padronização de Pacote de Dados e Revisão Editorial

Data: 2026-09-05  
Status da Tarefa: `VERIFIED` (O padrão e ferramentas de especificação foram consolidados)  
Status de Homologação da Rota de Exemplo: `PARTIAL` (Estrutura e geometrias comprovadas; dados editoriais operam como especificação/exemplo técnico, sem homologação de release)  
Executor: Antigravity  
Worktree / Branch: `.worktrees/eco-2604` (`eco-2604-route-data-package`)  
Commit-base: `a6fbf9f` (ECO-2603 — reconciliação normativa)  

---

## 1. Objetivo Atingido

A tarefa **ECO-2604** estabelece o padrão normativo e os instrumentos documentais para que a equipe humana do ECOnexão ou assistentes de IA possam coletar, catalogar, auditar e revisar de maneira reproduzível e segura cada uma das rotas turísticas do ecossistema, utilizando o caso da **Rota Pindobal** como referência técnica.

Foram produzidos e revisados com rigor factual estrito:
1. **Template Normativo (`docs/data/route_data_package_template.md`):** Modelo estruturado de especificação de rota cobrindo identificação, origens homologadas, trajetos viários/geometria, CRS 4326, proveniência imutável, taxonomia canônica de 8 grupos e subtipos, fichas de atores (POIs), governança de tags de experiência (com omissão de tags não aplicáveis), regras de mídia editorial com acessibilidade/licenciamento e checklist de publicação.
2. **Pacote de Referência Pindobal (`docs/data/pindobal_route_package.md`):** Caso concreto preenchido com dados auditados do recorte Pindobal e inventário SEMTUR:
   - Status da rota fixado em `draft` e `is_verified: false` (rota não homologada para release público; opera como base técnica);
   - 3 origens homologadas (Porto, Aeroporto e Rodoviária) com coordenadas WGS84 auditadas;
   - 3 geometrias OSRM com extensões (45,23 km, 41,45 km e 42,32 km) e hashes SHA-256 idênticos ao manifesto imutável do snapshot `teste-rota`;
   - Fichas de atores representativas extraídas diretamente com referências de página e ID nos inventários (`semtur_p57_id40`, `semtur_p73_id95`, `semtur_p96_id137`, `semtur_p36_id6`);
   - 31 valores ausentes estritamente explicitados como `VALOR_AUSENTE` (incluindo campos de contato, horários e referências externas nas fichas e no checklist), sem qualquer dado fictício;
   - Expurgadas todas as URIs artificiais com `cid=` e ratings/reviews comerciais sem Place ID comprovado;
   - Restrição do selo `SEMTUR` exclusivamente a quem possui referência comprovada no inventário municipal;
   - Omissão de tags de experiência não aplicáveis.
3. **Guia Operacional de Preenchimento (`docs/catalogo_territorial/instrucoes_preenchimento_rotas.md`):** Guia detalhado passo a passo orientando a curadoria editorial e IAs no preenchimento das próximas rotas, contendo regras de ouro, vedações estritas de alucinação de dados e dicionário de termos.

---

## 2. Auditoria e Correções Aplicadas (Rigor Factual)

Em conformidade com a auditoria corretiva:
1. **Remoção de Dados Sem Fonte Local:** Estabelecimentos inventados ou dados de contato sem correspondência no snapshot `teste-rota` foram substituídos por registros reais auditados com IDs da SEMTUR (ex: Pousada Casa de Vidro ID 40, Pousada Açairé ID 95, Casa do Saulo ID 137 e Araribá Tropical ID 6).
2. **Correção de `source_location`:** Proibido o uso de `source_location: google_places` sem coleta autorizada ponta a ponta. Registros legados sem chave foram classificados como `snapshot_infraestrutura_legado`.
3. **Eliminação de URIs `cid=` e Ratings Google:** Removidas todas as URLs artificiais com `cid=` e ratings/review counts não respaldados por `place_id` canônico da Places API (New).
4. **Isolamento do Selo SEMTUR:** Estabelecimentos de apoio viário comercial sem menção no inventário municipal receberam `is_semtur_inventory: false`.
5. **Omissão de Tags Incompatíveis:** Tags não aplicáveis foram completamente omitidas das fichas de atores, eliminando o preenchimento de tags nulas ou marcadas como 'não aplicável'.
6. **Vínculo Imutável de Geometrias:** As 3 geometrias mantêm seus vínculos estritos aos arquivos e hashes SHA-256 do manifesto imutável `teste-rota`.
7. **Status da Rota Não-Aprovado:** A rota Pindobal está expressamente demarcada como `draft` e status global `PARTIAL`, pois a mídia e a curadoria de campo final ainda dependem de carga real e homologação de release.

---

## 3. Evidências de Validação Automatizada

1. **Validador Estrutural de Integridade (`validate_eco_2604.py`):**
   - Check 1: Arquivos base existem e não estão vazios — `OK`
   - Check 2: Zero `google_place_id` inventados (instâncias como `VALOR_AUSENTE`) — `OK`
   - Check 3: Taxonomia canônica dos 8 grupos respeitada — `OK`
   - Check 4: Valores ausentes devidamente explicitados (31 ocorrências de `VALOR_AUSENTE`) — `OK`
   - Check 5: Proibição de cópia de fotos Google para Storage explicitada — `OK`
   - *Resultado:* 100% aprovado (`Exit Code 0`).

2. **Scanner de Segredos (`backend/scripts/scan_secrets.py`):**
   - `python backend/scripts/scan_secrets.py`
   - *Saída:* `SECRET_SCAN=OK` (`Exit Code 0`).

3. **Verificação de Diff do Git (`git diff --check`):**
   - *Saída:* Vazia / 0 erros de formatação ou whitespace (`Exit Code 0`).

---

## 4. Estado da Task e Próxima Ação

- **Status da Task ECO-2604:** `VERIFIED` (ferramental normativo e contrato concluídos).
- **Status da Rota Pindobal:** `PARTIAL` (especificação técnica de referência pronta; dados finais dependem da esteira de carga).
- **Desbloqueia:** Tarefa **ECO-2605** (Generalizar importação para múltiplas rotas e regiões).
