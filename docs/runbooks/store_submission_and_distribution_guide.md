# Guia: Submissão para Google Play, App Store e Distribuição PWA (ECO-2204)

Este guia estabelece os requisitos, metadados, comandos e procedimentos normativos para homologação e publicação dos pacotes do aplicativo móvel **ECOnexão** no Google Play Console, Apple App Store Connect e canais web PWA.

---

## 1. Identificadores de Pacote e Versão

- **Nome Oficial:** ECOnexão
- **Versão:** `1.0.0`
- **Build / Version Code:** `1`
- **Package Name (Android):** `org.econexao.app`
- **Bundle Identifier (iOS):** `org.econexao.app`
- **Scheme Customizado:** `econexao://`
- **URL Base Universal:** `https://econexao.app`

---

## 2. Geração de Artefatos de Build Homologados

### 2.1. Android (AAB / APK Assinado)
Para geração do Android App Bundle (AAB) para a Play Store:
```bash
cd econexao-app
# Build via EAS (Cloud / Local)
eas build --platform android --profile production
```
*Critério:* O arquivo gerado deve conter target SDK 34+ e assinatura com chave protegida no cofre de credenciais EAS/Google Play.

### 2.2. iOS (IPA / TestFlight)
Para compilação e submissão ao TestFlight / App Store:
```bash
cd econexao-app
eas build --platform ios --profile production
```
*Critério:* Provisioning profile e certificados de distribuição gerenciados e assinados.

### 2.3. Web PWA / Estático
Para compilação da versão Web:
```bash
cd econexao-app
npm run build:web
```

---

## 3. Checklist de Metadados e Conformidade nas Lojas

### 3.1. Google Play Console
- [x] **Nome do App:** ECOnexão
- [x] **Descrição Curta:** Descubra rotas ecológicas, atores locais e turismo sustentável.
- [x] **Categoria:** Viagens e Locais / Estilo de Vida
- [x] **Classificação de Conteúdo:** Livre / Todos
- [x] **Data Safety (Segurança dos Dados):**
  - Dados Coletados: Localização aproximada e precisa (somente em uso ativo, opcional para navegação e cálculo de distância).
  - Dados do Usuário: Nome e e-mail (para login e sincronização de favoritos).
  - Criptografia em trânsito: Sim (HTTPS/TLS 1.3 obrigatório).
  - Exclusão de Conta e Dados: Sim (Suportado via app e endpoint `/api/v1/auth/account/delete`).
- [x] **URL da Política de Privacidade:** `https://econexao.app/privacy`
- [x] **Declaração de Acessibilidade:** Conformidade WCAG 2.1 AA documentada.

### 3.2. Apple App Store Connect
- [x] **App Name:** ECOnexão
- [x] **Subtitle:** Turismo Sustentável e Rotas Locais
- [x] **Privacy Nutrition Labels:**
  - *Location:* Utilizada para funcionalidade do app (mapa de rotas).
  - *Contact Info:* E-mail para gerenciamento de conta.
  - *Identifiers:* User ID para sessão autenticada.
  - *Tracking:* Nenhum dado é utilizado para rastreamento de terceiros (Zero ad-trackers).
- [x] **TestFlight:** Canal de teste interno para equipe e beta testers convidados.

---

## 4. Política de Rollout Gradual

1. **Dia 1:** Liberação para 10% dos usuários (Monitoramento ativo de crashes e latência).
2. **Dia 2:** Expansão para 25%.
3. **Dia 3:** Expansão para 50%.
4. **Dia 4:** Liberação para 100% da base.

### Procedimento de Interrupção de Rollout:
Caso a taxa de falha (Crashlytics/Play Console) exceder 0.2%, pausar imediatamente a liberação no console e acionar o runbook de resposta a incidentes.
