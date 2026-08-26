# Operação segura do Google Routes — ECO-2314

## Estado

Provider aprovado: Google Routes API v2 `ComputeRoutes Essentials`.
Produção e chamadas reais não estão autorizadas. A feature permanece desligada em
staging até todos os gates abaixo estarem comprovados.

## Configuração de staging

Variáveis não secretas:

```env
APP_ENV=staging
ROUTING_PROVIDER=google_routes
ENABLE_DYNAMIC_ROUTING=false
DYNAMIC_ROUTING_RATE_LIMIT_PER_MINUTE=10
GOOGLE_ROUTES_TIMEOUT_SECONDS=3.5
GOOGLE_ROUTES_MAX_RETRIES=2
GOOGLE_ROUTES_MONTHLY_ALERT_AT=7500
GOOGLE_ROUTES_MONTHLY_LIMIT=9000
```

Segredo exclusivo do backend, configurado no secret manager do serviço:

```text
GOOGLE_ROUTES_API_KEY
```

Nunca registrar, imprimir, copiar para o Expo ou salvar o valor no repositório.

## Guardas obrigatórios

- Google Cloud: Routes API apenas; 10 chamadas/minuto; 290 chamadas/dia.
- Backend: 10 previews/minuto por identidade/IP; alerta mensal em 7.500; bloqueio
  antes da chamada 9.001.
- Somente `DRIVE`, `TRAFFIC_UNAWARE`, sem alternativas e field mask de distância,
  duração e polyline. Opções Pro/Enterprise são proibidas.
- Cache de respostas Google desabilitado até homologação jurídica específica.
- Logs `httpx`/`httpcore` desabilitados; métricas permitem apenas provider, resultado,
  latência, status e modo, nunca coordenadas, payload ou chave.

## Desativação e rollback

Definir `ENABLE_DYNAMIC_ROUTING=false` e reiniciar o serviço. O cliente mantém ou
restaura uma das origens oficiais. Provider desconhecido falha fechado e nunca cai
automaticamente no Fake.

## Smoke de staging

Não executar sem autorização humana específica posterior. Quando autorizado, usar
uma única chamada, host HTTPS allowlisted e coordenadas de teste aprovadas. O script
`backend/scripts/staging_routing_smoke.py` não aceita produção, não repete a chamada
e não imprime coordenadas.
