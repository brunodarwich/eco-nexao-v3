import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { useApp } from '../../hooks/useApp';
import { makeAccessibleButton } from '../../utils/accessibility';
import { useRegionsQuery } from '../../hooks/queries';
import { RegionSelectorModal } from './RegionSelectorModal';

interface AppHeaderProps {
  showBack?: boolean;
  onBackPress?: () => void;
  title?: string;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  showBack = false,
  onBackPress,
  title = 'ECOnexão',
}) => {
  const { state } = useApp();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const regions = useRegionsQuery();
  const activeRegion = regions.data?.find((region) => region.id === state.activeRegionId);

  return (
    <>
      <View style={styles.headerContainer}>
        <View style={styles.leftRow}>
          {showBack ? (
            <TouchableOpacity
              style={styles.backButton}
              onPress={onBackPress}
              {...makeAccessibleButton('Voltar', 'Retorna à tela anterior')}
            >
              <Ionicons name="arrow-back" size={24} color={theme.colors.brandForest} />
            </TouchableOpacity>
          ) : (
            <View style={styles.logoRow}>
              <View style={styles.logoBadge}>
                <Ionicons name="leaf" size={20} color={theme.colors.brandForest} />
              </View>
              <Text style={styles.brandTitle}>{title}</Text>
            </View>
          )}
        </View>

        <TouchableOpacity
          style={styles.regionChip}
          onPress={() => setIsModalOpen(true)}
          {...makeAccessibleButton(
            `Região atual: ${activeRegion?.name ?? 'não selecionada'}`,
            'Toque para abrir o seletor de região'
          )}
        >
          <Ionicons name="location" size={16} color={theme.colors.brandSage} />
          <Text style={styles.regionText} numberOfLines={1}>
            {activeRegion?.name ?? 'Selecionar região'}
          </Text>
        </TouchableOpacity>
      </View>

      <RegionSelectorModal
        visible={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};

const styles = StyleSheet.create({
  headerContainer: {
    height: 64,
    backgroundColor: 'rgba(249, 250, 247, 0.95)',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.surfaceContainer,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.marginMobile,
    zIndex: 50,
  },
  leftRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  backButton: {
    minWidth: theme.spacing.touchMin,
    minHeight: theme.spacing.touchMin,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radii.full,
    marginRight: theme.spacing.stackSm,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.stackSm,
  },
  logoBadge: {
    width: 32,
    height: 32,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.secondaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandTitle: {
    ...theme.typography.headlineMd,
    color: theme.colors.brandForest,
  },
  regionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: theme.colors.surfaceContainerLow,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: theme.radii.full,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
    maxWidth: 180,
  },
  regionText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
});
