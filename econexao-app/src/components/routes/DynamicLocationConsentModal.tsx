import React, { useRef, useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ScrollView,
  AccessibilityInfo,
} from 'react-native';
import * as Linking from 'expo-linking';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { makeAccessibleButton, setAccessibilityFocusSafely } from '../../utils/accessibility';
import { AccessibleModal } from '../common/AccessibleModal';
import {
  CURRENT_LOCATION_POLICY_VERSION,
  saveLocationConsent,
} from '../../auth/locationConsent';

export interface DynamicLocationConsentModalProps {
  visible: boolean;
  onConsentSuccess: () => void;
  onCancelFixedOrigin: () => void;
  returnFocusRef?: React.RefObject<any>;
}

export const DynamicLocationConsentModal: React.FC<DynamicLocationConsentModalProps> = ({
  visible,
  onConsentSuccess,
  onCancelFixedOrigin,
  returnFocusRef,
}) => {
  const [isAdult, setIsAdult] = useState(false);
  const [hasAgreedTerms, setHasAgreedTerms] = useState(false);

  const modalTitleRef = useRef<any>(null);
  const adultCheckboxRef = useRef<any>(null);

  useEffect(() => {
    if (visible) {
      setIsAdult(false);
      setHasAgreedTerms(false);
      const timer = setTimeout(() => {
        setAccessibilityFocusSafely(modalTitleRef);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [visible]);

  const canContinue = isAdult && hasAgreedTerms;

  const handleConfirm = async () => {
    if (!canContinue) {
      if (!isAdult) {
        AccessibilityInfo.announceForAccessibility(
          'Aviso: É necessário declarar ter 18 anos ou mais para utilizar localização dinâmica.'
        );
      } else if (!hasAgreedTerms) {
        AccessibilityInfo.announceForAccessibility(
          'Aviso: É necessário concordar com o tratamento temporário de localização.'
        );
      }
      return;
    }

    const saved = await saveLocationConsent(true, true);
    if (saved) {
      AccessibilityInfo.announceForAccessibility(
        'Consentimento registrado com sucesso. Prosseguindo com o cálculo do trajeto.'
      );
      onConsentSuccess();
    } else {
      AccessibilityInfo.announceForAccessibility('Não foi possível registrar o consentimento local.');
    }
  };

  const handleCancel = () => {
    AccessibilityInfo.announceForAccessibility('Uso de localização dinâmica cancelado. Mantendo origem fixa.');
    onCancelFixedOrigin();
  };

  const handleOpenPrivacyPolicy = () => {
    AccessibilityInfo.announceForAccessibility('Abrindo informações da Política de Privacidade.');
    void Linking.openURL(Linking.createURL('/(tabs)/(profile)/legal'));
  };

  return (
    <AccessibleModal
      visible={visible}
      transparent
      animationType="fade"
      onClose={handleCancel}
      initialFocusRef={modalTitleRef}
      returnFocusRef={returnFocusRef}
      accessibilityLabel="Consentimento para Localizacao Dinamica e Rotas"
    >
      <View style={styles.overlay}>
        <View style={styles.dialogCard} accessible accessibilityLabel="Consentimento de localização dinâmica">
          <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {/* Header */}
            <View style={styles.headerRow}>
              <View style={styles.iconBadge}>
                <Ionicons name="shield-checkmark" size={24} color={theme.colors.brandForest} />
              </View>
              <Text ref={modalTitleRef} style={styles.title} accessibilityRole="header">
                Privacidade de Localização
              </Text>
            </View>

            {/* Version / Status badge */}
            <View style={styles.badgeContainer}>
              <Text style={styles.badgeText}>
                Versão da política: {CURRENT_LOCATION_POLICY_VERSION}
              </Text>
            </View>

            {/* Short base text required by LGPD spec */}
            <Text style={styles.baseText}>
              Para calcular o trajeto, o ECOnexão enviará temporariamente sua localização e o destino da rota à Google Routes API. O ECOnexão não salva sua localização nem a registra em logs. Você pode cancelar e usar uma origem fixa.
            </Text>

            {/* Link to full policy */}
            <TouchableOpacity
              style={styles.policyLinkButton}
              onPress={handleOpenPrivacyPolicy}
              {...makeAccessibleButton('Ler Política de Privacidade de Localização e Rotas')}
              accessibilityRole="link"
            >
              <Ionicons name="document-text-outline" size={16} color={theme.colors.brandForest} />
              <Text style={styles.policyLinkText}>Ler Política de Privacidade Completa</Text>
            </TouchableOpacity>

            {/* Checkboxes Area */}
            <View style={styles.checkboxGroup}>
              {/* Checkbox 1: Age 18+ */}
              <TouchableOpacity
                ref={adultCheckboxRef}
                style={[styles.checkboxRow, isAdult && styles.checkboxRowActive]}
                onPress={() => {
                  const next = !isAdult;
                  setIsAdult(next);
                  AccessibilityInfo.announceForAccessibility(
                    next ? 'Declaracao de maioridade selecionada.' : 'Declaracao de maioridade desmarcada.'
                  );
                }}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: isAdult }}
                accessibilityLabel="Declaro que tenho 18 anos ou mais."
                accessibilityHint="Toque para alternar a confirmação de maioridade"
              >
                <View style={[styles.checkboxBox, isAdult && styles.checkboxBoxChecked]}>
                  {isAdult && <Ionicons name="checkmark" size={16} color={theme.colors.onPrimary} />}
                </View>
                <Text style={styles.checkboxLabel}>Declaro que tenho 18 anos ou mais.</Text>
              </TouchableOpacity>

              {/* Checkbox 2: LGPD agreement */}
              <TouchableOpacity
                style={[styles.checkboxRow, hasAgreedTerms && styles.checkboxRowActive]}
                onPress={() => {
                  const next = !hasAgreedTerms;
                  setHasAgreedTerms(next);
                  AccessibilityInfo.announceForAccessibility(
                    next ? 'Consentimento para calculo selecionado.' : 'Consentimento para calculo desmarcado.'
                  );
                }}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: hasAgreedTerms }}
                accessibilityLabel="Li e concordo com o tratamento temporário da minha localização para calcular este trajeto."
                accessibilityHint="Toque para alternar a concordância com o tratamento temporário"
              >
                <View style={[styles.checkboxBox, hasAgreedTerms && styles.checkboxBoxChecked]}>
                  {hasAgreedTerms && <Ionicons name="checkmark" size={16} color={theme.colors.onPrimary} />}
                </View>
                <Text style={styles.checkboxLabel}>
                  Li e concordo com o tratamento temporário da minha localização para calcular este trajeto.
                </Text>
              </TouchableOpacity>
            </View>

            {/* Action Buttons */}
            <View style={styles.actionsContainer}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={handleCancel}
                {...makeAccessibleButton('Cancelar e usar origem fixa', 'Retorna para as origens oficiais homologadas')}
              >
                <Text style={styles.cancelButtonText}>Cancelar e usar origem fixa</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.confirmButton, !canContinue && styles.confirmButtonDisabled]}
                onPress={handleConfirm}
                disabled={!canContinue}
                {...makeAccessibleButton(
                  'Concordar e continuar',
                  canContinue
                    ? 'Prossegue com a obtenção de coordenadas e cálculo'
                    : 'Desabilitado até marcar as duas declarações acima',
                  !canContinue
                )}
                accessibilityRole="button"
                accessibilityState={{ disabled: !canContinue }}
              >
                <Text
                  style={[
                    styles.confirmButtonText,
                    !canContinue && styles.confirmButtonTextDisabled,
                  ]}
                >
                  Concordar e continuar
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </View>
    </AccessibleModal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  dialogCard: {
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.xl,
    padding: 24,
    width: '100%',
    maxWidth: 460,
    maxHeight: '90%',
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.25)',
    ...theme.shadows.card,
  },
  scrollContent: {
    gap: 16,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(51, 96, 30, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    fontWeight: '700',
    flex: 1,
  },
  badgeContainer: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.surfaceContainerLow,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radii.sm,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
  },
  badgeText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '600',
    fontSize: 11,
  },
  baseText: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 22,
  },
  policyLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  policyLinkText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandForest,
    textDecorationLine: 'underline',
    fontWeight: '600',
  },
  checkboxGroup: {
    gap: 12,
    marginVertical: 4,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    padding: 12,
    borderRadius: theme.radii.md,
    backgroundColor: theme.colors.surfaceContainerLow,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
  },
  checkboxRowActive: {
    borderColor: theme.colors.brandForest,
    backgroundColor: 'rgba(51, 96, 30, 0.04)',
  },
  checkboxBox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: theme.colors.brandForest,
    backgroundColor: theme.colors.surfaceWhite,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 1,
  },
  checkboxBoxChecked: {
    backgroundColor: theme.colors.brandForest,
  },
  checkboxLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.brandDeep,
    flex: 1,
    lineHeight: 20,
    fontWeight: '500',
  },
  actionsContainer: {
    gap: 10,
    marginTop: 8,
  },
  confirmButton: {
    backgroundColor: theme.colors.brandForest,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  confirmButtonDisabled: {
    backgroundColor: theme.colors.surfaceContainerHigh,
  },
  confirmButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
  confirmButtonTextDisabled: {
    color: theme.colors.outline,
  },
  cancelButton: {
    backgroundColor: theme.colors.surfaceContainerLow,
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
  },
  cancelButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
});
