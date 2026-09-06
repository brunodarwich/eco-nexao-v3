import React from 'react';
import renderer, { act } from 'react-test-renderer';

import { AuthModal } from './AuthModal';
import { useAuth } from '../../hooks/useAuth';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));

jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

describe('ECO-1902 / ECO-2606 — Autenticação, Login Google e Linking (AuthModal)', () => {
  const mockLinkAccount = jest.fn();
  const mockSignInWithPassword = jest.fn();
  const mockSignUp = jest.fn();
  const mockResetPassword = jest.fn();
  const mockSignInWithGoogle = jest.fn();
  const mockLinkGoogleAccount = jest.fn();
  const mockClearGuestFavoritesSnapshot = jest.fn();
  const mockIsIdentityConflictError = jest.fn((err: any) => {
    const msg = String(err?.message || err).toLowerCase();
    return msg.includes('already') || msg.includes('conflict');
  });
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    (useAuth as jest.Mock).mockReturnValue({
      user: { id: 'guest-uuid-1', is_anonymous: true },
      linkAccount: mockLinkAccount,
      signInWithPassword: mockSignInWithPassword,
      signUp: mockSignUp,
      resetPassword: mockResetPassword,
      signInWithGoogle: mockSignInWithGoogle,
      linkGoogleAccount: mockLinkGoogleAccount,
      clearGuestFavoritesSnapshot: mockClearGuestFavoritesSnapshot,
      isIdentityConflictError: mockIsIdentityConflictError,
    });
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  test('renderiza modal em modo Salvar Conta quando usuário é anônimo', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const textNodes = tree.root.findAllByType('Text' as any).flatMap((n) => n.props.children);
    expect(textNodes).toContain('Salvar Minha Conta');
    expect(textNodes).toContain('Salvar Conta');
  });

  test('executa linkAccount preservando UUID do guest ao salvar conta', async () => {
    mockLinkAccount.mockResolvedValue(undefined);

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const inputs = tree.root.findAllByType('TextInput' as any);
    const emailInput = inputs[0];
    const passwordInput = inputs[1];

    await act(async () => {
      emailInput.props.onChangeText('turista@exemplo.com');
      passwordInput.props.onChangeText('senhaSegura123');
    });

    const submitButton = tree.root.findByProps({ accessibilityLabel: 'Salvar conta' });
    await act(async () => {
      submitButton.props.onPress();
    });
    act(() => {
      jest.runAllTimers();
    });

    expect(mockLinkAccount).toHaveBeenCalledWith('turista@exemplo.com', 'senhaSegura123');
  });

  test('informa conflito e orienta login quando e-mail já existe', async () => {
    mockLinkAccount.mockRejectedValue(new Error('user_already_exists'));

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const inputs = tree.root.findAllByType('TextInput' as any);
    await act(async () => {
      inputs[0].props.onChangeText('existente@exemplo.com');
      inputs[1].props.onChangeText('senhaSegura123');
    });

    const submitButton = tree.root.findByProps({ accessibilityLabel: 'Salvar conta' });
    await act(async () => {
      submitButton.props.onPress();
    });

    const textNodes = tree.root.findAllByType('Text' as any).flatMap((n) => n.props.children);
    expect(textNodes.join(' ')).toContain('Este e-mail já possui cadastro');
  });

  test('permite alternar para aba Entrar e executar signInWithPassword', async () => {
    mockSignInWithPassword.mockResolvedValue({ user: { id: 'user-auth-1' } });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    // Clica na tab Entrar
    const signinTab = tree.root.findByProps({ accessibilityLabel: 'Aba Entrar' });
    await act(async () => {
      signinTab.props.onPress();
    });

    const inputs = tree.root.findAllByType('TextInput' as any);
    await act(async () => {
      inputs[0].props.onChangeText('cadastrado@exemplo.com');
      inputs[1].props.onChangeText('senha123');
    });

    const submitButton = tree.root.findByProps({ accessibilityLabel: 'Entrar' });
    await act(async () => {
      submitButton.props.onPress();
    });
    act(() => {
      jest.runAllTimers();
    });

    expect(mockSignInWithPassword).toHaveBeenCalledWith('cadastrado@exemplo.com', 'senha123');
  });

  test('renderiza botão Salvar com o Google quando em modo Salvar Conta', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const googleBtn = tree.root.findByProps({ accessibilityLabel: 'Salvar conta com o Google' });
    expect(googleBtn).toBeDefined();
    const textNodes = tree.root.findAllByType('Text' as any).flatMap((n) => n.props.children);
    expect(textNodes).toContain('Salvar com o Google');
  });

  test('executa linkGoogleAccount ao acionar o botão Google no modo Salvar Conta', async () => {
    mockLinkGoogleAccount.mockResolvedValue({ url: 'https://accounts.google.com/...' });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const googleBtn = tree.root.findByProps({ accessibilityLabel: 'Salvar conta com o Google' });
    await act(async () => {
      googleBtn.props.onPress();
    });

    act(() => {
      jest.runAllTimers();
    });

    expect(mockLinkGoogleAccount).toHaveBeenCalledTimes(1);
  });

  test('alterna para aba Entrar e executa signInWithGoogle', async () => {
    mockSignInWithGoogle.mockResolvedValue({ url: 'https://accounts.google.com/...' });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const signinTab = tree.root.findByProps({ accessibilityLabel: 'Aba Entrar' });
    await act(async () => {
      signinTab.props.onPress();
    });

    const googleBtn = tree.root.findByProps({ accessibilityLabel: 'Entrar com o Google' });
    await act(async () => {
      googleBtn.props.onPress();
    });

    expect(mockSignInWithGoogle).toHaveBeenCalledTimes(1);
  });

  test('trata conflito de conta Google existente segundo ADR 0007 e permite login descartando dados guest', async () => {
    mockLinkGoogleAccount.mockRejectedValue(new Error('identity_already_exists'));
    mockSignInWithGoogle.mockResolvedValue({ url: 'https://accounts.google.com/...' });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const googleBtn = tree.root.findByProps({ accessibilityLabel: 'Salvar conta com o Google' });
    await act(async () => {
      googleBtn.props.onPress();
    });

    const textNodes = tree.root.findAllByType('Text' as any).flatMap((n) => n.props.children);
    expect(textNodes.join(' ')).toContain('Esta conta Google já possui cadastro no ECOnexão');

    // Botão de resolução de conflito segundo ADR 0007
    const conflictBtn = tree.root.findByProps({ accessibilityLabel: 'Fazer login na conta existente' });
    expect(conflictBtn).toBeDefined();

    await act(async () => {
      conflictBtn.props.onPress();
    });

    // Garante que o snapshot guest foi descartado para isolamento A/B e o login na conta antiga foi chamado
    expect(mockClearGuestFavoritesSnapshot).toHaveBeenCalledTimes(1);
    expect(mockSignInWithGoogle).toHaveBeenCalledTimes(1);
  });

  test('trata cancelamento gracioso de autenticação Google', async () => {
    mockLinkGoogleAccount.mockRejectedValue(new Error('Autenticacao cancelada pelo usuario'));

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AuthModal visible={true} onClose={mockOnClose} />);
    });

    const googleBtn = tree.root.findByProps({ accessibilityLabel: 'Salvar conta com o Google' });
    await act(async () => {
      googleBtn.props.onPress();
    });

    const textNodes = tree.root.findAllByType('Text' as any).flatMap((n) => n.props.children);
    expect(textNodes.join(' ')).toContain('Autenticação com o Google cancelada');
  });
});

