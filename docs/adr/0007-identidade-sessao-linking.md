# ADR 0007 — Identidade, Sessão Guest, Account Linking e Persistência Web

* **Status:** aceito
* **Data:** 12/08/2026
* **Decisores:** Proprietário do Produto (Owner) / Equipe Antigravity & Codex
* **Task Relacionada:** ECO-1304 (substitui/estende premissas genéricas do ADR 0004)

---

## 1. Contexto e Problema

O aplicativo ECOnexão utiliza a autenticação anônima do Supabase Auth (`signInAnonymously()`) para permitir que usuários naveguem por rotas, atores e salvem favoritos imediatamente sem necessidade de cadastro prévio. Conforme o ADR 0004, o Supabase Auth emite um token JWT com `role: authenticated` e claim `is_anonymous: true`, e todas as tabelas de usuário utilizam RLS estrito baseado em `(select auth.uid()) = user_id`.

No entanto, as seguintes lacunas arquiteturais precisavam de definição normativa formal:
1. **Persistência de Sessão na Plataforma Web (Expo Web):** O cliente web vinha utilizando um mapa em memória. Ao atualizar a página (F5) ou fechar a aba, o estado de autenticação era perdido e um novo `user_id` anônimo era gerado, orfanando os dados da sessão anterior.
2. **Account Linking (Guest → Conta Identificada):** O fluxo de transição de uma conta anônima para uma conta permanente via e-mail/senha ou OAuth.
3. **Resolução de Conflitos de Identidade:** O comportamento quando um usuário guest tenta vincular um e-mail que já possui conta ativa no Supabase.
4. **Ciclo de Vida de Contas Anônimas Órfãs:** Retenção e expurgo de dados de sessões anônimas abandonadas (conformidade LGPD).
5. **Validação de Tokens no FastAPI:** Estratégia de validação dos tokens JWT no backend de domínio.

---

## 2. Opções Analisadas

### 2.1 Persistência de Sessão na Web
* **Opção A (In-Memory Pure):** Mantém tokens apenas em memória JS. Imune a XSS, mas invalida a sessão no F5 (UX inaceitável).
* **Opção B (`localStorage` com Refresh Token Rotation - ESCOLHIDA):** Persiste os tokens no `localStorage` do navegador via chave isolada no cliente Supabase. Mitiga XSS via Content Security Policy (CSP) estrita e expiração curta do Access Token (15 min) com rotação automática de Refresh Tokens.
* **Opção C (Web BFF com Cookies `HttpOnly`):** Exige servidor proxy dedicado para gerenciar cookies de sessão. Segurança máxima, porém alto custo de infraestrutura e complexidade de integração com Expo Router Web.

### 2.2 Resolução de Conflito em Account Linking
* **Opção 1 (Rejeição Informativa "Fazer Login" - ESCOLHIDA PARA MVP):** Quando um guest tenta vincular um e-mail já existente em outra conta, o aplicativo rejeita a vinculação direta, avisa o usuário que o e-mail já possui cadastro e oferece botão para logar na conta existente. Zera o risco de contaminação inadvertida de dados entre contas.
* **Opção 2 (Fusão de Dados Server-Side `POST /me/merge-guest-data`):** O backend reatribui o `user_id` dos favoritos/viagens da conta anônima para a conta existente após validação de senha de ambas. Excelente UX, mas complexidade moderada (postergada para ciclo pós-MVP).

---

## 3. Decisão

Fica formalmente decidido que:

1. **Persistência Multi-Plataforma:**
   - **Mobile (iOS/Android):** O Supabase Auth utilizará `expo-secure-store` (iOS Keychain / Android EncryptedSharedPreferences).
   - **Web (Expo Web):** O Supabase Auth utilizará `localStorage` com rotação automática de Refresh Tokens e Access Tokens com validade máxima de 15 minutos.
2. **Account Linking (Guest → Conta Identificada):**
   - A vinculação de e-mail/senha em conta anônima ativa será feita via `supabase.auth.updateUser({ email, password })`. O Supabase Auth preserva o mesmo `UUID` (`user_id`), garantindo continuidade total de favoritos e viagens sem necessidade de migração SQL.
3. **Resolução de Conflitos (MVP):**
   - Conflitos de e-mail já cadastrado serão tratados pela **Opção 1 (Rejeição com Alternativa de Login)**. Se o usuário escolher logar na conta antiga, os favoritos anônimos locais da sessão atual são descartados, assumindo o perfil da conta autenticada.
4. **Ciclo de Vida e Expurgo de Guests (LGPD):**
   - Contas anônimas sem e-mail cadastrado que permanecerem inativas por mais de **90 dias** serão permanentemente excluídas por um job agendado assíncrono no FastAPI/Supabase Admin API, aplicando exclusão em cascata nas tabelas de domínio (`profiles`, `user_preferences`, `favorite_routes`, `favorite_actors`, `trips`).
5. **Validação de JWT no Backend FastAPI:**
   - O FastAPI validará o cabeçalho `Authorization: Bearer <access_token>` de forma assíncrona em memória via verificação de assinatura RS256/JWKS (ou HS256 em ambiente de testes), verificando emissor, audiência e expiração sem realizar chamadas HTTP de rede por requisição ao Supabase.

---

## 4. Consequências e Reversibilidade

### Vantagens:
* **UX Web Corrigida:** Usuários na Web não perdem a sessão ou favoritos ao pressionar F5.
* **Segurança e Isolamento:** Nenhuma contaminação de dados entre contas no MVP.
* **Conformidade LGPD:** Expurgo automático de contas fantasma reduz pegada de dados e custos de banco.
* **Baixa Latência no Backend:** Validação criptográfica de JWT em memória no FastAPI sem gargalo de I/O.

### Riscos e Mitigações:
* **Risco de Leitura de `localStorage` por XSS na Web:** Mitigado por Content Security Policy (CSP) estrita, sanitização de inputs React e Refresh Token Rotation no Supabase Auth.
* **Perda de Favoritos Guest em Colisão de E-mail:** Mitigado por alerta claro na UI informando a situação antes do usuário confirmar a troca de conta.

### Reversibilidade:
* **Alta:** A migração para fusão server-side de dados (Opção 2) pode ser introduzida em ciclo futuro via endpoint `/api/v1/me/merge-guest-data` sem quebrar o esquema atual.
