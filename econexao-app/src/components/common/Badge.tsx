import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';

interface BadgeProps {
  type: 'greenSeal' | 'verified' | 'warning';
  label?: string;
}

export const Badge: React.FC<BadgeProps> = ({ type, label }) => {
  switch (type) {
    case 'greenSeal':
      return (
        <View style={[styles.badgeContainer, styles.greenBadge]}>
          <Ionicons name="leaf" size={14} color={theme.colors.onPrimary} />
          <Text style={styles.greenText}>{label || 'Selo Verde'}</Text>
        </View>
      );
    case 'verified':
      return (
        <View style={[styles.badgeContainer, styles.verifiedBadge]}>
          <Ionicons name="checkmark-circle" size={14} color={theme.colors.onPrimary} />
          <Text style={styles.verifiedText}>{label || 'Verificada'}</Text>
        </View>
      );
    case 'warning':
      return (
        <View style={[styles.badgeContainer, styles.warningBadge]}>
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
