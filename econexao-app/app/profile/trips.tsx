import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../src/components/common/UIStateViews';
import { useMyTripsQuery } from '../../src/hooks/queries';
import { useAuth } from '../../src/hooks/useAuth';
import { theme } from '../../src/theme/theme';

export default function TripsHistoryScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const tripsQuery = useMyTripsQuery(user?.id);

  return (
    <View style={styles.container}>
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
          tripsQuery.data.map((trip: any) => (
            <View key={trip.id || Math.random().toString()} style={styles.tripCard}>
              <View style={styles.tripHeader}>
                <Ionicons name="navigate-circle" size={24} color={theme.colors.brandForest} />
                <Text style={styles.tripTitle}>{trip.route_name || 'Viagem em Rota Ecológica'}</Text>
              </View>
              <Text style={styles.tripDate}>
                Data: {new Date(trip.created_at || Date.now()).toLocaleDateString('pt-BR')}
              </Text>
              <Text style={styles.tripStatus}>
                Status: {trip.status === 'completed' ? 'Concluída' : 'Em andamento'}
              </Text>
            </View>
          ))
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
    backgroundColor: theme.colors.surfaceBackground,
  },
  content: {
    padding: theme.spacing.marginMobile,
    gap: 12,
  },
  tripCard: {
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.lg,
    padding: theme.spacing.marginMobile,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
    ...theme.shadows.card,
  },
  tripHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  tripTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
  },
  tripDate: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
  },
  tripStatus: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    marginTop: 4,
    fontWeight: '600',
  },
});
