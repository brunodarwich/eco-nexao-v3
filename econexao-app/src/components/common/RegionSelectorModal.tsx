import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  AccessibilityInfo,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { useApp } from '../../hooks/useApp';
import { useRegionsQuery } from '../../hooks/queries';
import { apiClient } from '../../api/client';
import { makeAccessibleButton } from '../../utils/accessibility';
import type { Region } from '../../api/types';

interface RegionSelectorModalProps {
  visible: boolean;
  onClose: () => void;
}

export const RegionSelectorModal: React.FC<RegionSelectorModalProps> = ({
  visible,
  onClose,
}) => {
  const { state, dispatch } = useApp();
  const regionsQuery = useRegionsQuery();

  const handleSelectRegion = async (region: Region) => {
    dispatch({ type: 'SET_ACTIVE_REGION', payload: region.id });
    onClose();
    AccessibilityInfo.announceForAccessibility(`Região alterada para ${region.name}`);

    try {
      await apiClient.updateMyPreferences({ active_region_id: region.id });
    } catch {
      AccessibilityInfo.announceForAccessibility('Não foi possível salvar a preferência de região no servidor.');
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
      accessibilityViewIsModal
      aria-modal
    >
      <View style={styles.backdrop}>
        <View style={styles.modalContainer}>
          <View style={styles.header}>
            <View style={styles.headerTitleRow}>
              <Ionicons name="location" size={22} color={theme.colors.brandForest} />
              <Text style={styles.title}>Selecionar Região</Text>
            </View>
            <TouchableOpacity
              style={styles.closeButton}
              onPress={onClose}
              {...makeAccessibleButton('Fechar', 'Fecha o seletor de região')}
            >
              <Ionicons name="close" size={24} color={theme.colors.onSurface} />
            </TouchableOpacity>
          </View>

          {regionsQuery.isPending ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={theme.colors.brandForest} />
              <Text style={styles.loadingText}>Carregando regiões...</Text>
            </View>
          ) : regionsQuery.isError ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>Erro ao carregar lista de regiões.</Text>
              <TouchableOpacity
                style={styles.retryButton}
                onPress={() => void regionsQuery.refetch()}
                {...makeAccessibleButton('Tentar novamente')}
              >
                <Text style={styles.retryText}>Tentar novamente</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <ScrollView contentContainerStyle={styles.listContent}>
              {regionsQuery.data?.map((region) => {
                const isSelected = region.id === state.activeRegionId;
                return (
                  <TouchableOpacity
                    key={region.id}
                    style={[styles.regionOption, isSelected && styles.regionOptionSelected]}
                    onPress={() => void handleSelectRegion(region)}
                    accessibilityRole="button"
                    accessibilityState={{ selected: isSelected }}
                    accessibilityLabel={`${region.name}, ${region.state_code}. ${isSelected ? 'Selecionada' : 'Toque para selecionar'}`}
                  >
                    <View style={styles.regionInfo}>
                      <Text style={[styles.regionName, isSelected && styles.regionNameSelected]}>
                        {region.name}
                      </Text>
                      <Text style={styles.regionState}>{region.state_code}</Text>
                    </View>
                    {isSelected && (
                      <Ionicons name="checkmark-circle" size={22} color={theme.colors.brandForest} />
                    )}
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.marginMobile,
  },
  modalContainer: {
    width: '100%',
    maxWidth: 400,
    maxHeight: '80%',
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.xl,
    padding: theme.spacing.marginMobile,
    ...theme.shadows.card,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.stackMd,
    paddingBottom: theme.spacing.stackSm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.surfaceContainer,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    ...theme.typography.headlineMd,
    color: theme.colors.brandDeep,
  },
  closeButton: {
    padding: 4,
    borderRadius: theme.radii.full,
  },
  loadingContainer: {
    padding: 32,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
  },
  errorContainer: {
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    ...theme.typography.bodyMd,
    color: theme.colors.error,
  },
  retryButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: theme.colors.brandForest,
    borderRadius: theme.radii.full,
  },
  retryText: {
    ...theme.typography.labelMd,
    color: theme.colors.onPrimary,
    fontWeight: '600',
  },
  listContent: {
    gap: 8,
  },
  regionOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderRadius: theme.radii.lg,
    backgroundColor: theme.colors.surfaceContainerLow,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  regionOptionSelected: {
    backgroundColor: theme.colors.secondaryContainer,
    borderColor: theme.colors.brandForest,
  },
  regionInfo: {
    flex: 1,
  },
  regionName: {
    ...theme.typography.titleMd,
    color: theme.colors.brandDeep,
  },
  regionNameSelected: {
    color: theme.colors.brandForest,
    fontWeight: '700',
  },
  regionState: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
  },
});
