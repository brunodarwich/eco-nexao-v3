import React from 'react';
import { ScrollView, StyleSheet, Text, View, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { useMyTripsQuery } from '../../../src/hooks/queries';
import { useAuth } from '../../../src/hooks/useAuth';
import { useAppTheme } from '../../../src/theme/theme';
import { makeAccessibleButton } from '../../../src/utils/accessibility';

export default function TripsHistoryScreen() {
  const router = useRouter();
  const theme = useAppTheme();
  const { user } = useAuth();
  const tripsQuery = useMyTripsQuery(user?.id);

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surfaceBackground }]}>
      <AppHeader showBack onBackPress={() => router.back()} title="Histórico de Viagens" />

      <ScrollView contentContainerStyle={styles.content}>
        {tripsQuery.isPending ? (
          <LoadingView message="Carregando histórico de viagens..." />
        ) : tripsQuery.isError ? (
          <ErrorStateView
            title="Erro ao carregar viagens"
            message="Não foi possível obter o histórico de viagens."
            onRetry={() => void tripsQuery.refetch()}
          />
        ) : tripsQuery.data?.length ? (
          tripsQuery.data.map((trip: any) => {
            const title = trip.route_title || trip.route_name || 'Trilha / Rota Ecológica';
            const isCompleted = trip.status === 'completed';
            const hasRoute = Boolean(trip.route_id);

            return (
              <TouchableOpacity
                key={trip.id || Math.random().toString()}
                style={[
                  styles.tripCard,
                  {
                    backgroundColor: theme.colors.surfaceWhite,
                    borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
                    borderWidth: theme.isHighContrast ? 2 : 1,
                  },
                ]}
                disabled={!hasRoute}
                onPress={() => {
                  if (hasRoute) {
                    router.push(`/route/${trip.route_id}`);
                  }
                }}
                {...makeAccessibleButton(
                  `Viagem ${title}`,
                  hasRoute ? 'Toque para ver os detalhes da rota' : undefined
                )}
              >
                <View style={styles.tripHeader}>
                  <Ionicons
                    name={isCompleted ? 'checkmark-circle' : 'compass'}
                    size={24}
                    color={isCompleted ? theme.colors.brandForest : theme.colors.brandLeaf}
                  />
                  <Text
                    style={[
                      styles.tripTitle,
                      theme.typography.titleMd,
                      { color: theme.colors.brandDeep, fontWeight: '700' },
                    ]}
                  >
                    {title}
                  </Text>
                </View>

                <Text style={[styles.tripDate, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
                  Data: {new Date(trip.created_at || Date.now()).toLocaleDateString('pt-BR')}
                </Text>

                <View style={styles.statusRow}>
                  <Text
                    style={[
                      styles.tripStatus,
                      theme.typography.labelSm,
                      {
                        color: isCompleted ? theme.colors.brandForest : '#B45309',
                        fontWeight: '700',
                      },
                    ]}
                  >
                    Status: {isCompleted ? 'Concluída' : 'Em andamento'}
                  </Text>
                  {hasRoute && (
                    <Ionicons name="chevron-forward" size={16} color={theme.colors.onSurfaceVariant} />
                  )}
                </View>
              </TouchableOpacity>
            );
          })
        ) : (
          <EmptyStateView
            title="Nenhuma viagem registrada"
            message="Você ainda não registrou nenhuma viagem ou visita em rotas ecológicas."
          />
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 12,
  },
  tripCard: {
    borderRadius: 16,
    padding: 16,
  },
  tripHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  tripTitle: {
    flex: 1,
  },
  tripDate: {
    marginBottom: 4,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  tripStatus: {
    marginTop: 2,
  },
});
