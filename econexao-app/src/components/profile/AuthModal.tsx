import React, { useRef, useState } from 'react';
import {
  AccessibilityInfo,
  ActivityIndicator,
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
import { AccessibleModal } from '../common/AccessibleModal';

interface AuthModalProps {
  visible: boolean;
  onClose: () => void;
  returnFocusRef?: React.RefObject<any>;
}

type AuthMode = 'link' | 'signin' | 'signup' | 'recovery';

export const AuthModal: React.FC<AuthModalProps> = ({ visible, onClose, returnFocusRef }) => {
  const {
    user,
    linkAccount,
    signInWithPassword,
    signUp,
    resetPassword,
    signInWithGoogle,
    linkGoogleAccount,
    isIdentityConflictError,
    clearGuestFavoritesSnapshot,
  } = useAuth();
  const isAnonymous = user ? (user.is_anonymous === true && !user.email) : true;
  const closeButtonRef = useRef<React.ElementRef<typeof TouchableOpacity>>(null);

  const [mode, setMode] = useState<AuthMode>(isAnonymous ? 'link' : 'signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isConflictDetected, setIsConflictDetected] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const resetState = () => {
    setEmail('');
    setPassword('');
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsConflictDetected(false);
    setIsLoading(false);
    setIsGoogleLoading(false);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleGoogleAuth = async () => {
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsConflictDetected(false);
    setIsGoogleLoading(true);

    try {
      AccessibilityInfo.announceForAccessibility(
        mode === 'link' ? 'Iniciando vinculação com o Google...' : 'Iniciando login com o Google...'
      );

      if (mode === 'link') {
        await linkGoogleAccount();
        setSuccessMessage('Redirecionando para vincular com o Google...');
        AccessibilityInfo.announceForAccessibility('Redirecionando para vincular com o Google.');
      } else {
        await signInWithGoogle();
        setSuccessMessage('Redirecionando para login com o Google...');
        AccessibilityInfo.announceForAccessibility('Redirecionando para login com o Google.');
      }
    } catch (err: any) {
      if (isIdentityConflictError(err)) {
        setIsConflictDetected(true);
        setErrorMessage(
          'Esta conta Google já possui cadastro no ECOnexão. Conforme a política de privacidade, os dados desta sessão de visitante não serão vinculados à conta antiga.'
        );
        AccessibilityInfo.announceForAccessibility('Conta existente detectada.');
      } else if (err?.message?.includes('cancel') || err?.message?.includes('denied')) {
        setErrorMessage('Autenticação com o Google cancelada.');
        AccessibilityInfo.announceForAccessibility('Autenticação com o Google cancelada.');
      } else {
        const msg = err?.message || 'Falha na autenticação com o Google. Tente novamente.';
        setErrorMessage(msg);
        AccessibilityInfo.announceForAccessibility(msg);
      }
    } finally {
      setIsGoogleLoading(false);
    }
  };

  const handleSwitchToExistingAccount = async () => {
    await clearGuestFavoritesSnapshot();
    setIsConflictDetected(false);
    setErrorMessage(null);
    setIsGoogleLoading(true);

    try {
      AccessibilityInfo.announceForAccessibility('Entrando na conta existente com o Google...');
      await signInWithGoogle();
      setSuccessMessage('Entrando na sua conta Google existente...');
    } catch (err: any) {
      const msg = err?.message || 'Falha ao entrar na conta existente com o Google.';
      setErrorMessage(msg);
      AccessibilityInfo.announceForAccessibility(msg);
    } finally {
      setIsGoogleLoading(false);
    }
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
    <AccessibleModal
      visible={visible}
      transparent
      animationType="slide"
      onClose={handleClose}
      initialFocusRef={closeButtonRef}
      returnFocusRef={returnFocusRef}
      accessibilityLabel="Autenticação e cadastro ECOnexão"
    >
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
              ref={closeButtonRef}
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
            <View style={styles.errorContainer} accessibilityRole="alert">
              <Ionicons name="alert-circle" size={18} color="#991B1B" />
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          {isConflictDetected && (
            <TouchableOpacity
              style={styles.conflictActionButton}
              onPress={handleSwitchToExistingAccount}
              disabled={isGoogleLoading}
              {...makeAccessibleButton(
                'Fazer login na conta existente',
                'Descarta os dados temporários de visitante e entra na conta Google existente'
              )}
              accessibilityState={{ busy: isGoogleLoading, disabled: isGoogleLoading }}
            >
              <Text style={styles.conflictActionText}>Fazer Login na Conta Existente</Text>
            </TouchableOpacity>
          )}

          {successMessage && (
            <View style={styles.successContainer} accessibilityRole="alert">
              <Ionicons name="checkmark-circle" size={18} color="#065F46" />
              <Text style={styles.successText}>{successMessage}</Text>
            </View>
          )}

          {mode !== 'recovery' && (
            <>
              <TouchableOpacity
                style={[
                  styles.googleButton,
                  (isGoogleLoading || isLoading) && styles.googleButtonDisabled,
                ]}
                onPress={handleGoogleAuth}
                disabled={isGoogleLoading || isLoading}
                {...makeAccessibleButton(
                  mode === 'link'
                    ? 'Salvar conta com o Google'
                    : mode === 'signup'
                    ? 'Cadastrar com o Google'
                    : 'Entrar com o Google',
                  'Inicia fluxo seguro de autenticação com sua conta Google'
                )}
                accessibilityState={{
                  busy: isGoogleLoading,
                  disabled: isGoogleLoading || isLoading,
                }}
              >
                {isGoogleLoading ? (
                  <ActivityIndicator size="small" color={theme.colors.brandForest} />
                ) : (
                  <View style={styles.googleButtonContent}>
                    <Ionicons name="logo-google" size={18} color="#EA4335" />
                    <Text style={styles.googleButtonText}>
                      {mode === 'link'
                        ? 'Salvar com o Google'
                        : mode === 'signup'
                        ? 'Cadastrar com o Google'
                        : 'Entrar com o Google'}
                    </Text>
                  </View>
                )}
              </TouchableOpacity>

              <View style={styles.dividerRow}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>ou continue com e-mail</Text>
                <View style={styles.dividerLine} />
              </View>
            </>
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
    </AccessibleModal>
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
  conflictActionButton: {
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#F59E0B',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: theme.radii.md,
    alignItems: 'center',
    marginBottom: 12,
  },
  conflictActionText: {
    color: '#92400E',
    fontWeight: '700',
    fontSize: 13,
  },
  googleButton: {
    backgroundColor: theme.colors.surfaceWhite,
    borderWidth: 1.5,
    borderColor: 'rgba(117, 155, 113, 0.35)',
    borderRadius: theme.radii.md,
    paddingVertical: 11,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
    ...theme.shadows.card,
  },
  googleButtonDisabled: {
    opacity: 0.6,
  },
  googleButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  googleButtonText: {
    color: theme.colors.brandDeep,
    fontSize: 14,
    fontWeight: '700',
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 10,
    gap: 10,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(117, 155, 113, 0.2)',
  },
  dividerText: {
    fontSize: 12,
    color: theme.colors.onSurfaceVariant,
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
