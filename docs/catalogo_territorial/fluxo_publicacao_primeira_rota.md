# Protocolo e Fluxo de Publicação da Primeira Rota e Região

Versão: 1.0  
Data: 2026-09-05  
Status Normativo: Homologado para esteira de governança  
Referências: ADR 0006 (Governança Editorial e RBAC), ADR 0008 (Mídia e Acessibilidade), ADR 0010 (Taxonomia Canônica), ADR 0015 (Subtipologia) e ECO-2605.

---

## 1. Princípio Fundamental de Publicação Territorial

Nenhuma rota ou região nasce pública no ECOnexão. A ingestão territorial (via pipeline automatizado ou curadoria assistida) cadastra registros invariavelmente nos seguintes estados iniciais de segurança:
- `Route.status`: **`draft`**
- `Route.is_verified`: **`false`**
- `Region.is_active`: **`true`** (visível internamente para indexação, porém sem rotas públicas ativas).

### Regra de Ouro da Região (ADR 0006)
> **Uma região turística só se torna elegível para exibição e navegação pública no aplicativo quando possuir pelo menos 1 rota integralmente homologada, verificada e promovida ao estado `status: published`.**

Caso uma região contenha apenas rotas em `draft` ou `review`, ela permanece oculta do seletor público do aplicativo móvel/web, evitando a exibição de destinos vazios ou incompletos aos viajantes.

---

## 2. Diagrama de Estados do Ciclo de Vida da Rota

```text
               [ Ingestão Inicial / ECO-2605 ]
                              │
                              ▼
                        ┌───────────┐
                        │   draft   │ <── Rota cadastrada tecnicamente
                        └─────┬─────┘
                              │
             (Checklist Seção 8 + Validação Factual)
                              │
                              ▼
                        ┌───────────┐
                        │  review   │ <── Submetida ao Revisor Editorial
                        └─────┬─────┘
                              │
              (Aprovação RBAC: Publisher / Gate H)
                              │
                              ▼
                        ┌───────────┐
                        │ published │ <── Disponível aos usuários no App
                        └───────────┘
```

---

## 3. Requisitos Obrigatórios para Transição de `draft` para `review`

Para que uma rota em rascunho seja elevada ao estado `review`, a equipe editorial ou curadoria deve satisfazer 100% dos seguintes critérios verificáveis:

1. **Ficha Geral Completa:**
   - `route_slug`, `title`, `summary`, `region_slug`, `city` e `state_code` devidamente preenchidos sem marcadores provisórios (*lorem ipsum*).
   - Informações contextuais (`best_season`, `connectivity`, `road_access`, `payment_info`) preenchidas ou explicitadas como `VALOR_AUSENTE`.

2. **Origens Homologadas e Geometrias (WGS84 / CRS 4326):**
   - Ao menos 1 origem cadastrada com coordenadas reais comprovadas de nós de transporte (rodoviária, porto, aeroporto).
   - Geometria viária conectando a origem ao destino com `LineString`, extensão linear (`distance_m`), duração estimada (`duration_s`) e `route_bounds` estrito (sem incluir hospitais ou delegacias urbanas distantes no cálculo de bounds).
   - Arquivo de proveniência rastreável com hash criptográfico SHA-256 verificado.

3. **Taxonomia Canônica dos Atores:**
   - 100% dos atores enquadrados em um dos 8 grupos canônicos protegidos (ADR 0010: `alimentacao`, `atrativos`, `hospedagem`, `artesanato`, `transporte`, `saude`, `seguranca`, `outros`).
   - Subtipos cadastrados conforme o dicionário da ADR 0015.

4. **Preservação de Lacunas e Proibição de Alucinação:**
   - Nenhum campo obrigatório em branco.
   - Campos de contato ou horários sem fonte documental verificada devem estar estritamente demarcados como `VALOR_AUSENTE`.
   - **Zero `google_place_id` inventados** e proibição absoluta de URIs artificiais contendo `cid=`.

5. **Mídia Editorial e Acessibilidade (Publish Guard / ADR 0008):**
   - Imagem de capa da rota (`hero`) cadastrada em `media_assets` com `storage_path` válido.
   - `alt_text` descritivo e acessível (mínimo de 1 frase contextualizando a foto para deficientes visuais).
   - `credit` identificando o fotógrafo ou acervo cedente.
   - `license_code` jurídico declarado (`CC-BY-4.0`, `SEMTUR_INSTITUTIONAL` ou `PROPRIETARY`).
   - Nenhuma foto proveniente do Google Places persistida no storage.

---

## 4. O Gate de Publicação (`review` $ightarrow$ `published`)

A promoção final para `published` é uma ação sensível protegida pelo modelo RBAC (ADR 0006):

1. **Papel Exigido:** Somente identidades autenticadas com a capability `routes:publish` (papel `publisher` ou `admin`) podem alterar o status para `published`.
2. **Registro de Auditoria Imutável:**
   - Ao publicar, a data e hora são registradas em `Route.verified_at` e a flag `Route.is_verified` é comutada para `true`.
   - Um registro é gravado em `app_private.audit_logs` documentando o autor da publicação, o hash do manifesto da rota no momento da aprovação e a justificativa editorial.
3. **Ativação da Região:**
   - Se for a primeira rota publicada da região, a consulta do catálogo passa a retornar a região na lista pública (`/api/v1/regions`).

---

## 5. Salvaguardas Contra Publicação Prematura

Nesta fase (ECO-2605):
- A rota Pindobal permanece em `status: draft` e `is_verified: false` (opera como exemplo de referência técnica).
- A rota fixture Altamira / Xingu permanece em `status: draft` e `is_verified: false` (opera como fixture de testes automatizados).
- Nenhuma chamada de API administrativa ou atualização manual de banco para `status = 'published'` é autorizada sem o preenchimento do checklist editorial humano e a decisão explícita do Owner.
