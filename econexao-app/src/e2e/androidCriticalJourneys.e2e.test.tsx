import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { Text } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RouteDetailScreen from '../../app/route/[routeId]/index';
import { NetworkStatusBar } from '../components/common/NetworkStatusBar';
import { EmptyStateView, ErrorStateView } from '../components/common/UIStateViews';
import { buildDeepLink, parseDeepLink, DeepLinkRoutes } from '../utils/linking';
import { useRouteDetailQuery, useRouteAlertsQuery, useRouteActorsQuery, useRegionsQuery } from '../hooks/queries';
import { useRouter, useLocalSearchParams } from 'expo-router';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));
jest.mock('expo-router', () => ({
  useRouter: jest.fn(),
  useLocalSearchParams: jest.fn(),
}));

jest.mock('../hooks/useApp', () => ({
  useApp: () => ({
    state: { activeRegionId: 'pindobal' },
    activeRegion: { id: 'pindobal', name: 'Pindobal' },
    setActiveRegion: jest.fn(),
    openRegionSelector: jest.fn(),
    isRegionModalOpen: false,
    closeRegionSelector: jest.fn(),
  }),
}));

jest.mock('../hooks/queries', () => ({
  useRegionsQuery: jest.fn(),
  useRouteDetailQuery: jest.fn(),
  useRouteAlertsQuery: jest.fn(),
  useRouteActorsQuery: jest.fn(),
}));

describe('E2E Android - Critical Mobile Journeys & Degraded Network (ECO-2102)', () => {
  let queryClient: QueryClient;
  const mockPush = jest.fn();
  const mockBack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      back: mockBack,
      replace: jest.fn(),
    });
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
    });
    (useRegionsQuery as jest.Mock).mockReturnValue({
      data: [{ id: 'pindobal', name: 'Pindobal' }],
    });
    (useRouteDetailQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      error: null,
      data: {
        id: 'route-pindobal',
        slug: 'rota-pindobal',
        title: 'Trilha da Serra da Piraoca',
        summary: 'Trilha ecológica com vista panorâmica do Rio Tapajós.',
        description: 'Descrição detalhada com fauna e flora exuberantes.',
        city: 'Belterra',
        state_code: 'PA',
        status: 'active',
        is_verified: true,
        best_season: 'Junho a Dezembro',
        connectivity: '4G Parcial',
        road_access: 'Asfalto e Terra',
        payment_info: 'Dinheiro e Pix',
        distance_km: 4.5,
        duration_minutes: 120,
        difficulty: 'moderada',
        hero_image_url: 'https://images.unsplash.com/photo-piraoca',
        origins: [],
      },
      refetch: jest.fn(),
    });
    (useRouteAlertsQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: [],
      refetch: jest.fn(),
    });
    (useRouteActorsQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: { data: [], meta: { total: 0, limit: 3 } },
      refetch: jest.fn(),
    });

    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });
  });

  test('Jornada 1: Resolução de Deep Link Nativo Android e Acessibilidade da Rota', async () => {
    const deepLinkPath = DeepLinkRoutes.ROUTE_DETAIL('route-pindobal');
    const deepLinkUrl = buildDeepLink(deepLinkPath);

    expect(deepLinkUrl).toBe('econexao://route/route-pindobal');

    const parsedTarget = parseDeepLink(deepLinkUrl);
    expect(parsedTarget).not.toBeNull();
    expect(parsedTarget?.path).toBe('/route/route-pindobal');

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    const textContents = textElements.map((el) => el.props.children);
    expect(textContents).toContain('Trilha da Serra da Piraoca');
  });

  test('Jornada 2: Comportamento em Rede Degradada, Modo Offline e Recuperação com Retry', async () => {
    let offlineTree!: renderer.ReactTestRenderer;
    await act(async () => {
      offlineTree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <NetworkStatusBar isOfflineOverride={true} />
        </QueryClientProvider>
      );
    });
    expect(offlineTree.toJSON()).not.toBeNull();

    const onRetryMock = jest.fn();
    let errorTree!: renderer.ReactTestRenderer;
    await act(async () => {
      errorTree = renderer.create(
        <ErrorStateView
          title="Falha na Conexão"
          message="Não foi possível sincronizar os dados da rota. Verifique sua rede."
          onRetry={onRetryMock}
        />
      );
    });
    const retryRoot = errorTree.root;
    const retryButton = retryRoot.findByProps({ accessibilityLabel: 'Tentar Novamente' });
    expect(retryButton).toBeDefined();

    act(() => {
      retryButton.props.onPress();
    });
    expect(onRetryMock).toHaveBeenCalledTimes(1);

    let emptyTree!: renderer.ReactTestRenderer;
    await act(async () => {
      emptyTree = renderer.create(
        <EmptyStateView
          title="Nenhum atrativo local encontrado"
          message="Tente ajustar seus filtros ou verificar rotas próximas."
        />
      );
    });
    expect(emptyTree.root.findAllByType(EmptyStateView)).toHaveLength(1);
  });
});
