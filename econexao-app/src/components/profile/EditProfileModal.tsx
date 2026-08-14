import React, { useState, useEffect } from 'react';
import {
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ActivityIndicator,
  AccessibilityInfo,
  Alert,
} from 'react-native';
import { useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';

import { apiClient } from '../../api/client';
import { queryKeys } from '../../api/queryKeys';
import { useAppTheme } from '../../theme/theme';
import { makeAccessibleButton, makeAccessibleHeader } from '../../utils/accessibility';
import { UserProfileSchema } from '../../api/types';

interface EditProfileModalProps {
  visible: boolean;
  onClose: () => void;
  currentProfile?: UserProfileSchema;
  userId?: string;
}

export const EditProfileModal: React.FC<EditProfileModalProps> = ({
  visible,
  onClose,
  currentProfile,
  userId = '',
}) => {
  const theme = useAppTheme();
  let queryClient: ReturnType<typeof useQueryClient> | undefined;
  try {
    queryClient = useQueryClient();
  } catch {
    queryClient = undefined;
  }

  const [name, setName] = useState(currentProfile?.name ?? '');
  const [location, setLocation] = useState(currentProfile?.location ?? '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (visible && currentProfile) {
      setName(currentProfile.name ?? '');
      setLocation(currentProfile.location ?? '');
    }
  }, [visible, currentProfile]);

  const handleSave = async () => {
    try {
      setIsSubmitting(true);
      const res = await apiClient.updateMyProfile({
        name: name.trim() || undefined,
        location: location.trim() || undefined,
      });

      if (queryClient) {
        queryClient.setQueryData(queryKeys.myProfile(userId), res);
        void queryClient.invalidateQueries({ queryKey: queryKeys.myProfile(userId) });
      }

      AccessibilityInfo.announceForAccessibility('Perfil atualizado com sucesso.');

      Alert.alert('Sucesso', 'Seu perfil foi atualizado.');
      onClose();
    } catch {
      AccessibilityInfo.announceForAccessibility('Erro ao atualizar perfil.');
      Alert.alert('Erro', 'Não foi possível atualizar suas informações de perfil.');
    } finally {
      setIsSubmitting(false);
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
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'transparent',
              borderWidth: theme.isHighContrast ? 2 : 0,
            },
          ]}
        >
          <View style={styles.header}>
            <Text
              {...makeAccessibleHeader('Editar Perfil', 2)}
              style={[styles.title, theme.typography.headlineSm, { color: theme.colors.brandDeep }]}
            >
              Editar Perfil
            </Text>
            <TouchableOpacity
              onPress={onClose}
              {...makeAccessibleButton('Fechar edição de perfil')}
            >
              <Ionicons name="close" size={24} color={theme.colors.onSurfaceVariant} />
            </TouchableOpacity>
          </View>

          <View style={styles.formGroup}>
            <Text style={[styles.label, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
              Nome de Exibição
            </Text>
            <TextInput
              style={[
                styles.input,
                {
                  borderColor: theme.isHighContrast ? theme.colors.brandDeep : 'rgba(117, 155, 113, 0.3)',
                  color: theme.colors.brandDeep,
                },
              ]}
              value={name}
              onChangeText={setName}
              placeholder="Ex: Maria Silva"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              accessibilityLabel="Nome de exibição"
            />
          </View>

          <View style={styles.formGroup}>
            <Text style={[styles.label, theme.typography.labelMd, { color: theme.colors.brandDeep }]}>
              Cidade / Comunidade de Origem
            </Text>
            <TextInput
              style={[
                styles.input,
                {
                  borderColor: theme.isHighContrast ? theme.colors.brandDeep : 'rgba(117, 155, 113, 0.3)',
                  color: theme.colors.brandDeep,
                },
              ]}
              value={location}
              onChangeText={setLocation}
              placeholder="Ex: Belterra, PA"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              accessibilityLabel="Localização ou cidade"
            />
          </View>

          <View style={styles.actionsRow}>
            <TouchableOpacity
              style={[styles.cancelButton, { borderColor: theme.colors.brandForest }]}
              onPress={onClose}
              disabled={isSubmitting}
              {...makeAccessibleButton('Cancelar alterações')}
            >
              <Text style={[styles.cancelButtonText, { color: theme.colors.brandForest }]}>
                Cancelar
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.saveButton,
                { backgroundColor: theme.colors.brandForest },
              ]}
              onPress={handleSave}
              disabled={isSubmitting}
              {...makeAccessibleButton('Salvar perfil')}
            >
              {isSubmitting ? (
                <ActivityIndicator size="small" color={theme.colors.surfaceWhite} />
              ) : (
                <Text style={[styles.saveButtonText, { color: theme.colors.surfaceWhite }]}>
                  Salvar
                </Text>
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
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    width: '100%',
    maxWidth: 420,
    borderRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: {
    fontWeight: '700',
  },
  formGroup: {
    marginBottom: 14,
  },
  label: {
    marginBottom: 6,
    fontWeight: '600',
  },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    backgroundColor: '#FAFBF9',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
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
  saveButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
  },
  saveButtonText: {
    fontWeight: '700',
    fontSize: 14,
  },
});
