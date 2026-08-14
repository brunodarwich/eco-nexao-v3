# Guia de Operação Assistida, SLOs e Handoff Operacional (ECO-2205)

Este documento define o modelo de operação assistida pós-lançamento, métricas de qualidade de serviço (SLOs), políticas de contenção de custos e os critérios para assinatura do aceite final da release `v1.0.0` do **ECOnexão**.

---

## 1. Janela de Operação Assistida (24h a 72h)

Durante a primeira janela de operação pública:
- **Monitoramento Contínuo:** Observabilidade ativa dos logs estruturados do Render e métricas de conexão do Supabase.
- **Canal de Comunicação Direta:** Plantão técnico para triagem imediata de qualquer anomalia reportada por usuários piloto ou de campo.
- **Reunião de Alinhamento Diária:** Revisão de métricas de tráfego, cadastros e acessibilidade.

---

## 2. Indicadores e Objetivos de Nível de Serviço (SLIs / SLOs)

| Métrica / Serviço | SLI (Indicador) | SLO (Objetivo Mínimo) | Ação em caso de violação |
|---|---|---|---|
| **Disponibilidade da API** | Requisições HTTP com sucesso (2xx/3xx/4xx) | `>= 99.9%` (janela 30d) | Rollback imediato no Render e análise de crash logs. |
| **Latência da API** | Tempo de resposta P95 em rotas de catálogo e rotas | `<= 500ms` | Otimização de índices PostGIS e cache de queries. |
| **Taxa de Falha 5xx** | Erros 500/502/503/504 sobre total de requests | `<= 0.1%` | Acionamento de SEV-1 ou SEV-2 conforme incident runbook. |
| **Estabilidade Mobile** | Sessões livres de crash (Android/iOS) | `>= 99.8%` | Pausa de rollout na Play Store/App Store. |
| **Sanidade do Storage** | Upload e renderização de mídia | `>= 99.5%` sucesso | Verificação de cotas e RLS de buckets. |

---

## 3. Monitoramento e Guarda de Custos (Cost Guards)

Conforme documentado em [`cost_guards.md`](file:///c:/Users/Bruno/Downloads/eco-nexao-v3/docs/runbooks/cost_guards.md):
- **Render:** Instância Web Python com teto fixo no plano *Starter*.
- **Supabase:** Monitoramento do volume de banco (PostgreSQL) e egress de Storage para permanência dentro dos limites do plano.
- **Google Places API:** Conector protegido com cache local, limite de requisições e bloqueio automático caso a cota gratuita mensal se aproxime do teto estipulado.

---

## 4. Matriz de Escalonamento e Handoff

| Papel | Responsabilidade | Contato / Canal |
|---|---|---|
| **Human Owner / Product Lead** | Decisões de negócio, aceite de release e aprovação de janelas de produção. | Canal Principal de Operações |
| **Tech Lead / Operador de Nuvem** | Manutenção de infraestrutura Render, Supabase e DNS. | On-Call Técnico |
| **Encarregado de Dados (DPO)** | Atendimento a solicitações LGPD e segurança de dados. | `privacidade@econexao.app` |
| **Suporte ao Usuário** | Recepção de feedbacks e triagem de dúvidas. | `contato@econexao.app` |

---

## 5. Ata de Aceite Final do Marco 22

A conclusão formal deste ciclo atesta que:
1. Todas as tarefas técnicas e de infraestrutura do Marco 22 foram documentadas, auditadas e preparadas para execução controlada.
2. Os Gates 7 e 8 possuem critérios claros, determinísticos e planos de rollback acionáveis.
3. O sistema está homologado e pronto para a evolução contínua da plataforma.
