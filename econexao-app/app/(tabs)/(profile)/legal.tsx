import React, { useState, useEffect, useRef } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  AccessibilityInfo,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as Linking from 'expo-linking';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { AccessibleModal } from '../../../src/components/common/AccessibleModal';
import { useAppTheme } from '../../../src/theme/theme';
import { makeAccessibleButton, makeAccessibleHeader } from '../../../src/utils/accessibility';
import {
  hasValidLocationConsent,
  revokeLocationConsent,
  CURRENT_LOCATION_POLICY_VERSION,
} from '../../../src/auth/locationConsent';

export default function LegalAndPrivacyScreen() {
  const router = useRouter();
  const theme = useAppTheme();
  const [hasConsent, setHasConsent] = useState(false);
  const [isCheckingConsent, setIsCheckingConsent] = useState(true);
  const [isRevokeModalOpen, setIsRevokeModalOpen] = useState(false);
  const [revokeError, setRevokeError] = useState<string | null>(null);
  const [isRevoking, setIsRevoking] = useState(false);

  const revokeButtonRef = useRef<any>(null);
  const modalTitleRef = useRef<any>(null);
  const retryButtonRef = useRef<any>(null);

  useEffect(() => {
    let isMounted = true;
    void (async () => {
      const valid = await hasValidLocationConsent();
      if (isMounted) {
        setHasConsent(valid);
        setIsCheckingConsent(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleOpenRevokeModal = () => {
    setRevokeError(null);
    setIsRevokeModalOpen(true);
  };

  const handleCloseRevokeModal = () => {
    if (isRevoking) return;
    setIsRevokeModalOpen(false);
    setRevokeError(null);
    AccessibilityInfo.announceForAccessibility('Revogação cancelada. Consentimento mantido.');
  };

  const handleConfirmRevoke = async () => {
    setIsRevoking(true);
    setRevokeError(null);
    try {
      const success = await revokeLocationConsent();
      if (success) {
        setHasConsent(false);
        setIsRevokeModalOpen(false);
        AccessibilityInfo.announceForAccessibility(
          'Consentimento de localização revogado com sucesso. O aplicativo utilizará exclusivamente origens fixas homologadas.'
        );
      } else {
        setRevokeError('Não foi possível revogar o consentimento no armazenamento local. Tente novamente.');
        AccessibilityInfo.announceForAccessibility(
          'Erro ao revogar consentimento no armazenamento local. Tente novamente.'
        );
      }
    } catch {
      setRevokeError('Não foi possível revogar o consentimento no armazenamento local. Tente novamente.');
      AccessibilityInfo.announceForAccessibility(
        'Erro ao revogar consentimento no armazenamento local. Tente novamente.'
      );
    } finally {
      setIsRevoking(false);
    }
  };

  const handleOpenGoogleTerms = () => {
    void Linking.openURL('https://maps.google.com/help/terms_maps/');
  };

  const handleOpenGooglePrivacy = () => {
    void Linking.openURL('https://policies.google.com/privacy');
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surfaceBackground }]}>
      <AppHeader showBack onBackPress={() => router.back()} title="Termos & Privacidade" />

      <ScrollView contentContainerStyle={styles.content}>
        {/* Aviso de Pré-Publicação */}
        <View style={[styles.preReleaseNoticeCard, { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' }]}>
          <View style={styles.noticeHeader}>
            <Ionicons name="information-circle" size={20} color="#B45309" />
            <Text style={[styles.noticeTitle, { color: '#92400E' }]}>
              Versão em Desenvolvimento / Pré-Publicação
            </Text>
          </View>
          <Text style={[styles.noticeText, { color: '#92400E' }]}>
            Esta política reflete as regras aprovadas pelo proprietário do projeto (04/09/2026) para desenvolvimento local e validação. Os dados de identificação cadastral formal do controlador estão pendentes de preenchimento antes da publicação final em produção.
          </Text>
        </View>

        {/* Política de Localização Dinâmica e Rotas */}
        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.25)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="navigate-circle" size={22} color={theme.colors.brandForest} />
            <Text
              {...makeAccessibleHeader('Política de Privacidade de Localização e Rotas', 2)}
              style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
            >
              Política de Localização e Rotas
            </Text>
          </View>

          <View style={styles.metaRow}>
            <Text style={[styles.metaBadge, theme.typography.labelSm, { color: theme.colors.brandForest }]}>
              Versão: {CURRENT_LOCATION_POLICY_VERSION}
            </Text>
            <Text style={[styles.metaBadge, theme.typography.labelSm, { color: theme.colors.onSurfaceVariant }]}>
              Status: Aprovada pelo Owner e responsável jurídico
            </Text>
          </View>

          {/* Controlador */}
          <Text style={[styles.subSectionTitle, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
            Identificação do Controlador
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            • Controlador: [PREENCHER ANTES DA PUBLICAÇÃO]{'\n'}
            • CPF/CNPJ: [PREENCHER ANTES DA PUBLICAÇÃO]{'\n'}
            • Endereço: [PREENCHER ANTES DA PUBLICAÇÃO]{'\n'}
            • Contato do Encarregado (DPO): privacidade@econexao.app
          </Text>

          {/* Finalidade e Dados */}
          <Text style={[styles.subSectionTitle, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
            Finalidade Exclusiva e Dados Tratados
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            O tratamento de localização destina-se exclusivamente a calcular e desenhar o trajeto rodoviário sugerido até a rota escolhida. Os dados tratados temporariamente são latitude, longitude da origem (via GPS ou seleção no mapa), destino oficial e perfil de condução (DRIVE).
          </Text>

          {/* Zero Persistência e Segurança */}
          <Text style={[styles.subSectionTitle, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
            Segurança, Transporte e Descarte (Zero Persistência)
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            As coordenadas trafegam criptografadas exclusivamente no corpo (POST body) de requisições HTTPS. O ECOnexão não persiste coordenadas em banco de dados, nem as registra em arquivos de log, URLs ou métricas. Os dados são mantidos apenas em memória volátil e descartados imediatamente após o cálculo ou erro.
          </Text>

          {/* Proibições Absolutas */}
          <Text style={[styles.subSectionTitle, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
            Vedações Absolutas
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            É terminantemente vedado o rastreamento contínuo em segundo plano, perfilamento comercial ou publicidade comportamental com base na sua localização.
          </Text>

          {/* Compartilhamento Google */}
          <Text style={[styles.subSectionTitle, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
            Compartilhamento com a Google Routes API
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            Para calcular o trajeto sugerido, as coordenadas são enviadas de servidor para servidor à Google Routes API (ComputeRoutes Essentials). O processamento sujeita-se aos termos do Google e pode envolver transferência internacional de dados para essa finalidade específica.
          </Text>

          <View style={styles.linkGroup}>
            <TouchableOpacity
              style={styles.externalLinkRow}
              onPress={handleOpenGoogleTerms}
              {...makeAccessibleButton('Termos Adicionais do Google Maps')}
              accessibilityRole="link"
            >
              <Ionicons name="open-outline" size={16} color={theme.colors.brandForest} />
              <Text style={[styles.linkText, { color: theme.colors.brandForest }]}>
                Termos Adicionais do Google Maps
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.externalLinkRow}
              onPress={handleOpenGooglePrivacy}
              {...makeAccessibleButton('Política de Privacidade do Google')}
              accessibilityRole="link"
            >
              <Ionicons name="open-outline" size={16} color={theme.colors.brandForest} />
              <Text style={[styles.linkText, { color: theme.colors.brandForest }]}>
                Política de Privacidade do Google
              </Text>
            </TouchableOpacity>
          </View>

          {/* Restrição de Maioridade */}
          <Text style={[styles.subSectionTitle, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
            Restrição Etária (18+)
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            A utilização da localização dinâmica é restrita a maiores de 18 anos. Menores de 18 anos podem utilizar plenamente todas as funcionalidades do aplicativo por meio das origens fixas oficiais verificadas (Porto, Aeroporto e Rodoviária).
          </Text>

          {/* Gestão e Revogação do Consentimento */}
          <Text style={[styles.subSectionTitle, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
            Gerenciamento do Seu Consentimento
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            Seu consentimento é registrado de forma estritamente local no seu dispositivo, sem armazenar dados pessoais ou coordenadas. Se uma nova versão material da política for lançada, um novo aceite será solicitado.
          </Text>

          {!isCheckingConsent && (
            <View style={styles.consentStatusCard}>
              <View style={styles.consentStatusRow}>
                <Ionicons
                  name={hasConsent ? 'checkmark-circle' : 'close-circle'}
                  size={18}
                  color={hasConsent ? theme.colors.success : theme.colors.onSurfaceVariant}
                />
                <Text style={[styles.consentStatusText, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
                  {hasConsent
                    ? 'Consentimento de localização ativo neste dispositivo'
                    : 'Nenhum consentimento de localização ativo neste dispositivo'}
                </Text>
              </View>

              {hasConsent && (
                <TouchableOpacity
                  ref={revokeButtonRef}
                  style={[styles.revokeButton, { borderColor: theme.colors.error }]}
                  onPress={handleOpenRevokeModal}
                  {...makeAccessibleButton(
                    'Revogar consentimento de localização dinâmica',
                    'Abre diálogo de confirmação para revogar o consentimento local e restaurar o uso exclusivo de origens fixas'
                  )}
                >
                  <Ionicons name="trash-outline" size={16} color={theme.colors.error} />
                  <Text style={[styles.revokeButtonText, { color: theme.colors.error }]}>
                    Revogar Consentimento de Localização
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <Text
            {...makeAccessibleHeader('Termos de Uso Comunitário', 2)}
            style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
          >
            Termos de Uso Comunitário
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            O ECOnexão é uma plataforma comunitária aberta destinada a promover o ecoturismo sustentável, a valorização dos negócios locais e a preservação ambiental no polo turístico Tapajós-Arapiuns (Belterra, Santarém e região).
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            Todas as rotas, trilhas e pontos de interesse listados são mantidos colaborativamente com a curadoria editorial da SEMTUR e lideranças locais. O usuário compromete-se a respeitar as diretrizes de não deixar rastros, conservação da fauna e flora e valorização das comunidades tradicionais.
          </Text>
        </View>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <Text
            {...makeAccessibleHeader('Privacidade Geral e LGPD', 2)}
            style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
          >
            Privacidade Geral e LGPD
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            O ECOnexão trata dados pessoais de acordo com os princípios e direitos previstos na Lei Geral de Proteção de Dados (Lei nº 13.709/2018 - LGPD).
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            • Navegação Anônima: Você pode utilizar o aplicativo sem fornecer e-mail ou dados pessoais.
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            • Coleta Mínima: Apenas armazenamos suas preferências de acessibilidade e lista de favoritos para personalizar sua experiência.
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            • Direito à Exclusão: Você pode solicitar a exclusão de sua conta a qualquer momento diretamente pelo seu perfil, resultando na imediata desvinculação dos seus dados pessoais.
          </Text>
        </View>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <Text
            {...makeAccessibleHeader('Licenças e Fontes Abertas', 2)}
            style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
          >
            Licenças e Fontes
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            Mapas e dados geoespaciais são fornecidos sob a licença OpenStreetMap / ODbL e dados da Google Routes API sob os termos da Google Maps Platform. Fotos comunitárias são atribuídas conforme a política editorial estabelecida no ADR 0008.
          </Text>
        </View>
      </ScrollView>

      {/* Modal Acessível de Revogação de Consentimento */}
      <AccessibleModal
        visible={isRevokeModalOpen}
        transparent
        animationType="fade"
        onClose={handleCloseRevokeModal}
        initialFocusRef={modalTitleRef}
        returnFocusRef={revokeButtonRef}
        accessibilityLabel="Confirmar revogação de consentimento de localização"
      >
        <View style={styles.modalOverlay}>
          <View
            style={[
              styles.modalCard,
              {
                backgroundColor: theme.colors.surfaceWhite,
                borderColor: theme.isHighContrast ? theme.colors.error : 'rgba(117, 155, 113, 0.25)',
                borderWidth: theme.isHighContrast ? 2 : 1,
              },
            ]}
            accessible
            accessibilityLabel="Modal de confirmação de revogação de consentimento"
          >
            <View style={styles.modalIconRow}>
              <Ionicons name="warning-outline" size={32} color={theme.colors.error} />
            </View>

            <Text
              ref={modalTitleRef}
              {...makeAccessibleHeader('Revogar Consentimento de Localização', 2)}
              style={[styles.modalTitle, theme.typography.headlineSm, { color: theme.colors.brandDeep }]}
            >
              Revogar Consentimento de Localização
            </Text>

            <Text style={[styles.modalDescription, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
              Deseja revogar o consentimento para cálculo de rotas com localização dinâmica? Novos cálculos dinâmicos serão bloqueados até um novo aceite explícito.
            </Text>

            {revokeError && (
              <View
                style={[styles.errorBanner, { backgroundColor: 'rgba(239, 68, 68, 0.08)', borderColor: theme.colors.error }]}
                accessible
                accessibilityRole="alert"
                accessibilityLabel={`Erro: ${revokeError}`}
              >
                <Ionicons name="alert-circle" size={18} color={theme.colors.error} />
                <Text style={[styles.errorText, theme.typography.bodySm, { color: theme.colors.error }]}>
                  {revokeError}
                </Text>
              </View>
            )}

            <View style={styles.modalActionsRow}>
              {revokeError ? (
                <>
                  <TouchableOpacity
                    style={[styles.modalCancelButton, { borderColor: theme.colors.brandSage }]}
                    onPress={handleCloseRevokeModal}
                    disabled={isRevoking}
                    {...makeAccessibleButton('Fechar modal de erro', 'Cancela e fecha a confirmação mantendo consentimento')}
                  >
                    <Text style={[styles.modalCancelButtonText, { color: theme.colors.brandDeep }]}>
                      Fechar
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    ref={retryButtonRef}
                    style={[styles.retryButton, { backgroundColor: theme.colors.brandForest }]}
                    onPress={handleConfirmRevoke}
                    disabled={isRevoking}
                    {...makeAccessibleButton(
                      'Tentar novamente',
                      'Tenta revogar o consentimento de localização novamente'
                    )}
                    accessibilityRole="button"
                    accessibilityState={{ disabled: isRevoking, busy: isRevoking }}
                  >
                    <Ionicons name="refresh" size={16} color="#FFFFFF" />
                    <Text style={styles.retryButtonText}>
                      {isRevoking ? 'Tentando...' : 'Tentar novamente'}
                    </Text>
                  </TouchableOpacity>
                </>
              ) : (
                <>
                  <TouchableOpacity
                    style={[styles.modalCancelButton, { borderColor: theme.colors.brandSage }]}
                    onPress={handleCloseRevokeModal}
                    disabled={isRevoking}
                    {...makeAccessibleButton('Cancelar revogação', 'Mantém o consentimento ativo')}
                  >
                    <Text style={[styles.modalCancelButtonText, { color: theme.colors.brandDeep }]}>
                      Cancelar
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.modalConfirmButton, { backgroundColor: theme.colors.error }]}
                    onPress={handleConfirmRevoke}
                    disabled={isRevoking}
                    {...makeAccessibleButton(
                      'Confirmar revogação',
                      'Revoga o consentimento e restaura origens fixas homologadas'
                    )}
                    accessibilityRole="button"
                    accessibilityState={{ disabled: isRevoking, busy: isRevoking }}
                  >
                    <Text style={styles.modalConfirmButtonText}>
                      {isRevoking ? 'Revogando...' : 'Revogar'}
                    </Text>
                  </TouchableOpacity>
                </>
              )}
            </View>
          </View>
        </View>
      </AccessibleModal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  preReleaseNoticeCard: {
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    gap: 6,
  },
  noticeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  noticeTitle: {
    fontWeight: '700',
    fontSize: 13,
  },
  noticeText: {
    fontSize: 12,
    lineHeight: 18,
  },
  card: {
    padding: 18,
    borderRadius: 16,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  sectionTitle: {
    fontWeight: '700',
    flex: 1,
  },
  metaRow: {
    gap: 4,
    marginBottom: 14,
  },
  metaBadge: {
    fontWeight: '600',
    fontSize: 11,
  },
  subSectionTitle: {
    fontWeight: '700',
    marginTop: 12,
    marginBottom: 4,
  },
  paragraph: {
    lineHeight: 20,
    marginBottom: 8,
  },
  linkGroup: {
    gap: 8,
    marginVertical: 8,
  },
  externalLinkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 4,
  },
  linkText: {
    fontSize: 13,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  consentStatusCard: {
    backgroundColor: 'rgba(51, 96, 30, 0.05)',
    padding: 14,
    borderRadius: 12,
    marginTop: 12,
    gap: 10,
  },
  consentStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  consentStatusText: {
    fontSize: 12,
    fontWeight: '600',
    flex: 1,
  },
  revokeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  revokeButtonText: {
    fontSize: 12,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    maxWidth: 420,
    borderRadius: 20,
    padding: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 8,
  },
  modalIconRow: {
    alignItems: 'center',
    marginBottom: 10,
  },
  modalTitle: {
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  modalDescription: {
    lineHeight: 18,
    marginBottom: 14,
    textAlign: 'center',
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 14,
  },
  errorText: {
    flex: 1,
    fontWeight: '600',
    fontSize: 13,
  },
  modalActionsRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 6,
  },
  modalCancelButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
    borderWidth: 1,
  },
  modalCancelButtonText: {
    fontWeight: '600',
    fontSize: 14,
  },
  modalConfirmButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
  },
  modalConfirmButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  retryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 10,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
});
