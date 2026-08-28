# ADR 0008 — Política de Mídia, Armazenamento, Privacidade e Direitos Autorais

* **Status:** aceito
* **Data:** 12/08/2026
* **Decisores:** Proprietário do Produto (Owner) / Equipe Antigravity & Codex
* **Task Relacionada:** ECO-1305

---

## 1. Contexto e Problema

O aplicativo ECOnexão lida com três classes principais de mídias visuais:
1. **Avatares de Usuário:** Fotos de perfil enviadas por usuários anônimos ou autenticados.
2. **Mídia Editorial Territorial:** Fotos de rotas, origens, pontos de interesse, patrimônio natural e atores do turismo ecológico oriundas de acervos próprios, parceiros comunitários ou órgãos oficiais (SEMTUR).
3. **Mídias de Conectores Terceiros (Google Places API):** Fotografias originadas da Places API do Google Maps Platform.

Estas mídias demandavam definição estrita quanto a isolamento de privacidade (LGPD), proteção contra overwrites/BOLA no Supabase Storage, otimização de banda móvel no Expo React Native, governança de direitos autorais (Lei nº 9.610/98), acessibilidade universal (leitores de tela) e regras de retenção/exclusão.

---

## 2. Decisão

Fica formalmente decidido que:

1. **Topologia e Visibilidade dos Buckets no Supabase Storage:**
   - `avatars` (Público; Leitura livre; Upload/Update/Delete restrito ao próprio usuário via RLS `(select auth.uid())::text = (storage.foldername(name))[1]` sob o caminho `{user_id}/avatar_{timestamp}.webp`).
   - `editorial-media` (Público; Leitura irrestrita via Supabase CDN; Mutações restritas exclusivamente ao backend FastAPI validando os papéis RBAC `editor` ou `publisher` do ADR 0006).
   - `raw-ingestion` (Privado; Acesso exclusivo do backend FastAPI via `service_role` para staging de mídias brutas da ingestão Pindobal).

2. **Sanitização EXIF e Privacidade LGPD:**
   - **Remoção de Metadados:** Todo upload de avatar ou mídia editorial passará por sanitização server-side (ou pre-upload) obrigatória no FastAPI, eliminando 100% das tags EXIF/GPS, modelo do aparelho e data da foto antes de salvar o binário no Storage.
   - **Dados Espaciais:** Caso a localização geográfica da fotografia seja relevante para o catálogo territorial, ela deve ser cadastrada explicitamente na coluna espacial PostGIS da tabela `media_assets`, e nunca mantida oculta no arquivo binário.

3. **Geração de Derivados Imutáveis (Thumbnails):**
   - O backend FastAPI gerará automaticamente três variantes compactadas em formato **WebP** otimizado para cada mídia:
     - `thumb` (150x150 px): Para avatares, listas e pins do mapa.
     - `card` (600x400 px): Para cards de feed de rotas e atores.
     - `hero` (1200x800 px): Para cabeçalhos da tela de detalhes.
   - Os arquivos serão armazenados com URLs públicas CDN contendo hash no nome (`Cache-Control: public, max-age=31536000, immutable`).

4. **Direitos Autorais e Regra para Fotos do Google Places API:**
   - **Vedação de Download Google:** É **estritamente proibido** baixar, copiar ou armazenar binários de fotos do Google Places API nos buckets do Supabase Storage (violação dos termos do Google Maps Platform).
   - **Proxy sem persistência:** Esta redação é substituída pela correção normativa do ADR 0016: `photos[].name`, URLs de mídia, `flagContentUri` e atribuições são mantidos somente no grant opaco em memória, de uso único e vida curta. Não há cache, coluna ou licença `GOOGLE_PLACES_PROXY` em `media_assets`.
   - **Licenciamento de Conteúdo:** Toda mídia editorial deve ter sua licença explicitada em `media_assets.license_code` (`CC-BY-4.0`, `SEMTUR_INSTITUTIONAL` ou `PROPRIETARY`).

5. **Acessibilidade e Publish Guard:**
   - Toda mídia em `media_assets` exige `alt_text TEXT NOT NULL` e `credit TEXT NOT NULL`.
   - **Publish Guard (ADR 0006):** O FastAPI rejeitará a publicação (`published`) de qualquer rota ou ator cujas mídias associadas possuam `alt_text` vazio ou genérico. O aplicativo Expo renderizará obrigatoriamente `accessibilityLabel={media.alt_text}`.

6. **Retenção, Exclusão e Limpeza de Órfãos:**
   - **Exclusão de Avatar:** A exclusão de conta apaga imediatamente o binário do avatar no Supabase Storage (Hard Delete).
   - **Soft Delete Editorial:** Mídias editoriais removidas entram em quarentena por 30 dias (`deleted_at`).
   - **Expurgo de Órfãos:** Um job agendado assíncrono expurga definitivamente do Storage os binários sem registro correspondente em `media_assets`.

---

## 3. Consequências e Reversibilidade

### Vantagens:
* **Conformidade LGPD e Termos Google:** Zera o risco de vazamento de localização via EXIF e elimina violação de licenças do Google Places.
* **Performance Móvel:** Redução extrema do consumo de dados via WebP derivados (`thumb`/`card`/`hero`).
* **Acessibilidade Incondicional:** Garante suporte a leitores de tela em 100% das imagens publicadas.

### Reversibilidade:
* **Alta:** Ajustes em limites de tamanho ou inclusão de novos formatos (ex: AVIF) podem ser feitos no FastAPI sem alterar as tabelas de banco.
