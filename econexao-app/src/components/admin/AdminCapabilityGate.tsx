import React from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { ApiClientError } from '../../api/client';
import { useAdminContextQuery } from '../../hooks/queries';
import { AccessDeniedView } from './AccessDeniedView';

export interface AdminCapabilityGateProps {
  requiredCapability?: string;
  requiredRole?: string;
  isAuthenticated?: boolean;
  onGoHome?: () => void;
  onLoginRequest?: () => void;
  onRetry?: () => void;
  children: React.ReactNode;
}

export const AdminCapabilityGate: React.FC<AdminCapabilityGateProps> = ({
  requiredCapability,
  requiredRole,
  isAuthenticated = true,
  onGoHome,
  onLoginRequest,
  onRetry,
  children,
}) => {
  const { data: adminContext, isLoading, isError, error, refetch } = useAdminContextQuery(isAuthenticated);

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    } else {
      void refetch();
    }
  };

  if (isLoading) {
    return (
      <View
        style={styles.loadingContainer}
        accessibilityRole="progressbar"
        accessibilityLabel="Verificando permissões editoriais..."
      >
        <ActivityIndicator size="large" color="#059669" />
        <Text style={styles.loadingText}>Verificando permissões editoriais...</Text>
      </View>
    );
  }

  if (!isAuthenticated) {
    return (
      <AccessDeniedView
        title="Autenticação Necessária"
        message="Faça login com uma conta editorial autorizada para acessar este painel."
        onGoHome={onGoHome}
        onLoginRequest={onLoginRequest}
      />
    );
  }

  if (isError) {
    const isForbidden =
      error instanceof ApiClientError && (error.status === 403 || error.status === 401);

    if (isForbidden) {
      return (
        <AccessDeniedView
          title="Acesso Negado (403)"
          message="Sua sessão anônima ou conta não possui credenciais suficientes para a área editorial."
          onGoHome={onGoHome}
          onLoginRequest={onLoginRequest}
        />
      );
    }

    // Erro de rede ou 5xx recuperável
    return (
      <View
        style={styles.errorContainer}
        accessibilityRole="alert"
        accessibilityLabel="Erro de Conexão Editorial. Não foi possível validar o contexto editorial no servidor."
      >
        <View style={styles.errorCard}>
          <View style={styles.errorBadge}>
            <Text style={styles.errorBadgeText}>FALHA DE CONEXÃO</Text>
          </View>
          <Text style={styles.errorTitle}>Erro de Conexão Editorial</Text>
          <Text style={styles.errorMessage}>
            Não foi possível validar o contexto editorial no servidor. Verifique sua conexão e tente novamente.
          </Text>

          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.button, styles.retryButton]}
              onPress={handleRetry}
              accessibilityRole="button"
              accessibilityLabel="Tentar reconectar com o servidor editorial"
            >
              <Text style={styles.retryButtonText}>Tentar Novamente</Text>
            </TouchableOpacity>

            {onGoHome && (
              <TouchableOpacity
                style={[styles.button, styles.secondaryButton]}
                onPress={onGoHome}
                accessibilityRole="button"
                accessibilityLabel="Voltar ao início do aplicativo público"
              >
                <Text style={styles.secondaryButtonText}>Voltar ao App Público</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </View>
    );
  }

  if (!adminContext) {
    return (
      <AccessDeniedView
        title="Acesso Negado (403)"
        message="Sua sessão anônima ou conta comum não possui credenciais para a área editorial."
        onGoHome={onGoHome}
        onLoginRequest={onLoginRequest}
      />
    );
  }

  const scopes = adminContext?.access?.scopes || [];
  const userCapabilities = Array.from(new Set(scopes.flatMap((s) => s.capabilities || [])));
  const userRoles = Array.from(new Set(scopes.flatMap((s) => s.roles || [])));

  if (requiredCapability && !userCapabilities.includes(requiredCapability)) {
    return (
      <AccessDeniedView
        title="Permissão Insuficiente (403)"
        message={`Sua conta editorial precisa da permissão '${requiredCapability}' para esta funcionalidade.`}
        onGoHome={onGoHome}
        onLoginRequest={onLoginRequest}
      />
    );
  }

  if (requiredRole && !userRoles.includes(requiredRole)) {
    return (
      <AccessDeniedView
        title="Papel Editorial Necessário (403)"
        message={`Esta operação exige o papel de '${requiredRole}'.`}
        onGoHome={onGoHome}
        onLoginRequest={onLoginRequest}
      />
    );
  }

  return <>{children}</>;
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
    color: '#475569',
    fontWeight: '500',
  },
  errorContainer: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 32,
    maxWidth: 480,
    width: '100%',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 3,
  },
  errorBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 16,
  },
  errorBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#D97706',
    letterSpacing: 0.5,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0F172A',
    textAlign: 'center',
    marginBottom: 12,
  },
  errorMessage: {
    fontSize: 15,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  buttonContainer: {
    width: '100%',
    gap: 12,
  },
  button: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 10,
    alignItems: 'center',
  },
  retryButton: {
    backgroundColor: '#059669',
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#F1F5F9',
  },
  secondaryButtonText: {
    color: '#334155',
    fontSize: 15,
    fontWeight: '600',
  },
});

