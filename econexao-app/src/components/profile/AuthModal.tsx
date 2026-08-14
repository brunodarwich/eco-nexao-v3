import React, { useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useAuth } from '../../hooks/useAuth';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';

interface AuthModalProps {
  visible: boolean;
  onClose: () => void;
}

type AuthMode = 'link' | 'signin' | 'signup' | 'recovery';

export const AuthModal: React.FC<AuthModalProps> = ({ visible, onClose }) => {
  const { user, linkAccount, signInWithPassword, signUp, resetPassword } = useAuth();
  const isAnonymous = user?.is_anonymous ?? true;

  const [mode, setMode] = useState<AuthMode>(isAnonymous ? 'link' : 'signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const resetState = () => {
    setEmail('');
    setPassword('');
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsLoading(false);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleSubmit = async () => {
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@')) {
      setErrorMessage('Informe um e-mail válido.');
      return;
    }

    if (mode !== 'recovery' && password.length < 6) {
      setErrorMessage('A senha deve conter no mínimo 6 caracteres.');
      return;
    }

    setIsLoading(true);
    try {
      if (mode === 'link') {
        await linkAccount(cleanEmail, password);
        setSuccessMessage('Conta vinculada com sucesso! Seus favoritos foram preservados.');
        setTimeout(() => handleClose(), 1500);
      } else if (mode === 'signin') {
        await signInWithPassword(cleanEmail, password);
        setSuccessMessage('Login realizado com sucesso!');
        setTimeout(() => handleClose(), 1200);
      } else if (mode === 'signup') {
        await signUp(cleanEmail, password);
        setSuccessMessage('Cadastro realizado com sucesso!');
        setTimeout(() => handleClose(), 1500);
      } else if (mode === 'recovery') {
        await resetPassword(cleanEmail);
        setSuccessMessage('E-mail de recuperação enviado! Verifique sua caixa de entrada.');
      }
    } catch (err: any) {
      const msg = err?.message || 'Ocorreu um erro ao processar a autenticação.';
      if (msg.includes('user_already_exists') || msg.includes('already registered')) {
        setErrorMessage('Este e-mail já possui cadastro. Alterne para a aba "Entrar" para acessar.');
      } else if (msg.includes('Invalid login credentials')) {
        setErrorMessage('E-mail ou senha incorretos. Verifique suas credenciais.');
      } else {
        setErrorMessage(msg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={handleClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.header}>
            <View style={styles.headerTitleRow}>
              <Ionicons
                name={mode === 'recovery' ? 'key-outline' : 'person-circle-outline'}
                size={28}
                color={theme.colors.brandForest}
              />
              <Text style={styles.title}>
                {mode === 'link'
                  ? 'Salvar Minha Conta'
                  : mode === 'signin'
                  ? 'Entrar no ECOnexão'
                  : mode === 'signup'
                  ? 'Criar Nova Conta'
                  : 'Recuperar Senha'}
              </Text>
            </View>
            <TouchableOpacity
              onPress={handleClose}
              style={styles.closeButton}
              {...makeAccessibleButton('Fechar modal de autenticação')}
            >
              <Ionicons name="close" size={24} color={theme.colors.onSurfaceVariant} />
            </TouchableOpacity>
          </View>

          {/* Mode Selector Tabs */}
          {mode !== 'recovery' && (
            <View style={styles.tabRow}>
              {isAnonymous && (
                <TouchableOpacity
                  style={[styles.tab, mode === 'link' && styles.activeTab]}
                  onPress={() => {
                    setMode('link');
                    setErrorMessage(null);
                  }}
                  accessibilityRole="tab"
                  accessibilityLabel="Aba Salvar Conta"
                  accessibilityState={{ selected: mode === 'link' }}
                >
                  <Text style={[styles.tabText, mode === 'link' && styles.activeTabText]}>
                    Salvar Conta
                  </Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity
                style={[styles.tab, mode === 'signin' && styles.activeTab]}
                onPress={() => {
                  setMode('signin');
                  setErrorMessage(null);
                }}
                accessibilityRole="tab"
                accessibilityLabel="Aba Entrar"
                accessibilityState={{ selected: mode === 'signin' }}
              >
                <Text style={[styles.tabText, mode === 'signin' && styles.activeTabText]}>
                  Entrar
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, mode === 'signup' && styles.activeTab]}
                onPress={() => {
                  setMode('signup');
                  setErrorMessage(null);
                }}
                accessibilityRole="tab"
                accessibilityLabel="Aba Cadastrar"
                accessibilityState={{ selected: mode === 'signup' }}
              >
                <Text style={[styles.tabText, mode === 'signup' && styles.activeTabText]}>
                  Cadastrar
                </Text>
              </TouchableOpacity>
            </View>
          )}

          {mode === 'link' && (
            <Text style={styles.infoText}>
              Adicione um e-mail e senha para salvar suas rotas favoritadas e histórico de viagens permanentemente.
            </Text>
          )}

          {errorMessage && (
            <View style={styles.errorContainer}>
              <Ionicons name="alert-circle" size={18} color="#991B1B" />
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          {successMessage && (
            <View style={styles.successContainer}>
              <Ionicons name="checkmark-circle" size={18} color="#065F46" />
              <Text style={styles.successText}>{successMessage}</Text>
            </View>
          )}

          <View style={styles.form}>
            <Text style={styles.label}>E-mail</Text>
            <TextInput
              style={styles.input}
              placeholder="seuemail@exemplo.com"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              accessibilityLabel="Campo de e-mail"
            />

            {mode !== 'recovery' && (
              <>
                <Text style={styles.label}>Senha</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Mínimo 6 caracteres"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  autoCapitalize="none"
                  accessibilityLabel="Campo de senha"
                />
              </>
            )}

            {mode === 'signin' && (
              <TouchableOpacity
                style={styles.forgotButton}
                onPress={() => {
                  setMode('recovery');
                  setErrorMessage(null);
                }}
              >
                <Text style={styles.forgotText}>Esqueceu a senha?</Text>
              </TouchableOpacity>
            )}

            {mode === 'recovery' && (
              <TouchableOpacity
                style={styles.forgotButton}
                onPress={() => {
                  setMode('signin');
                  setErrorMessage(null);
                }}
              >
                <Text style={styles.forgotText}>Voltar para o login</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={styles.submitButton}
              onPress={handleSubmit}
              disabled={isLoading}
              accessibilityRole="button"
              accessibilityLabel={
                mode === 'link'
                  ? 'Salvar conta'
                  : mode === 'signin'
                  ? 'Entrar'
                  : mode === 'signup'
                  ? 'Cadastrar'
                  : 'Enviar e-mail de recuperação'
              }
            >
              {isLoading ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.submitText}>
                  {mode === 'link'
                    ? 'Salvar Conta e Favoritos'
                    : mode === 'signin'
                    ? 'Entrar'
                    : mode === 'signup'
                    ? 'Cadastrar'
                    : 'Enviar Link de Recuperação'}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.marginMobile,
  },
  card: {
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.xl,
    padding: 20,
    width: '100%',
    maxWidth: 420,
    ...theme.shadows.card,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.brandDeep,
  },
  closeButton: {
    padding: 4,
  },
  tabRow: {
    flexDirection: 'row',
    backgroundColor: theme.colors.surfaceContainerLow,
    borderRadius: theme.radii.md,
    padding: 4,
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: theme.radii.sm,
  },
  activeTab: {
    backgroundColor: theme.colors.surfaceWhite,
    ...theme.shadows.card,
  },
  tabText: {
    fontSize: 13,
    color: theme.colors.onSurfaceVariant,
    fontWeight: '500',
  },
  activeTabText: {
    color: theme.colors.brandForest,
    fontWeight: '700',
  },
  infoText: {
    fontSize: 13,
    color: theme.colors.onSurfaceVariant,
    marginBottom: 12,
    lineHeight: 18,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEE2E2',
    padding: 10,
    borderRadius: theme.radii.md,
    marginBottom: 12,
  },
  errorText: {
    color: '#991B1B',
    fontSize: 13,
    flex: 1,
  },
  successContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#D1FAE5',
    padding: 10,
    borderRadius: theme.radii.md,
    marginBottom: 12,
  },
  successText: {
    color: '#065F46',
    fontSize: 13,
    flex: 1,
  },
  form: {
    gap: 12,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.brandDeep,
    marginBottom: -4,
  },
  input: {
    backgroundColor: theme.colors.surfaceContainerLow,
    borderRadius: theme.radii.md,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: theme.colors.onSurface,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
  },
  forgotButton: {
    alignSelf: 'flex-end',
    paddingVertical: 4,
  },
  forgotText: {
    fontSize: 12,
    color: theme.colors.brandForest,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: theme.colors.brandForest,
    borderRadius: theme.radii.md,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 6,
  },
  submitText: {
    color: theme.colors.surfaceWhite,
    fontSize: 15,
    fontWeight: '700',
  },
});
