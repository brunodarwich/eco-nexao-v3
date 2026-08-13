import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';

export type StatsRoute = {
  best_season?: string | null;
  bestSeason?: string | null;
  connectivity?: string | null;
  road_access?: string | null;
  roadAccess?: string | null;
  payment_info?: string | null;
  paymentInfo?: string | null;
};

interface RouteStatsProps {
  route: StatsRoute;
}

export const RouteStats: React.FC<RouteStatsProps> = ({ route }) => {
  const bestSeason = route.best_season ?? route.bestSeason ?? 'Não informado';
  const connectivity = route.connectivity ?? 'Não informado';
  const roadAccess = route.road_access ?? route.roadAccess ?? 'Não informado';
  const paymentInfo = route.payment_info ?? route.paymentInfo ?? 'Não informado';

  const stats = [
    {
      icon: 'sunny-outline' as keyof typeof Ionicons.glyphMap,
      label: 'Melhor Época',
      value: bestSeason,
    },
    {
      icon: 'wifi-outline' as keyof typeof Ionicons.glyphMap,
      label: 'Conectividade',
      value: connectivity,
    },
    {
      icon: 'car-outline' as keyof typeof Ionicons.glyphMap,
      label: 'Acesso',
      value: roadAccess,
    },
    {
      icon: 'card-outline' as keyof typeof Ionicons.glyphMap,
      label: 'Pagamento Base',
      value: paymentInfo,
    },
  ];

  return (
    <View style={styles.grid}>
      {stats.map((item, index) => (
        <View
          key={index}
          style={styles.statCard}
          accessible
          accessibilityLabel={`${item.label}: ${item.value}`}
        >
          <Ionicons name={item.icon} size={22} color={theme.colors.brandForest} />
          <Text style={styles.statLabel}>{item.label}</Text>
          <Text style={styles.statValue} numberOfLines={1}>
            {item.value}
          </Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.stackSm,
    marginVertical: theme.spacing.stackMd,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: theme.colors.surfaceContainerLow,
    padding: 14,
    borderRadius: theme.radii.lg,
    gap: 4,
  },
  statLabel: {
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
  },
  statValue: {
    ...theme.typography.labelMd,
    color: theme.colors.brandDeep,
    fontWeight: '700',
  },
});
