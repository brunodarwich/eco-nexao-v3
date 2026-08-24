# ADR 0004 — Decisões de Produto para Autenticação, Telas e Infraestrutura

Status: aceito  
Data: 12/08/2026

## Contexto

A integração do backend do ECOnexão exige definições formais para o fluxo de identidade do usuário, o comportamento dos selos ambientais, a navegação para detalhes de atores turísticos e a arquitetura de hospedagem dos serviços.

## Decisões

### 1. Autenticação e Gestão de Identidade (ECO-0601)
- O aplicativo adotará o **Anonymous Sign-in do Supabase Auth** para a criação imediata de sessão na primeira inicialização.
- Toda ação do usuário (favoritos, preferências, histórico de viagens) será associada ao `user_id` único fornecido pelo Supabase Auth.
- No futuro, a conta anônima poderá ser vinculada (*identity linking*) a um endereço de e-mail ou provedor social sem perda de histórico.
- Usuários anônimos também utilizam o papel Postgres `authenticated`, devendo o isolamento de dados ser garantido estritamente via `(select auth.uid()) = user_id` nas políticas RLS do Supabase.

### 2. Suporte a Plataformas
- O aplicativo oferece suporte completo às plataformas **Android, iOS e Web**, mantendo o Expo SDK 54 como referência técnica normativa conforme o ADR 0001.

### 3. Comportamento do Selo Consciente

Substituído pelo ADR 0009. O produto não possui selo pessoal nem impacto ecológico
calculado para o usuário. Selos territoriais editoriais de atores/rotas permanecem
separados e preservados.

### 4. Formato e Navegação do Detalhe do Ator (ECO-1002)
- O detalhe de um ator turístico terá duas formas de apresentação integradas:
  1. **Bottom Sheet no Mapa**: Resumo rápido de informações (nome, categoria, foto, botões de ação rápida para rota e ligação).
  2. **Tela Dedicada (`/actor/[actorId]`)**: Visualização completa acessível via deep link contendo galeria de fotos, horários de funcionamento (JSONB), contatos (telefone, site, Instagram), mapa de localização, selos de acessibilidade e proveniência pública dos dados.

### 5. Provedores de Hospedagem e Serviços
- **Backend API**: FastAPI em Python 3.13 executando em ambiente de contêineres gerenciados.
- **Banco de Dados**: Supabase PostgreSQL 17 gerenciado com a extensão PostGIS ativada.
- **Autenticação**: Supabase Auth (JWT).
- **Armazenamento de Mídia**: Supabase Storage com buckets separados para `avatars` e `editorial-media`.

## Consequências

- Nenhuma funcionalidade de usuário dependerá de armazenamento local volátil ou mock global.
- Todas as rotas do FastAPI verificarão a validade do JWT Supabase antes de autorizar mutações de usuário.
- O schema do banco de dados e as políticas RLS garantem conformidade com LGPD e isolamento completo entre contas.
