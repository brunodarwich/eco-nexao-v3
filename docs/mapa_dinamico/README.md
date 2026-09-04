# ECOnexão — Mapa por camadas e origens dinâmicas

Status: registro histórico de uma iniciativa amplamente implementada; estado atual
em [`../project_status.md`](../project_status.md).
Owner das decisões: proprietário do produto  
Entrada normativa superior: `../README.md`

## Para que serve esta pasta

Este pacote organiza duas evoluções relacionadas, sem descartar as três rotas já
existentes:

1. padronizar categorias, cores, ícones, legenda e camadas de pins;
2. acrescentar `Minha localização` e `Escolher no mapa` como origens temporárias.

As rotas Porto, Aeroporto e Rodoviária permanecem como geometrias verificadas,
rápidas e disponíveis como fallback. Rotas calculadas de uma coordenada do usuário
serão sugestões efêmeras e não serão publicadas como rotas territoriais verificadas.

## Como pedir uma sessão ao Antigravity

Use somente um prompt por conversa/sessão. Exemplo:

```text
Execute exatamente a task descrita em
docs/mapa_dinamico/prompts/ECO-2304.md.
Leia o arquivo inteiro e siga o protocolo de subagentes indicado nele.
Não antecipe a próxima task.
```

Antes de iniciar outra sessão, cole ou registre o handoff da sessão anterior e
confirme que a dependência está realmente concluída.

## Arquivos deste pacote

- `plano_implementacao.md`: visão geral, ordem, escopo e gates.
- `tasks.md`: backlog proposto ECO-2301–ECO-2315 e seus estados permitidos.
- `protocolo_sessoes.md`: regras comuns para todas as sessões e subagentes.
- `prompts/ECO-2301.md` a `prompts/ECO-2315.md`: prompts copiáveis.

## Regras que não podem ser flexibilizadas

- Uma sessão executa somente uma task `ECO-23XX`.
- Nenhum agente aceita ADR ou decisão em nome do owner.
- Coordenadas do usuário não são persistidas em tabelas editoriais nem registradas
  em logs, telemetria ou URLs.
- Nenhuma chamada Google real, billing, contratação ou produção ocorre sem decisão
  e autorização explícitas.
- O servidor público de demonstração do OSRM não é infraestrutura de produção.
- O frontend não acessa tabelas territoriais diretamente no Supabase; usa FastAPI.
- Contrato e schema precedem consumidores.
- Alterações do usuário e áreas fora da task são preservadas.

## Próxima ação histórica

Começar por `ECO-2301` para congelar a taxonomia visual. A decisão de camadas
espaciais ocorre em `ECO-2305` e o ADR de origens dinâmicas em `ECO-2308`. As três
tasks são documentais e exigem aprovação humana antes das implementações dependentes.

Esta sequência registra o plano original e não deve mais orientar a próxima sessão.
Android/iOS estão `MOBILE_LATER` e não bloqueiam o fechamento da versão Web.
