import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AccessibilityInfo, TextInput, TouchableOpacity } from 'react-native';

import { AppContextProvider } from '../../state/AppContext';
import { EditProfileModal } from './EditProfileModal';
import { AccountDeletionModal } from './AccountDeletionModal';
import LegalAndPrivacyScreen from '../../../app/profile/legal';
import RouteDetailScreen from '../../../app/route/[routeId]/index';
import { apiClient } from '../../api/client';
import { useAuth } from '../../hooks/useAuth';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));

jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useLocalSearchParams: () => ({
    routeId: 'route-test-1',
  }),
}));

jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

jest.mock('../../hooks/useApp', () => ({
  useApp: () => ({
    state: { activeRegionId: 'pindobal' },
    activeRegion: { id: 'pindobal', name: 'Pindobal' },
    openRegionSelector: jest.fn(),
  }),
}));

jest.mock('../../hooks/queries', () => ({
  useRegionsQuery: jest.fn().mockReturnValue({
    data: [{ id: 'pindobal', name: 'Pindobal' }],
    isPending: false,
    isError: false,
  }),
  useRouteDetailQuery: jest.fn().mockReturnValue({
    data: {
      id: 'route-test-1',
      title: 'Trilha do Jamaraquá',
      city: 'Belterra',
      state_code: 'PA',
      is_verified: true,
      description: 'Trilha em floresta primária com árvores centenárias.',
      origins: [{ id: 'orig-1', name: 'Comunidade Jamaraquá' }],
    },
    isPending: false,
    isError: false,
  }),
  useRouteAlertsQuery: jest.fn().mockReturnValue({
    data: [],
    isPending: false,
    isError: false,
  }),
  useRouteActorsQuery: jest.fn().mockReturnValue({
    data: { data: [] },
    isPending: false,
    isError: false,
  }),
  useBootstrapQuery: jest.fn().mockReturnValue({ data: null }),
  useMyPreferencesQuery: jest.fn().mockReturnValue({ data: null }),
}));


describe('ECO-1904: Perfil, Trips, Termos Legais e LGPD', () => {
  let queryClient: QueryClient;
  let announceSpy: jest.SpyInstance;
  const mockSignOut = jest.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    announceSpy = jest.spyOn(AccessibilityInfo, 'announceForAccessibility').mockImplementation(() => {});
    (useAuth as jest.Mock).mockReturnValue({
      user: { id: 'test-user-uuid', email: 'turista@econexao.org', is_anonymous: false },
      isAuthenticated: true,
      signOut: mockSignOut,
    });
    jest.clearAllMocks();
  });

  afterEach(() => {
    announceSpy.mockRestore();
  });

  test('EditProfileModal renderiza dados atuais e atualiza perfil via API', async () => {
    const updateSpy = jest.spyOn(apiClient, 'updateMyProfile').mockResolvedValueOnce({
      data: {
        id: 'prof-1',
        name: 'Maria Floresta',
        location: 'Belterra, PA',
        status: 'active',
      },
    });

    const mockClose = jest.fn();
    let tree!: renderer.ReactTestRenderer;

    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <EditProfileModal
              visible={true}
              onClose={mockClose}
              currentProfile={{
                id: 'prof-1',
                name: 'Maria Antiga',
                location: 'Santarém, PA',
                status: 'active',
              }}
              userId="test-user-uuid"
            />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    const inputs = tree.root.findAllByType(TextInput);
    expect(inputs.length).toBe(2);

    // Alterar nome
    await act(async () => {
      inputs[0].props.onChangeText('Maria Floresta');
    });

    const touchables = tree.root.findAllByType(TouchableOpacity);
    const saveBtn = touchables.find(
      (t) => t.props.accessibilityLabel && t.props.accessibilityLabel.includes('Salvar perfil')
    );
    expect(saveBtn).toBeTruthy();

    await act(async () => {
      saveBtn!.props.onPress();
    });

    expect(updateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Maria Floresta' })
    );
    expect(announceSpy).toHaveBeenCalledWith(expect.stringContaining('Perfil atualizado'));
    expect(mockClose).toHaveBeenCalled();
  });

  test('AccountDeletionModal apresenta informações LGPD e encerra a sessão', async () => {
    const mockClose = jest.fn();
    let tree!: renderer.ReactTestRenderer;

    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <AccountDeletionModal visible={true} onClose={mockClose} />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    const touchables = tree.root.findAllByType(TouchableOpacity);
    const confirmBtn = touchables.find(
      (t) => t.props.accessibilityLabel && t.props.accessibilityLabel.includes('Confirmar exclusão')
    );
    expect(confirmBtn).toBeTruthy();

    await act(async () => {
      await confirmBtn!.props.onPress();
    });

    expect(mockSignOut).toHaveBeenCalled();
    expect(announceSpy).toHaveBeenCalled();
    expect(mockClose).toHaveBeenCalled();
  });

  test('LegalAndPrivacyScreen renderiza termos e privacidade sem erros', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <LegalAndPrivacyScreen />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    expect(tree.toJSON()).toBeTruthy();
  });

  test('RouteDetailScreen permite iniciar e registrar uma viagem na rota', async () => {
    const createTripSpy = jest.spyOn(apiClient, 'createTrip').mockResolvedValueOnce({
      data: {
        id: 'trip-new-1',
        user_id: 'test-user-uuid',
        route_id: 'route-test-1',
        status: 'in_progress',
      },
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <RouteDetailScreen />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    const touchables = tree.root.findAllByType(TouchableOpacity);
    const startTripBtn = touchables.find(
      (t) => t.props.accessibilityLabel && t.props.accessibilityLabel.includes('Registrar início de viagem')
    );
    expect(startTripBtn).toBeTruthy();

    await act(async () => {
      await startTripBtn!.props.onPress();
    });

    expect(createTripSpy).toHaveBeenCalledWith('route-test-1');
    expect(announceSpy).toHaveBeenCalledWith(expect.stringContaining('Viagem iniciada com sucesso'));
  });
});

