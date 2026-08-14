import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

export interface AccessDeniedViewProps {
  title?: string;
  message?: string;
  onGoHome?: () => void;
  onLoginRequest?: () => void;
}

export const AccessDeniedView: React.FC<AccessDeniedViewProps> = ({
  title = 'Acesso Negado (403)',
  message = 'Você não possui permissões editoriais suficientes para acessar esta funcionalidade.',
  onGoHome,
  onLoginRequest,
}) => {
  return (
    <View
      style={styles.container}
      accessibilityRole="header"
      accessibilityLabel={`${title}. ${message}`}
    >
      <View style={styles.card}>
        <Text style={styles.badgeText}>SEM AUTORIZAÇÃO</Text>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.message}>{message}</Text>

        <View style={styles.buttonContainer}>
          {onGoHome && (
            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={onGoHome}
              accessibilityRole="button"
              accessibilityLabel="Voltar ao início do aplicativo público"
            >
              <Text style={styles.primaryButtonText}>Voltar ao Início</Text>
            </TouchableOpacity>
          )}

          {onLoginRequest && (
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={onLoginRequest}
              accessibilityRole="button"
              accessibilityLabel="Fazer login com conta editorial"
            >
              <Text style={styles.secondaryButtonText}>Entrar com Conta Editorial</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 32,
    maxWidth: 480,
    width: '100%',
    alignItems: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#DC2626',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
    textAlign: 'center',
    marginBottom: 12,
  },
  message: {
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
  primaryButton: {
    backgroundColor: '#059669',
  },
  primaryButtonText: {
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
