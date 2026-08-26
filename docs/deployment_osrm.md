# Guia de Operação e Deploy do OSRM (Roteamento Regional Próprio)

> **DESCONTINUADO PARA A INICIATIVA ATUAL:** o ADR 0013 e o Gate H3 revisado em
> 2026-08-25 substituíram OSRM Self-Hosted por Google Routes API Essentials. Este
> arquivo é mantido somente como histórico técnico. Não contratar, provisionar ou
> ativar OSRM com base neste runbook sem uma nova decisão formal do Owner.

> Estado histórico anterior ao ADR 0013: a infraestrutura OSRM dedicada nunca foi
> comprovada neste repositório e não deve mais ser provisionada para esta iniciativa.
> O servidor público `router.project-osrm.org` continua proibido em staging e produção.

O procedimento histórico de smoke era one-shot, sem retry, e aceitava apenas o hostname exato
explicitamente autorizado. As coordenadas devem ser fornecidas por variáveis de
ambiente e nunca são impressas:

```powershell
$env:STAGING_SMOKE_ORIGIN_LATITUDE='<coordenada-autorizada>'
$env:STAGING_SMOKE_ORIGIN_LONGITUDE='<coordenada-autorizada>'
python backend/scripts/staging_routing_smoke.py --base-url https://<staging-autorizado> --route-id <uuid> --allowed-host <staging-autorizado> --confirm-staging
```

Não execute esse comando até a infraestrutura dedicada existir e o staging estar
explicitamente autorizado. Produção é recusada pelo script e permanece fora do escopo.

Este documento contém o passo a passo completo para subir e operar o serviço de roteamento **OSRM (Open Source Routing Machine)** em ambientes de **Staging** e **Produção** para o ECOnexão.

---

## 1. Arquitetura do Roteamento

```text
[ Expo App (Mobile/Web) ]
           │
           ▼ (POST /api/v1/routes/{id}/preview)
[ FastAPI Backend ] (Fronteira Única / Circuit Breaker 3.5s)
           │
           ▼ (HTTP GET na rede privada / interna)
[ OSRM Backend Container ] (:5000)
           │
           ▼
[ Grafo OpenStreetMap do Norte/Pará (Santarém, Belterra, Alter do Chão) ]
```

---

## 2. Preparação do Grafo Viário (Passo Único)

O OSRM precisa processar o extrato da malha rodoviária do OpenStreetMap uma única vez (ou quando quiser atualizar o mapa da região).

### No Linux / macOS / Servidor de Staging:
```bash
chmod +x scripts/setup_osrm.sh
./scripts/setup_osrm.sh
```

### No Windows (PowerShell):
```powershell
.\scripts\setup_osrm.ps1
```

O script realiza automaticamente:
1. Download do arquivo `norte-latest.osm.pbf` (~150MB) do Geofabrik.
2. Extração das vias navegáveis via perfil `car.lua` (`osrm-extract`).
3. Particionamento e hierarquia de nós (`osrm-partition`).
4. Customização das células de roteamento (`osrm-customize`).

---

## 3. Subindo o Serviço

Com os dados gerados na pasta `./osrm-data`, inicie o container:

```bash
docker compose -f docker-compose.osrm.yml up -d
```

### Testando a saúde do serviço:
```bash
curl "http://localhost:5000/route/v1/driving/-54.9536,-2.5089;-54.9600,-2.5100?overview=full&geometries=geojson"
```

---

## 4. Conectando o FastAPI ao OSRM

No servidor do backend (FastAPI), basta configurar as variáveis de ambiente no arquivo `.env` ou no painel da sua hospedagem:

```ini
# Provedor ativo
ROUTING_PROVIDER=osrm

# URL interna do serviço OSRM
# Se rodando na mesma rede Docker: http://osrm-backend:5000
# Se rodando em outra VPS/porta: http://10.0.0.X:5000 ou https://osrm.seu-dominio.com
OSRM_BASE_URL=http://osrm-backend:5000

# Guardrails e Timeouts de Segurança
OSRM_TIMEOUT_SECONDS=3.5
OSRM_MAX_RETRIES=2
ROUTING_CIRCUIT_BREAKER_FAILURES=5
ROUTING_CIRCUIT_BREAKER_RESET_SECONDS=60
ENABLE_DYNAMIC_ROUTING=true
```

---

## 5. Resiliência e Fallback Automático

O conector implementado no FastAPI (`backend/app/connectors/osrm_connector.py`) possui salvaguardas nativas:
- **Circuit Breaker:** Se o container OSRM ficar indisponível ou demorar mais de 3.5s por 5 vezes consecutivas, o circuito abre e o backend passa a responder instantaneamente sem travar o app.
- **Degradação Elegante no App:** O frontend exibe uma mensagem amigável e preserva a rota padrão oficial selecionada (Porto, Aeroporto ou Rodoviária).
