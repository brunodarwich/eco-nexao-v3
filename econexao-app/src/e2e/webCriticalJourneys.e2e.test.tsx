import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppContextProvider } from '../state/AppContext';
import { AdminShell } from '../components/admin/AdminShell';
import { TerritoryEditor } from '../components/admin/TerritoryEditor';
import { ActorEditor } from '../components/admin/ActorEditor';
import { WorkflowReviewQueue } from '../components/admin/WorkflowReviewQueue';
import { AuditLogViewer } from '../components/admin/AuditLogViewer';
import { AuthModal } from '../components/profile/AuthModal';
import { EditProfileModal } from '../components/profile/EditProfileModal';
import { AccountDeletionModal } from '../components/profile/AccountDeletionModal';
import { useAuth } from '../hooks/useAuth';
import { useAdminContextQuery } from '../hooks/queries';
import { apiClient } from '../api/client';

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
    useAdminContextQuery: jest.fn(),
  };
});

jest.mock('../api/client', () => ({
  apiClient: {
    configureAuth: jest.fn(),
    getAdminContext: jest.fn(),
    getAdminRegions: jest.fn().mockResolvedValue({ data: [] }),
    getAdminRoutes: jest.fn().mockResolvedValue({ data: [] }),
    getAdminActors: jest.fn().mockResolvedValue({ data: [] }),
    getReviewQueue: jest.fn().mockResolvedValue({ data: [] }),
    getReconciliationCandidates: jest.fn().mockResolvedValue({ data: [] }),
    getCommunityAlerts: jest.fn().mockResolvedValue({ data: [] }),
    getAuditLogs: jest.fn().mockResolvedValue({ data: [] }),
    updateMyProfile: jest.fn(),
    deleteMyAccount: jest.fn(),
    createTrip: jest.fn(),
    listRoutes: jest.fn(),
    listActors: jest.fn(),
  },
}));

describe('E2E Web - Critical User Journeys (ECO-2101)', () => {
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
    (useAdminContextQuery as jest.Mock).mockReturnValue({
      data: {
        access: {
          scopes: [
            {
              role: 'admin',
              roles: ['admin'],
              capabilities: ['territory.read', 'territory.write', 'actor.write', 'content.publish', 'content.archive'],
            },
          ],
        },
      },
      isLoading: false,
      isError: false,
    });
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });
  });

  const renderWithProviders = (ui: React.ReactElement) => {
    return renderer.create(
      <QueryClientProvider client={queryClient}>
        <AppContextProvider>{ui}</AppContextProvider>
      </QueryClientProvider>
    );
  };

  test('Jornada 1: Fluxo de Autenticação, Edição de Perfil e LGPD', async () => {
    const onCloseAuth = jest.fn();

    // 1. Renderiza modal de autenticação
    let authTree: renderer.ReactTestRenderer;
    await act(async () => {
      authTree = renderWithProviders(
        <AuthModal
          visible={true}
          onClose={onCloseAuth}
        />
      );
    });
    const authJson = JSON.stringify(authTree!.toJSON());
    expect(authJson).toContain('Entrar no ECOnexão');

    // 2. Renderiza modal de edição de perfil
    (apiClient.updateMyProfile as jest.Mock).mockResolvedValueOnce({
      id: 'usr_1',
      display_name: 'Maria Silva',
      location: 'Alter do Chão',
      status: 'active',
    });

    let editTree: renderer.ReactTestRenderer;
    await act(async () => {
      editTree = renderWithProviders(
        <EditProfileModal
          visible={true}
          onClose={jest.fn()}
          currentProfile={{ id: 'usr_1', name: 'Maria Antiga', location: 'Santarém', status: 'active' }}
        />
      );
    });
    const editJson = JSON.stringify(editTree!.toJSON());
    expect(editJson).toContain('Editar Perfil');

    // 3. Renderiza modal de exclusão LGPD
    let deleteTree: renderer.ReactTestRenderer;
    await act(async () => {
      deleteTree = renderWithProviders(
        <AccountDeletionModal
          visible={true}
          onClose={jest.fn()}
        />
      );
    });
    const deleteJson = JSON.stringify(deleteTree!.toJSON());
    expect(deleteJson).toContain('Excluir Conta');
    expect(deleteJson).toContain('LGPD');
  });

  test('Jornada 2: Painel Administrativo, Edição Territorial e Atores', async () => {
    (apiClient.getAdminRegions as jest.Mock).mockResolvedValue({
      data: [{ id: 'reg_1', name: 'Região Tapajós', status: 'published' }],
    });

    (apiClient.getAdminRoutes as jest.Mock).mockResolvedValue({
      data: [{ id: 'rot_1', name: 'Rota das Praias', status: 'published' }],
    });

    (apiClient.getAdminActors as jest.Mock).mockResolvedValue({
      data: [{ id: 'act_1', name: 'Pousada Encanto', status: 'published' }],
    });

    // 1. Renderiza Shell com abas operacionais
    let shellTree: renderer.ReactTestRenderer;
    await act(async () => {
      shellTree = renderWithProviders(<AdminShell />);
    });
    const shellJson = JSON.stringify(shellTree!.toJSON());
    expect(shellJson).toContain('ECOconexão Editorial');
    expect(shellJson).toContain('Território & Rotas');

    // 2. Renderiza Editor de Território
    let territoryTree: renderer.ReactTestRenderer;
    await act(async () => {
      territoryTree = renderWithProviders(<TerritoryEditor />);
    });
    const territoryJson = JSON.stringify(territoryTree!.toJSON());
    expect(territoryJson).toContain('Editor Territorial & Rotas Comunitárias');

    // 3. Renderiza Editor de Atores
    let actorTree: renderer.ReactTestRenderer;
    await act(async () => {
      actorTree = renderWithProviders(<ActorEditor />);
    });
    const actorJson = JSON.stringify(actorTree!.toJSON());
    expect(actorJson).toContain('Gestão de Atores');
  });

  test('Jornada 3: Fila de Revisão Editorial (Publish Guard, Reconciliação e Auditoria)', async () => {
    // 1. Renderiza Fila de Revisão
    let reviewTree: renderer.ReactTestRenderer;
    await act(async () => {
      reviewTree = renderWithProviders(<WorkflowReviewQueue />);
    });
    const reviewJson = JSON.stringify(reviewTree!.toJSON());
    expect(reviewJson).toContain('Publish Guard');

    // 2. Renderiza Trilha de Auditoria
    let auditTree: renderer.ReactTestRenderer;
    await act(async () => {
      auditTree = renderWithProviders(<AuditLogViewer initialLogs={[]} />);
    });
    const auditJson = JSON.stringify(auditTree!.toJSON());
    expect(auditJson).toContain('Trilha de Auditoria Imutável (ADR 0006)');
  });
});
