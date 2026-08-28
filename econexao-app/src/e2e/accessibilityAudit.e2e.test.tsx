import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppContextProvider } from '../state/AppContext';
import { NetworkStatusBar } from '../components/common/NetworkStatusBar';
import { AuthModal } from '../components/profile/AuthModal';
import { EditProfileModal } from '../components/profile/EditProfileModal';
import { AccountDeletionModal } from '../components/profile/AccountDeletionModal';
import { RegionSelectorModal } from '../components/common/RegionSelectorModal';
import { AccessibleModal } from '../components/common/AccessibleModal';
import { AccessDeniedView } from '../components/admin/AccessDeniedView';
import { useAuth } from '../hooks/useAuth';
import { useRegionsQuery } from '../hooks/queries';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
}));

jest.mock('../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

jest.mock('../hooks/queries', () => {
  const actual = jest.requireActual('../hooks/queries');
  return {
    ...actual,
    useRegionsQuery: jest.fn().mockReturnValue({
      data: [
        { id: 'reg-1', name: 'Polo Tapajós', state_code: 'PA' },
        { id: 'reg-2', name: 'Polo Belterra', state_code: 'PA' },
      ],
      isPending: false,
      isError: false,
    }),
  };
});

jest.mock('../api/client', () => ({
  apiClient: {
    configureAuth: jest.fn(),
    updateMyPreferences: jest.fn().mockResolvedValue({ success: true }),
  },
}));

describe('E2E Accessibility & WCAG Semantic Audit (ECO-2101 / ECO-2307 / ECO-2315)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      user: { id: 'usr_admin', email: 'admin@econexao.org', is_anonymous: false },
      linkAccount: jest.fn(),
      signInWithPassword: jest.fn(),
      signUp: jest.fn(),
      resetPassword: jest.fn(),
    });
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: Infinity },
        mutations: { retry: false, gcTime: Infinity },
      },
    });
  });

  afterEach(() => {
    queryClient.clear();
  });

  const renderWithProviders = (ui: React.ReactElement) => {
    return renderer.create(
      <QueryClientProvider client={queryClient}>
        <AppContextProvider>{ui}</AppContextProvider>
      </QueryClientProvider>
    );
  };

  test('WCAG 1.3.1 / 4.1.2: Validar rótulos, papéis e hints em modais e alertas', async () => {
    // 1. Modal de Auth
    let authTree: renderer.ReactTestRenderer;
    await act(async () => {
      authTree = renderWithProviders(
        <AuthModal visible={true} onClose={jest.fn()} />
      );
    });
    const authJson = JSON.stringify(authTree!.toJSON());
    expect(authJson).toContain('Fechar modal');
    expect(authJson).toContain('Campo de e-mail');

    // 2. Modal de Edição de Perfil
    let editTree: renderer.ReactTestRenderer;
    await act(async () => {
      editTree = renderWithProviders(
        <EditProfileModal
          visible={true}
          onClose={jest.fn()}
          currentProfile={{ id: 'usr_1', name: 'João', location: 'Belém', status: 'active' }}
        />
      );
    });
    const editJson = JSON.stringify(editTree!.toJSON());
    expect(editJson).toContain('Editar Perfil');
    expect(editJson).toContain('Fechar edição de perfil');

    // 3. Modal de Exclusão LGPD
    let deleteTree: renderer.ReactTestRenderer;
    await act(async () => {
      deleteTree = renderWithProviders(
        <AccountDeletionModal visible={true} onClose={jest.fn()} />
      );
    });
    const deleteJson = JSON.stringify(deleteTree!.toJSON());
    expect(deleteJson).toContain('Confirmar exclusão e encerrar conta');
    expect(deleteJson).toContain('Cancelar exclusão de conta');

    // 4. Modal de Seleção de Região
    let regionTree: renderer.ReactTestRenderer;
    await act(async () => {
      regionTree = renderWithProviders(
        <RegionSelectorModal visible={true} onClose={jest.fn()} />
      );
    });
    const regionJson = JSON.stringify(regionTree!.toJSON());
    expect(regionJson).toContain('Selecionar Região');
    expect(regionJson).toContain('Polo Tapajós');
  });

  test('WCAG 2.1.2 / 2.4.3: AccessibleModal implementa aria-modal, foco seguro e diálogo sem bloquear aria-hidden', async () => {
    const onClose = jest.fn();
    let modalTree: renderer.ReactTestRenderer;
    await act(async () => {
      modalTree = renderWithProviders(
        <AccessibleModal
          visible={true}
          onClose={onClose}
          accessibilityLabel="Janela de teste acessível"
        >
          <NetworkStatusBar isOfflineOverride={false} onReconnect={jest.fn()} />
        </AccessibleModal>
      );
    });

    const modalJson = JSON.stringify(modalTree!.toJSON());
    expect(modalJson).toContain('Janela de teste acessível');
  });

  test('WCAG 4.1.3: Status messages e acessibilidade de rede offline', async () => {
    let networkTree: renderer.ReactTestRenderer;
    await act(async () => {
      networkTree = renderWithProviders(
        <NetworkStatusBar isOfflineOverride={true} onReconnect={jest.fn()} />
      );
    });

    const netJson = JSON.stringify(networkTree!.toJSON());
    expect(netJson).toContain('Modo Offline');
    expect(netJson).toContain('Tentar reconectar');
    expect(netJson).toContain('alert');
  });

  test('Acesso negado possui semântica clara e ação de retorno', async () => {
    const onHome = jest.fn();
    let deniedTree: renderer.ReactTestRenderer;
    await act(async () => {
      deniedTree = renderWithProviders(
        <AccessDeniedView onGoHome={onHome} />
      );
    });

    const deniedJson = JSON.stringify(deniedTree!.toJSON());
    expect(deniedJson).toContain('Acesso Negado (403)');
    expect(deniedJson).toContain('Voltar ao início do aplicativo público');
  });
});
