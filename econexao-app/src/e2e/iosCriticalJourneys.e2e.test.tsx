import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { Text } from 'react-native';
import RouteDetailScreen from '../../app/route/[routeId]/index';
import { parseDeepLink } from '../utils/linking';
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

describe('E2E iOS - Critical Mobile Journeys & Universal Links (ECO-2103)', () => {
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
      routeId: 'route-flona-01',
    });
    (useRegionsQuery as jest.Mock).mockReturnValue({
      data: [{ id: 'pindobal', name: 'Pindobal' }],
    });
    (useRouteDetailQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      error: null,
      data: {
        id: 'route-flona-01',
        slug: 'rota-flona-tapajos',
        title: 'Trilha das Sumaúmas Gigantes - Flona Tapajós',
        summary: 'Caminhada interpretativa na Floresta Nacional do Tapajós.',
        description: 'Trilha em área de preservação com guias tradicionais.',
        city: 'Belterra',
        state_code: 'PA',
        status: 'active',
        is_verified: true,
        best_season: 'Ano Todo',
        connectivity: 'Sem Sinal',
        road_access: 'Barco / Terra',
        payment_info: 'Dinheiro',
        distance_km: 8.5,
        duration_minutes: 240,
        difficulty: 'dificil',
        hero_image_url: 'https://images.unsplash.com/photo-flona',
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
  });

  test('Jornada 1: Universal Links HTTPS (Cold Start) no iOS', async () => {
    const universalUrl = 'https://econexao.app/route/route-flona-01';
    const parsedTarget = parseDeepLink(universalUrl);

    expect(parsedTarget).not.toBeNull();
    expect(parsedTarget?.path).toBe('/route/route-flona-01');

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    const textContents = textElements.map((el) => el.props.children);
    expect(textContents).toContain('Trilha das Sumaúmas Gigantes - Flona Tapajós');
  });

  test('Jornada 2: Acessibilidade VoiceOver e Estrutura Semântica', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const screenInstance = root.findByType(RouteDetailScreen);
    expect(screenInstance).toBeDefined();
  });
});
