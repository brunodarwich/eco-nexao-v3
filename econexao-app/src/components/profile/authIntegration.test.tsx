import React from 'react';
import renderer, { act } from 'react-test-renderer';

import { AuthModal } from './AuthModal';
import { useAuth } from '../../hooks/useAuth';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));

jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

describe('ECO-1902 — Cadastro, Login, Linking e Ciclo de Sessão (AuthModal)', () => {
  const mockLinkAccount = jest.fn();
  const mockSignInWithPassword = jest.fn();
  const mockSignUp = jest.fn();
  const mockResetPassword = jest.fn();
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
});

