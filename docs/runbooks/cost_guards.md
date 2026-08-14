# Runbook: Governança de Custos, Quotas e Proteção de Orçamento (Cost Guards)

Este documento estabelece as diretrizes e limites operacionais para prevenir estouro de custos na infraestrutura do ECOnexão.

---

## 1. Conector Google Places API (GBP)

- **Diretriz**: Nenhuma chamada externa ao Google Places é permitida em tempo de execução de consultas do usuário final no App.
- **Mecanismo de Proteção**:
  - Ingestão assíncrona controlada por script (`backend/app/services/places_importer.py`).
  - Cache obrigatório com TTL de 30 dias para Place Details e 90 dias para fotos.
  - Orçamento diário configurado no Google Cloud Console com alerta em 50%, 80% e 100% da quota mensal autorizada.
  - `GBP_CONNECTOR_ENABLED=False` por padrão em ambientes de teste e desenvolvimento.

---

## 2. Supabase PostgreSQL & Storage

- **Banco de Dados (PostgreSQL 17 + PostGIS)**:
  - Limite de conexões ativas gerenciado pelo pooler Supavisor (modo transaction).
  - Índices espaciais GiST em todas as colunas geométricas (`geom`) para evitar sequential scans caros em memória.
  - Queries territoriais filtradas por bounding box antes de cálculos de distância exata.
- **Storage**:
  - Imagens de avatares com limite estrito de 2 MB por arquivo.
  - Validação de tipos MIME permitidos (`image/jpeg`, `image/png`, `image/webp`).
  - Imagens servidas via CDN com cabeçalhos `Cache-Control: public, max-age=31536000, immutable`.

---

## 3. Render Native Python (FastAPI)

- **Plano de Execução**: `starter` (Render Native Python Service sem Docker).
- **Consumo de Memória**: Baseline monitorado < 250 MB sob carga nominal.
- **Rate Limiter em Memória**:
  - Sliding-window de 120 req/min por IP/Token previne abuso de chamadas que poderiam forçar autoscaling desnecessário.
  - Limpeza automática de histórico de IPs a cada 30 segundos para manter a memória do processo estável.

---

## 4. Checklist de Monitoramento de Custos Mensais

| Recurso | Limite de Alerta | Ação em Caso de Alerta |
|---|---|---|
| **Google Cloud API** | R$ 100 / mês | Pausar sincronização de fotos e detalhes; usar apenas dados já armazenados em cache. |
| **Supabase Egress** | 80% do plano | Revisar compressão de assets e otimizar payloads GeoJSON no backend. |
| **Render CPU/Bandwidth** | 80% do limite | Investigar rotas não cacheadas e verificar picos de tráfego nos logs estruturados. |
