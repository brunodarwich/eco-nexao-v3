import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';

interface BadgeProps {
  type: 'greenSeal' | 'verified' | 'semturInventory' | 'semtur' | 'warning';
  label?: string;
}

export const Badge: React.FC<BadgeProps> = ({ type, label }) => {
  switch (type) {
    case 'greenSeal':
      return (
        <View style={[styles.badgeContainer, styles.greenBadge]} accessible accessibilityRole="text" accessibilityLabel={`Selo Verde: ${label || 'Selo Verde'}`}>
          <Ionicons name="leaf" size={14} color={theme.colors.onPrimary} />
          <Text style={styles.greenText}>{label || 'Selo Verde'}</Text>
        </View>
      );
    case 'semturInventory':
    case 'semtur':
      return (
        <View
          style={[styles.badgeContainer, styles.semturBadge]}
          accessible
          accessibilityRole="text"
          accessibilityLabel="Origem dos dados: Inventário SEMTUR"
        >
          <Ionicons name="bookmark-outline" size={13} color="#334155" />
          <Text style={styles.semturText}>{label || 'Inventário SEMTUR'}</Text>
        </View>
      );
    case 'verified':
      return (
        <View style={[styles.badgeContainer, styles.verifiedBadge]} accessible accessibilityRole="text" accessibilityLabel={label || 'Verificada'}>
          <Ionicons name="checkmark-circle" size={14} color={theme.colors.onPrimary} />
          <Text style={styles.verifiedText}>{label || 'Verificada'}</Text>
        </View>
      );
    case 'warning':
      return (
        <View style={[styles.badgeContainer, styles.warningBadge]} accessible accessibilityRole="text" accessibilityLabel={label || 'Aviso Territorial'}>
          <Ionicons name="warning" size={14} color={theme.colors.brandDeep} />
          <Text style={styles.warningText}>{label || 'Aviso Territorial'}</Text>
        </View>
      );
    default:
      return null;
  }
};

const styles = StyleSheet.create({
  badgeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radii.full,
    gap: 4,
  },
  greenBadge: {
    backgroundColor: theme.colors.brandLeaf,
  },
  greenText: {
    ...theme.typography.labelSm,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
  semturBadge: {
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  semturText: {
    ...theme.typography.labelSm,
    color: '#334155',
    fontWeight: '600',
    fontSize: 11,
  },
  verifiedBadge: {
    backgroundColor: theme.colors.brandForest,
  },
  verifiedText: {
    ...theme.typography.labelSm,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
  warningBadge: {
    backgroundColor: theme.colors.errorContainer,
  },
  warningText: {
    ...theme.typography.labelSm,
    color: theme.colors.onErrorContainer,
    fontWeight: '700',
  },
});
