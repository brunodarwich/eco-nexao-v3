import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';

export const MapLegend: React.FC = () => {
  const items = [
    { label: 'Hospedagem', color: theme.colors.brandForest, icon: 'bed' },
    { label: 'Alimentação', color: theme.colors.brandSun, icon: 'restaurant' },
    { label: 'Artesanato', color: theme.colors.brandLeaf, icon: 'basket' },
    { label: 'Emergência', color: theme.colors.error, icon: 'medical' },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.legendTitle}>Legenda do Mapa Acessível:</Text>
      <View style={styles.row}>
        {items.map((item, idx) => (
          <View key={idx} style={styles.item}>
            <View style={[styles.colorDot, { backgroundColor: item.color }]}>
              <Ionicons name={item.icon as any} size={10} color="#FFF" />
            </View>
            <Text style={styles.itemLabel}>{item.label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    padding: 12,
    borderRadius: theme.radii.lg,
    marginHorizontal: theme.spacing.marginMobile,
    marginVertical: theme.spacing.stackSm,
    ...theme.shadows.sm,
  },
  legendTitle: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontWeight: '700',
    marginBottom: 6,
  },
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  colorDot: {
    width: 18,
    height: 18,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  itemLabel: {
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 11,
  },
});
