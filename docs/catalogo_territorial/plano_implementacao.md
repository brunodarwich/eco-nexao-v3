# Plano de implementação — catálogo territorial SEMTUR + Google

Versão: 1.0  
Data: 27/08/2026  
Status: proposto

## 1. Arquitetura alvo

```text
Snapshot SEMTUR ─> raw_source_records ─> actor_external_refs ─┐
                                                             ├─> actors + actor_types
Places API (New) ─> refs/metadados permitidos ─> reconciliação┘          │
                                                                        ├─> route_actors/PostGIS
Fotos editoriais ─> Supabase Storage                                    │
Fotos Google ─> referência + atribuição + proxy temporário               └─> API/mapa/cards
```

Um ator canônico pode ter várias fontes. O selo `Inventário SEMTUR` deriva de uma
referência/proveniência institucional válida, não de texto duplicado no ator. Google
nunca sobrescreve silenciosamente SEMTUR ou edição aprovada.

## 2. Experiência pretendida

- Selo discreto no card: ícone institucional pequeno + texto `Inventário SEMTUR`,
  contraste AA, não interativo, com label acessível `Estabelecimento presente no
  Inventário Turístico da SEMTUR`. Não usar aparência de verificação ou endosso.
- Filtro primário por grupo visual e secundário por tipo específico.
- Pins do corredor dependem da geometria selecionada e de buffer editorial.
- Saúde/segurança são territoriais; transporte/apoio pode ser `both`.
- Card/detalhe separa conteúdo ECOnexão/SEMTUR de conteúdo `Dados do Google`.
- Galeria própria e galeria Google têm origem e licenciamento visualmente distintos.
- Nenhum modo de viagem, tracker, GPS contínuo ou navegação turn-by-turn.

## 3. Taxonomia proposta para decisão

Preservar poucos grupos visuais e adicionar tipos controlados:

| Grupo | Tipos iniciais candidatos | Escopo candidato |
|---|---|---|
| alimentação | restaurante, lanchonete, café, bar, barraca de praia | corredor |
| hospedagem | hotel, pousada, hostel, camping, casa de temporada | corredor |
| atrativos | praia, balneário, trilha, mirante, igreja, centro cultural | corredor |
| artesanato/economia local | artesanato, biojoias, souvenirs, associação comunitária | corredor |
| comércio e serviços | mercado, conveniência, oficina, banco/ATM, telecom | corredor/territorial a decidir |
| transporte e apoio viário | aeroporto, porto, rodoviária, táxi, ônibus, transfer, combustível | both |
| saúde | hospital, UPA, UBS, posto, farmácia, clínica | territorial |
| segurança e proteção | polícia, delegacia, bombeiros, guarda, defesa civil, conselho tutelar | territorial, com revisão por tipo |
| outros | não classificado/curadoria | política a decidir |

ECO-2503 deve comparar: manter oito grupos + tipos; ampliar grupos; ou modelo de tags
multivalor. Nenhuma opção é aceita por este plano.

## 4. Fases

### A — inventário e decisões (ECO-2501–2503)

Congela evidência, direitos, autoridade por campo, taxonomia e semântica espacial.
Entrega ADRs propostos e para nos gates H25.1/H25.2.

### B — dados institucionais e espaço (ECO-2504–2506)

Cria schema aprovado, importa todos os registros SEMTUR com relatório idempotente e
calibra 500/1000/2000/3000 m por Porto, Aeroporto e Rodoviária. A escolha de raio é
editorial e baseada nas contagens, não em preferência do implementador.

### C — Google e mídia (ECO-2507–2510)

Decide plataforma/política/custo, implementa Places New offline-first em testes,
reconciliação humana e fotos por proxy. GBP fica fora, salvo OAuth de parceiro
explicitamente autorizado em iniciativa futura.

### D — produto e homologação (ECO-2511–2513)

Congela contrato, entrega filtros/pins/cards/selo/galeria e executa homologação em
web e dispositivos. Staging/produção e gasto permanecem gates separados.

## 5. Dependências

```text
2501 -> 2502 -> 2504 -> 2505 -> 2506 ───────────┐
   └-> 2503 ───────┘                            ├-> 2511 -> 2512 -> 2513
2501 + 2502 -> 2507 -> 2508 -> 2509 -> 2510 ───┘
```

## 6. Critérios globais

- `lidos = criados + atualizados + inalterados + rejeitados + candidatos`.
- Os 674 SEMTUR são contabilizados; registro inválido continua preservado em raw.
- Nenhum Place ID é inferido de URL/nome.
- Distância é PostGIS/geography e calculada para a geometria selecionada.
- `route_bounds` não incorpora serviço territorial distante.
- Payload tem limite, ordenação, clustering e paginação/estratégia proporcional.
- Google usa field mask mínima, quota, cache permitido e atribuição atual.
- Foto Google não vira binário permanente no Storage.
- Selo SEMTUR é discreto, acessível e não significa certificação.
- Cor não é o único identificador; alvos interativos têm pelo menos 44 dp.
- Testes/CI não chamam SEMTUR, Google ou production.

## 7. Rollback

Migrations aplicadas recebem forward fix; importação é transacional e reexecutável;
associações espaciais são regeneráveis; Google e galeria são feature flags; desligar
Google preserva atores SEMTUR, rota e mídia editorial. Taxonomia antiga permanece
compatível durante janela definida no ADR.
