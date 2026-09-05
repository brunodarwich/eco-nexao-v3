# Guia de Preenchimento — Pacote de Dados e Revisão Editorial de Novas Rotas

Versão: 1.0  
Data: 2026-09-05  
Público-alvo: Equipe de Produto ECOnexão, Curadoria Editorial e Assistentes de IA

---

## 1. Visão Geral e Propósito

Este guia orienta o levantamento, a organização documental e a revisão editorial de cada nova rota turística a ser incluída no ecossistema ECOnexão (como as próximas rotas do polo Santarém: Praia do Amor, Vila Socorro, Ponta de Pedras, Eramanai, e as 5 rotas do polo Altamira).

O objetivo é assegurar que todas as informações necessárias para a exibição no aplicativo e a ingestão no banco PostgreSQL/PostGIS cheguem estruturadas, íntegras, auditáveis e livres de alucinações ou infrações de termos de serviço de terceiros.

---

## 2. Passo a Passo do Processo Editorial

O fluxo de inclusão de uma nova rota divide-se em 6 etapas sequenciais:

```text
[1. Coleta Bruta & Origens] ──> [2. Geometria & Trajeto] ──> [3. Catalogação de Atores]
                                                                        │
[6. Ingestão & Publicação] <── [5. Checklist & Assinatura] <── [4. Mídia & Tags]
```

### Etapa 1: Definição da Ficha Geral e Origens
1. Crie uma cópia do arquivo `docs/data/route_data_package_template.md` nomeando-a como `docs/data/{slug_da_rota}_route_package.md`.
2. Defina o `route_slug` em formato minúsculo e hifenizado (ex: `rota-praia-do-amor`).
3. Cadastre a região (`region_slug`) e o município polo (`city`).
4. Identifique as **origens homologadas de saída** (mínimo de 1 origem, recomendando 2 a 3 pontos reais de chegada de turistas: aeroporto, porto/terminal fluvial, rodoviária ou centro da cidade).
5. Obtenha as coordenadas geográficas exatas (`latitude`, `longitude`) de cada origem em formato decimal WGS84.

### Etapa 2: Obtenção e Verificação da Geometria da Rota
1. A rota precisa de uma geometria viária ou fluvial real conectando cada ponto de origem ao destino final.
2. A geometria deve ser expressa em `LineString` com coordenadas `(longitude, latitude)` em CRS 4326.
3. Obtenha a extensão linear total (`distance_m`) e duração estimada (`duration_s`).
4. Calcule o `route_bounds` estrito (bounding box do trajeto `[minLng, minLat, maxLng, maxLat]`). Não inclua hospitais ou serviços municipais distantes no cálculo de bounds da rota (evita distorção de zoom na tela inicial).
5. Armazene o arquivo fonte da geometria (CSV ou GeoJSON) no diretório de dados correspondente e anote o seu hash SHA-256 no pacote da rota.

### Etapa 3: Catalogação e Classificação dos Atores
1. Mapeie os estabelecimentos turísticos, produtores e pontos de apoio ao longo do trajeto (dentro da faixa de 1.000m do corredor viário) e os serviços essenciais da cidade polo.
2. Para cada estabelecimento, enquadre obrigatoriamente em:
   - **Um dos 8 grupos canônicos protegidos (ADR 0010):** `alimentacao`, `atrativos`, `hospedagem`, `artesanato`, `transporte`, `saude`, `seguranca`, `outros`.
   - **Um subtipo específico controlado (ADR 0015):** ex: `barraca_praia`, `pousada_hotel`, `artesanato_local`, `posto_combustivel`, `hospital_upa`.
   - **Um escopo espacial definido (ADR 0011):**
     - `route_corridor`: estabelecimentos de lazer/estrada que pertencem ao corredor da rota;
     - `citywide_essential`: serviços de socorro médico e segurança pública localizados na malha da cidade;
     - `both`: modais de transporte, postos de combustível e mercados que atendem ambos os contextos.
3. Se o estabelecimento constar em inventário municipal oficial (ex: SEMTUR Santarém ou Secretaria de Altamira), anote o identificador da fonte e marque `is_semtur_inventory: true`.

### Etapa 4: Contatos, Mídia Editorial e Tags de Experiência
1. Preencha contatos reais auditados: telefone comercial (formatado preferencialmente em E.164), e-mail válido, site institucional e Instagram.
2. Atribua **tags de experiência** pertinentes (ex: `por-do-sol`, `banho-de-rio`, `trilha-ecologica`, `culinaria-regional`, `domingo-em-familia`), sempre registrando a justificativa concreta e o responsável pela checagem.
3. Defina a imagem de capa da rota (`hero`) e mídias principais dos atores:
   - Toda imagem precisa de `alt_text` descritivo, rico e acessível (mínimo de 1 frase explicando o conteúdo visual da foto para leitores de tela);
   - Crédito nominal do autor ou acervo institucional cedente;
   - Licença jurídica clara (`SEMTUR_INSTITUTIONAL`, `CC-BY-4.0` ou `PROPRIETARY`).

