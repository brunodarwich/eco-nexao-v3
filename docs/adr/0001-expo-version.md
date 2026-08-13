# ADR 0001 — Manter Expo SDK 54 durante a integração

Status: aceito  
Data: 11/08/2026

## Contexto

O `package.json` usa Expo `~54.0.0`, React Native 0.81 e React 19.1. A instrução anterior citava SDK 57, criando risco de documentação e APIs incompatíveis.

## Decisão

Manter SDK 54 durante toda a integração de backend. Consultar documentação versionada em `https://docs.expo.dev/versions/v54.0.0/`.

## Consequências

- Nenhuma task de backend pode atualizar Expo implicitamente.
- Dependências devem ser compatíveis com SDK 54.
- Upgrade terá ADR, branch/task e regressão Android/iOS/web próprios.
