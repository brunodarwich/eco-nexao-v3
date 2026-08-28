# Plano — higiene e saúde do repositório

Status: `PROPOSED`

## Sequência

```text
ECO-2401 -> ECO-2402 -> ECO-2403 -> ECO-2404 -> ECO-2405
                                      |             |
                                      +-> ECO-2406 -+
                                      +-> ECO-2407 -+
                                                     -> ECO-2408 -> ECO-2409 -> ECO-2410
```

`ECO-2405`, `ECO-2406` e `ECO-2407` podem ser avaliadas separadamente depois da
baseline documental, mas não devem editar os mesmos arquivos em paralelo.

## Gates

- **H24.1 — baseline protegida:** alterações locais identificadas, testes possíveis
  registrados e ponto de retorno Git definido sem sobrescrever trabalho.
- **H24.2 — classificação aprovada:** owner aprova a matriz manter/arquivar/remover
  antes de qualquer remoção material.
- **H24.3 — consumidores provados:** busca estática, configuração de CI/deploy e
  documentação não indicam consumidor do legado proposto.
- **H24.4 — regressão verde:** testes proporcionais e revisão independente aprovam
  cada remoção ou consolidação.

## Princípios

1. Arquivar antes de apagar quando houver valor histórico.
2. Separar mudança documental, limpeza gerada e remoção de código em commits distintos.
3. Não alterar comportamento do produto em uma task de higiene.
4. Não remover dados OSRM importados ao remover o runtime OSRM.
5. Migrations individuais continuam sendo a única fonte normativa do schema.
6. Evidência formal é selecionada; saída bruta regenerável não é documentação.
7. Finding P0/P1 ou teste obrigatório falho reabre implementação e invalida conclusão.

## Rollback

- documentação: restauração por Git e manutenção de redirects/índices;
- artefatos: regeneração pelo comando documentado;
- código/configuração: revert do commit isolado;
- assets: restauração da cópia canônica por checksum;
- nenhuma task promete rollback de dados remotos ou migrations destrutivas.

