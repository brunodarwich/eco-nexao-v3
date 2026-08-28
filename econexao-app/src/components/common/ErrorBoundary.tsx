import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });
    if (__DEV__) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  private handleReset = () => {
    if (this.props.onReset) {
      this.props.onReset();
    }
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <SafeAreaView style={styles.safeArea}>
          <ScrollView contentContainerStyle={styles.container}>
            <View style={styles.iconCircle}>
              <Ionicons name="alert-circle-outline" size={48} color={theme.colors.error} />
            </View>

            <Text style={styles.title}>Ops! Algo deu errado</Text>
            <Text style={styles.message}>
              Ocorreu um erro inesperado ao renderizar esta tela. Não se preocupe, seus dados estão seguros.
            </Text>

            {__DEV__ && this.state.error && (
              <View style={styles.devErrorBox}>
                <Text style={styles.devErrorTitle}>Detalhes do Erro (Modo Dev):</Text>
                <Text style={styles.devErrorText}>{this.state.error.toString()}</Text>
              </View>
            )}

            <TouchableOpacity
              style={styles.retryButton}
              onPress={this.handleReset}
              {...makeAccessibleButton('Tentar novamente', 'Tenta recarregar a interface')}
            >
              <Ionicons name="refresh-outline" size={20} color={theme.colors.onPrimary} />
              <Text style={styles.retryButtonText}>Tentar novamente</Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.surfaceBackground,
  },
  container: {
    flexGrow: 1,
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.errorContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    ...theme.typography.headlineMd,
    color: theme.colors.brandDeep,
    textAlign: 'center',
    marginBottom: 12,
  },
  message: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurfaceVariant,
    textAlign: 'center',
    marginBottom: 24,
    maxWidth: 320,
    lineHeight: 22,
  },
  devErrorBox: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: theme.colors.surfaceContainerLow,
    padding: 16,
    borderRadius: theme.radii.md,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(186, 26, 26, 0.2)',
  },
  devErrorTitle: {
    ...theme.typography.labelMd,
    color: theme.colors.error,
    fontWeight: '700',
    marginBottom: 6,
  },
  devErrorText: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurface,
    fontFamily: 'monospace',
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    height: 48,
    paddingHorizontal: 24,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.brandForest,
    ...theme.shadows.sm,
  },
  retryButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
  },
});