### Etapa 5: Checklist de Auditoria e Aprovação Editorial
1. O revisor humano responsável ou IA de curadoria confere item a item do checklist da Seção 8 do template.
2. Assegure que nenhum campo ausente foi preenchido com dados hipotéticos ou falsos.
3. O responsável assina com seu nome, papel RBAC (`editor`/`publisher`) e data de revisão.

### Etapa 6: Submissão para Ingestão Técnica
1. O pacote aprovado é submetido ao pipeline de ingestão do backend (`backend/app/ingestion`).
2. A ingestão executa `--dry-run` para comprovação de integridade, contagens e geração de relatório antes de qualquer escrita no banco de dados.

---

## 3. Regras Críticas e O Que NUNCA Fazer

> [!CAUTION]
> **Proibição Absoluta de Invenção de Dados:**
> Se uma pousada, restaurante ou atrativo não possuir telefone, site ou horário conhecido, marque expressamente `VALOR_AUSENTE`. **Nunca gere dados fictícios ou estimativas sem confirmação.**

> [!WARNING]
> **Proibição de Inventar Google Place IDs e URLs Artificiais:**
> Nunca infira ou gere um `place_id` a partir da URL do Google Maps, de strings aleatórias ou de nomes. O `place_id` só pode ser preenchido se vier de uma coleta oficial ponta a ponta da Places API (New). Caso contrário, preencha obrigatoriamente `VALOR_AUSENTE`.
> É igualmente **proibido gerar URIs artificiais com `cid=`** ou registrar avaliações/ratings do Google sem Place ID comprovado por conector.

> [!CAUTION]
> **Rigor em `source_location` e Atribuição SEMTUR:**
> Nunca use `source_location: google_places` sem evidência de coleta autorizada ponta a ponta. Registros legados sem chave devem ser marcados com sua fonte real (ex: `snapshot_infraestrutura_legado` ou `semtur_inventory`).
> O selo `is_semtur_inventory: true` exige referência concreta (página ou ID) no inventário oficial. Sem vínculo comprovado, marque `is_semtur_inventory: false`.

> [!NOTE]
> **Omissão de Tags Incompatíveis:**
> Tags de experiência não aplicáveis a um determinado tipo de ator (ex: gastronomia em pousada sem restaurante ou artesanato) devem ser **omitidas**, e nunca cadastradas com valores 'não aplicável' ou 'VALOR_AUSENTE'.

> [!WARNING]
> **Vedação de Download de Mídia Google:**
> É estritamente proibido baixar fotos da Google Places API e colocá-las no repositório ou no Supabase Storage. As fotos do Google são servidas exclusivamente sob demanda via proxy efêmero em memória pelo backend FastAPI (ADR 0016).

> [!IMPORTANT]
> **Selo SEMTUR Não é Certificação:**
> O selo `SEMTUR` / `Inventário SEMTUR` é um indicador neutro de proveniência pública de que o local consta no cadastro municipal. Ele nunca deve ser apresentado como "certificado", "garantido" ou "fiscalizado" pela prefeitura (ADR 0014).

---

## 4. Dicionário Rápido de Status e Valores

- `status_coord`:
  - `ok`: Coordenada geográfica validada em mapa satélite/campo dentro dos limites municipais.
  - `ausente`: Coordenada desconhecida (o registro não é publicado no mapa, ficando restrito a catálogo textual ou rascunho de triagem).
  - `inconsistente`: Coordenada conflitante (ex: estabelecimento em Alter do Chão com ponto caindo no centro urbano de Santarém).
- `license_code`:
  - `SEMTUR_INSTITUTIONAL`: Imagem cedida pelo poder público municipal para fomento turístico.
  - `CC-BY-4.0`: Mídia de uso livre sob licença Creative Commons com atribuição ao fotógrafo.
  - `PROPRIETARY`: Mídia própria da ECOnexão ou com cessão direta de direitos de uso pelo estabelecimento parceiro.
- `evidence_type` (Tags de Experiência):
  - `inspecao_em_campo`: Verificado presencialmente pela equipe.
  - `declaracao_institucional`: Constando em documento descritivo oficial da SEMTUR.
  - `analise_geografica`: Comprovado por orientação solar/azimute, proximidade fluvial ou relevo.
