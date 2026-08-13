# ADR 0003 — Mapa com adaptadores por plataforma

Status: aceito  
Data: 11/08/2026

## Contexto

O projeto possui Android, iOS e web. Uma única biblioteca de mapa pode não oferecer o mesmo suporte nas três plataformas e o protótipo atual usa imagem raster.

## Decisão

Preservar `MapAdapter` como contrato do domínio visual:

- Implementação nativa compatível com Expo SDK 54 para Android/iOS.
- Implementação web baseada em Leaflet/MapLibre.
- Payload único do FastAPI com GeoJSON/polyline, bounds, pins, categorias e origem.

## Critérios

- Zoom, câmera, linha e pins funcionam nas plataformas suportadas.
- Nenhuma regra de negócio depende do SDK visual.
- Chaves públicas de mapas têm restrições de aplicativo/domínio.
- A seleção `actorId` e `originId` sobrevive à navegação.
