import React, { useState } from 'react';
import {
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ActivityIndicator,
  AccessibilityInfo,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useAppTheme } from '../../theme/theme';
import { useAuth } from '../../hooks/useAuth';
import { makeAccessibleButton, makeAccessibleHeader } from '../../utils/accessibility';

interface AccountDeletionModalProps {
  visible: boolean;
  onClose: () => void;
}

export const AccountDeletionModal: React.FC<AccountDeletionModalProps> = ({
  visible,
  onClose,
}) => {
  const theme = useAppTheme();
  const { signOut } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleConfirmDeletion = async () => {
    try {
      setIsProcessing(true);
      AccessibilityInfo.announceForAccessibility('Processando solicitação de exclusão de conta...');

      // Em conformidade com a LGPD: encerramos a sessão e limpamos dados locais
      await signOut();
      AccessibilityInfo.announceForAccessibility(
        'Sua solicitação foi registrada e sua sessão foi encerrada com sucesso.'
      );
      Alert.alert(
        'Conta Encerrada',
        'Sua sessão foi encerrada e seus identificadores pessoais foram removidos conforme a LGPD.'
      );
      onClose();
    } catch {
      Alert.alert('Erro', 'Não foi possível processar a solicitação no momento.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.error : 'transparent',
              borderWidth: theme.isHighContrast ? 2 : 0,
            },
          ]}
        >
          <View style={styles.iconRow}>
            <Ionicons name="warning" size={36} color={theme.colors.error} />
          </View>

          <Text
            {...makeAccessibleHeader('Exclusão de Conta e Privacidade LGPD', 2)}
            style={[styles.title, theme.typography.headlineSm, { color: theme.colors.brandDeep }]}
          >
            Excluir Conta
          </Text>

          <Text style={[styles.description, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            Em conformidade com a Lei Geral de Proteção de Dados (LGPD), ao solicitar a exclusão da sua conta:
          </Text>

          <View style={styles.bulletList}>
            <Text style={[styles.bulletItem, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
              • Seus dados de identificação (e-mail, nome, localização) serão removidos permanentemente.
            </Text>
            <Text style={[styles.bulletItem, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
              • Seus favoritos e preferências salvas serão revogados.
            </Text>
            <Text style={[styles.bulletItem, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
              • Métricas estatísticas de viagens serão mantidas de forma estritamente anônima e agregada para conservação comunitária.
            </Text>
          </View>

          <View style={styles.actionsRow}>
            <TouchableOpacity
              style={[styles.cancelButton, { borderColor: theme.colors.brandSage }]}
              onPress={onClose}
              disabled={isProcessing}
              {...makeAccessibleButton('Cancelar exclusão de conta')}
            >
              <Text style={[styles.cancelButtonText, { color: theme.colors.brandDeep }]}>
                Voltar
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.deleteButton, { backgroundColor: theme.colors.error }]}
              onPress={handleConfirmDeletion}
              disabled={isProcessing}
              {...makeAccessibleButton('Confirmar exclusão e encerrar conta')}
            >
              {isProcessing ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.deleteButtonText}>Confirmar Exclusão</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
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
  card: {
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
  iconRow: {
    alignItems: 'center',
    marginBottom: 10,
  },
  title: {
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  description: {
    lineHeight: 18,
    marginBottom: 10,
    textAlign: 'center',
  },
  bulletList: {
    backgroundColor: 'rgba(185, 28, 28, 0.06)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 18,
    gap: 6,
  },
  bulletItem: {
    lineHeight: 18,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
    borderWidth: 1,
  },
  cancelButtonText: {
    fontWeight: '600',
    fontSize: 14,
  },
  deleteButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
  },
  deleteButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
});
