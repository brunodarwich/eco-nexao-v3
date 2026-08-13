import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';

interface LoadingViewProps {
  message?: string;
}

export const LoadingView: React.FC<LoadingViewProps> = ({
  message = 'Carregando dados da rota...',
}) => (
  <View style={styles.container}>
    <ActivityIndicator size="large" color={theme.colors.brandForest} />
    <Text style={styles.loadingText}>{message}</Text>
  </View>
);

interface EmptyStateViewProps {
  title?: string;
  message?: string;
  onReset?: () => void;
  resetLabel?: string;
}

export const EmptyStateView: React.FC<EmptyStateViewProps> = ({
  title = 'Nenhum resultado encontrado',
  message = 'Tente ajustar seus termos de busca ou selecionar outra categoria.',
  onReset,
  resetLabel = 'Limpar Filtros',
}) => (
  <View style={styles.container}>
    <View style={styles.iconCircle}>
      <Ionicons name="search-outline" size={32} color={theme.colors.brandSage} />
    </View>
    <Text style={styles.title}>{title}</Text>
    <Text style={styles.subtitle}>{message}</Text>
    {onReset && (
      <TouchableOpacity
        style={styles.resetButton}
        onPress={onReset}
        {...makeAccessibleButton(resetLabel, 'Redefine a busca e os filtros aplicados')}
      >
        <Text style={styles.resetButtonText}>{resetLabel}</Text>
      </TouchableOpacity>
    )}
  </View>
);

interface ErrorStateViewProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorStateView: React.FC<ErrorStateViewProps> = ({
  title = 'Erro de Carregamento',
  message = 'Não foi possível conectar com os dados da rota no momento.',
  onRetry,
}) => (
  <View style={styles.container}>
    <View style={[styles.iconCircle, { backgroundColor: theme.colors.errorContainer }]}>
      <Ionicons name="alert-circle-outline" size={32} color={theme.colors.error} />
    </View>
    <Text style={styles.title}>{title}</Text>
    <Text style={styles.subtitle}>{message}</Text>
    {onRetry && (
      <TouchableOpacity
        style={styles.resetButton}
        onPress={onRetry}
        {...makeAccessibleButton('Tentar Novamente', 'Recarrega as informações da rota')}
      >
        <Text style={styles.resetButtonText}>Tentar Novamente</Text>
      </TouchableOpacity>
    )}
  </View>
);

const styles = StyleSheet.create({
  container: {
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 250,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  loadingText: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
    marginTop: 16,
  },
  title: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
    textAlign: 'center',
    marginBottom: 20,
    maxWidth: 300,
  },
  resetButton: {
    height: 44,
    paddingHorizontal: 20,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.brandForest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  resetButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
});
