import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { Image, Text, TouchableOpacity } from 'react-native';

import RouteDetailScreen from '../../../app/route/[routeId]/index';
import {
  useActorCategoriesQuery,
  useRouteAlertsQuery,
  useRouteActorsQuery,
  useRouteDetailQuery,
  useRouteMapQuery,
} from '../../hooks/queries';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { ApiClientError } from '../../api/client';

const textValue = (value: unknown): string => {
  if (typeof value === 'string' || typeof value === 'number') return String(value);
  if (Array.isArray(value)) return value.map(textValue).join('');
  return '';
};

jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

jest.mock('../map/MapAdapter', () => {
  const { TouchableOpacity: MockTouchableOpacity } = require('react-native');
  return {
    MapAdapter: ({ onSelectActor }: { onSelectActor: (actorId: string) => void }) => (
      <MockTouchableOpacity
        accessibilityLabel="Selecionar Pousada no mini mapa"
        onPress={() => onSelectActor('actor-1')}
      />
    ),
  };
});

jest.mock('expo-router', () => ({
  useRouter: jest.fn(),
  useLocalSearchParams: jest.fn(),
}));

jest.mock('@tanstack/react-query', () => {
  const actual = jest.requireActual('@tanstack/react-query');
  return {
    ...actual,
    useQueryClient: jest.fn(),
  };
});

jest.mock('../../hooks/useApp', () => ({
  useApp: () => ({
    state: { activeRegionId: 'pindobal' },
    activeRegion: { id: 'pindobal', name: 'Pindobal' },
    setActiveRegion: jest.fn(),
    openRegionSelector: jest.fn(),
    isRegionModalOpen: false,
    closeRegionSelector: jest.fn(),
  }),
}));

jest.mock('../../hooks/queries', () => ({
  useRegionsQuery: jest.fn().mockReturnValue({ data: [{ id: 'pindobal', name: 'Pindobal' }] }),
  useRouteDetailQuery: jest.fn(),
  useRouteAlertsQuery: jest.fn(),
  useRouteActorsQuery: jest.fn(),
  useRouteMapQuery: jest.fn(),
  useActorCategoriesQuery: jest.fn(),
}));

jest.mock('../../state/useAppContext', () => {
  const { initialAppState } = require('../../state/appReducer');
  return {
    useAppContext: jest.fn().mockReturnValue({
      state: initialAppState,
      dispatch: jest.fn(),
    }),
  };
});

describe('RouteDetailScreen Integration (ECO-0901..0907)', () => {
  const mockPush = jest.fn();
  const mockBack = jest.fn();

  const mockRouteDetailData = {
    id: 'route-pindobal',
    slug: 'rota-pindobal',
    title: 'Rota Pindobal',
    summary: 'Uma linda rota ecológica em Belterra.',
    description: 'Descrição detalhada da Rota Pindobal.',
    city: 'Belterra',
    state_code: 'PA',
    status: 'active',
    is_verified: true,
    best_season: 'Junho a Dezembro',
    connectivity: '4G Parcial',
    road_access: 'Asfalto e Terra',
    payment_info: 'Dinheiro e Pix',
    origins: [
      {
        id: 'origin-porto',
        route_id: 'route-pindobal',
        code: 'porto',
        name: 'Porto de Santarém',
        description: 'Saída hidroviária principal',
        distance_m: 45229,
        duration_s: 3600,
        sort_order: 1,
      },
      {
        id: 'origin-aeroporto',
        route_id: 'route-pindobal',
        code: 'aeroporto',
        name: 'Aeroporto Maestro Wilson Fonseca',
        description: 'Saída aérea principal',
        distance_m: 41452,
        duration_s: 3200,
        sort_order: 2,
      },
      {
        id: 'origin-rodoviaria',
        route_id: 'route-pindobal',
        code: 'rodoviaria',
        name: 'Terminal Rodoviário de Santarém',
        description: 'Saída rodoviária principal',
        distance_m: 42319,
        duration_s: 3400,
        sort_order: 3,
      },
    ],
  };

  const mockAlertsData = [
    {
      id: 'alert-1',
      route_id: 'route-pindobal',
      title: 'Trecho em Obras',
      message: 'Atenção no km 12 devido a manutenção.',
      severity: 'warning' as const,
      published_at: '2026-08-01T10:00:00Z',
      is_active: true,
    },
  ];

  const mockActorsData = {
    data: [
      {
        id: 'actor-1',
        slug: 'pousada-floresta',
        name: 'Pousada Canto da Floresta',
        category_slug: 'hospedagem',
        category_label: 'Hospedagem',
        address: 'Praia de Pindobal, s/n',
        green_badge_status: 'verified' as const,
        verification_status: 'verified' as const,
        google_rating: 4.8,
        cover_media: {
          id: 'media-1',
          owner_type: 'actor',
          owner_id: 'actor-1',
          url: 'https://cdn.example.com/pousada.webp',
          derivatives: { card: 'https://cdn.example.com/pousada-card.webp' },
          alt_text: 'Fachada da Pousada Canto da Floresta',
          sort_order: 0,
        },
      },
      {
        id: 'actor-2',
        slug: 'restaurante-moqueca',
        name: 'Restaurante Moqueca do Tapajós',
        category_slug: 'alimentacao',
        category_label: 'Alimentação',
        address: 'Orla de Pindobal',
        green_badge_status: 'none' as const,
        verification_status: 'verified' as const,
        google_rating: 4.6,
      },
    ],
    meta: { total: 2, limit: 3 },
  };

  beforeEach(() => {
    jest.clearAllMocks();

    const { useQueryClient } = require('@tanstack/react-query');
    (useQueryClient as jest.Mock).mockReturnValue({
      getQueryData: jest.fn().mockReturnValue(undefined),
      setQueryData: jest.fn(),
      removeQueries: jest.fn(),
      invalidateQueries: jest.fn(),
    });

    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: false },
      },
      dispatch: jest.fn(),
    });

    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      back: mockBack,
    });

    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
    });

    (useRouteDetailQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      error: null,
      data: mockRouteDetailData,
      refetch: jest.fn(),
    });

    (useRouteAlertsQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: mockAlertsData,
      refetch: jest.fn(),
    });

    (useRouteActorsQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: mockActorsData,
      refetch: jest.fn(),
    });

    (useRouteMapQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: {
        route_id: 'route-pindobal',
        selected_origin_id: 'origin-porto',
        bounds: null,
        geometry: null,
        pins: [{ id: 'pin-1', actor_id: 'actor-1', name: 'Pousada', category_slug: 'hospedagem', latitude: -2.6, longitude: -54.9 }],
      },
      refetch: jest.fn(),
    });

    (useActorCategoriesQuery as jest.Mock).mockReturnValue({
      data: [
        { id: 'category-1', slug: 'hospedagem', label: 'Hospedagem', sort_order: 1 },
        { id: 'category-2', slug: 'alimentacao', label: 'Alimentação', sort_order: 2 },
      ],
    });
  });

  it('renders route details, origin simulator, alerts, and preview actors', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    const textContents = textElements.map((el) => el.props.children);

    expect(textContents).toContain('Rota Pindobal');
    expect(textContents).toContain('Descrição detalhada da Rota Pindobal.');
    expect(textContents).toContain('Porto de Santarém');
    expect(textElements.map((node) => textValue(node.props.children)).join(' ')).toContain('45.2 km');
    expect(textContents).toContain('Trecho em Obras');
    expect(textContents).toContain('Pousada Canto da Floresta');
    expect(textContents).toContain('Restaurante Moqueca do Tapajós');
  });

  it('allows origin selection and queries actors with effective originId', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;

    // Verify initial actors query call with default origin ('origin-porto')
    expect(useRouteActorsQuery).toHaveBeenCalledWith('route-pindobal', {
      origin_id: 'origin-porto',
      category: undefined,
      limit: 3,
    });

    // Find all three contractual origins and select Rodoviária.
    const originButtons = root.findAll((node) => node.type === TouchableOpacity && node.props.accessibilityLabel?.includes('Selecionar origem'));
    expect(originButtons.length).toBe(3);
    expect(originButtons[0].props.accessibilityState).toEqual({ selected: true });

    await act(async () => {
      originButtons[2].props.onPress();
    });

    // Verify updated actors query call and selected-state semantics.
    expect(useRouteActorsQuery).toHaveBeenLastCalledWith('route-pindobal', {
      origin_id: 'origin-rodoviaria',
      category: undefined,
      limit: 3,
    });
    expect(originButtons[2].props.accessibilityState).toEqual({ selected: true });
    expect(
      root.findAllByType(Text).map((node) => textValue(node.props.children)).join(' ')
    ).toContain('42.3 km');
  });

  it('navigates to map and catalog preserving originId in URL query params', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;

    const mapBtn = root.find((node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Expandir mapa da rota');
    const catalogBtn = root.find((node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Ver catálogo completo');

    await act(async () => {
      mapBtn.props.onPress();
    });
    expect(mockPush).toHaveBeenCalledWith('/route/route-pindobal/map?originId=origin-porto');

    await act(async () => {
      catalogBtn.props.onPress();
    });
    expect(mockPush).toHaveBeenCalledWith('/route/route-pindobal/catalog?originId=origin-porto');
  });

  it('honors a deep-linked origin and actor in map and catalog navigation', async () => {
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
      originId: 'origin-aeroporto',
      actorId: 'actor-2',
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    expect(useRouteActorsQuery).toHaveBeenCalledWith('route-pindobal', {
      origin_id: 'origin-aeroporto',
      category: undefined,
      limit: 3,
    });

    const buttons = tree.root.findAllByType(TouchableOpacity);
    await act(async () => {
      buttons.find((node) => node.props.accessibilityLabel === 'Expandir mapa da rota')!
        .props.onPress();
      buttons.find((node) => node.props.accessibilityLabel === 'Ver catálogo completo')!
        .props.onPress();
    });

    expect(mockPush).toHaveBeenCalledWith(
      '/route/route-pindobal/map?originId=origin-aeroporto&actorId=actor-2'
    );
    expect(mockPush).toHaveBeenCalledWith(
      '/route/route-pindobal/catalog?originId=origin-aeroporto&actorId=actor-2'
    );
  });

  it('opens an actor preview on the map preserving the selected origin', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const actorPreview = tree.root.find(
      (node) =>
        node.type === TouchableOpacity &&
        node.props.accessibilityLabel === 'Selecionar Pousada no mini mapa'
    );
    await act(async () => actorPreview.props.onPress());

    expect(mockPush).toHaveBeenCalledWith(
      '/route/route-pindobal/map?originId=origin-porto&actorId=actor-1'
    );
  });

  it('recolhe o mapa, preserva semântica expanded e permite mostrar novamente', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    let toggle = tree.root.find(
      (node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Ocultar mapa da rota'
    );
    expect(toggle.props.accessibilityState).toEqual({ expanded: true });

    await act(async () => toggle.props.onPress());
    toggle = tree.root.find(
      (node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Mostrar mapa da rota'
    );
    expect(toggle.props.accessibilityState).toEqual({ expanded: false });

    await act(async () => toggle.props.onPress());
    expect(
      tree.root.find(
        (node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Expandir mapa da rota'
      )
    ).toBeTruthy();
  });

  it('exibe foto acessível e filtra o catálogo local sem fabricar contagens', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const image = tree.root.findAllByType(Image).find(
      (node) => node.props.accessibilityLabel === 'Fachada da Pousada Canto da Floresta'
    );
    expect(image).toBeDefined();
    expect(image!.props.source).toEqual({ uri: 'https://cdn.example.com/pousada-card.webp' });
    expect(image!.props.accessibilityLabel).toBe('Fachada da Pousada Canto da Floresta');

    const lodgingFilter = tree.root.find(
      (node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Filtro Hospedagem'
    );
    await act(async () => lodgingFilter.props.onPress());

    expect(useRouteActorsQuery).toHaveBeenLastCalledWith('route-pindobal', {
      origin_id: 'origin-porto',
      category: 'hospedagem',
      limit: 3,
    });
  });

  it('renders loading state when route detail is pending', async () => {
    (useRouteDetailQuery as jest.Mock).mockReturnValue({
      isPending: true,
      isError: false,
      error: null,
      data: undefined,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    const textContents = textElements.map((el) => el.props.children);

    expect(textContents).toContain('Carregando detalhes da rota...');
  });

  it('renders ErrorStateView with retry button when route query fails (ECO-0907)', async () => {
    const mockRefetch = jest.fn();
    (useRouteDetailQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: true,
      error: new ApiClientError('Falha temporária', 503, 'SERVICE_UNAVAILABLE'),
      data: undefined,
      refetch: mockRefetch,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    const textContents = textElements.map((el) => el.props.children);

    expect(textContents).toContain('Erro ao carregar rota');

    const retryButton = root.find((node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Tentar Novamente');
    expect(retryButton).toBeTruthy();

    await act(async () => {
      retryButton.props.onPress();
    });

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('distinguishes a real HTTP 404 and keeps retry and back independent', async () => {
    const mockRefetch = jest.fn();
    (useRouteDetailQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: true,
      error: new ApiClientError('Rota não encontrada', 404, 'NOT_FOUND'),
      data: undefined,
      refetch: mockRefetch,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    const textContents = textElements.map((el) => el.props.children);

    expect(textContents).toContain('Rota não encontrada');

    const retryButton = root.find(
      (node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Tentar novamente'
    );
    const backButton = root.find(
      (node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Voltar para a lista'
    );
    expect(retryButton).toBeTruthy();
    expect(backButton).toBeTruthy();

    await act(async () => {
      retryButton.props.onPress();
      backButton.props.onPress();
    });

    expect(mockRefetch).toHaveBeenCalledTimes(1);
    expect(mockBack).toHaveBeenCalledTimes(1);
  });

  it('keeps practical route fields out of the current detail presentation', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const contents = tree.root
      .findAllByType(Text)
      .map((node) => textValue(node.props.children));
    expect(contents).not.toContain('Informações Práticas');
    expect(contents).not.toContain('Junho a Dezembro');
    expect(contents).not.toContain('4G Parcial');
    expect(contents).not.toContain('Asfalto e Terra');
    expect(contents).not.toContain('Dinheiro e Pix');
  });

  it('hides "Escolher no mapa" and ignores ephemeral cache when dynamicRouting is false (fail-closed remediation ECO-2311)', async () => {
    const { useQueryClient } = require('@tanstack/react-query');
    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: false },
      },
      dispatch: jest.fn(),
    });

    const getQueryDataMock = jest.fn().mockReturnValue({
      originType: 'map-selection-preview',
      previewData: {
        distance_m: 15400,
        duration_s: 1200,
        provider: 'dynamic_preview',
        geojson: { type: 'LineString', coordinates: [[-54.7083, -2.4431], [-54.9, -2.5]] },
        bounds: { min_lat: -2.5, max_lat: -2.4, min_lng: -54.9, max_lng: -54.7 },
      },
    });
    const removeQueriesMock = jest.fn();
    (useQueryClient as jest.Mock).mockReturnValue({
      getQueryData: getQueryDataMock,
      removeQueries: removeQueriesMock,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const buttons = root.findAllByType(TouchableOpacity);

    // "Escolher no mapa" must NOT be rendered when dynamic routing is false
    const mapButton = buttons.find(
      (b) => b.props.accessibilityLabel === 'Escolher ponto de partida no mapa'
    );
    expect(mapButton).toBeUndefined();

    // Notice banner must NOT be visible
    const textContents = root.findAllByType(Text).map((node) => textValue(node.props.children));
    expect(textContents).not.toContain('Trajeto sugerido a partir do seu ponto de partida');

    // Ephemeral cache was not consumed
    expect(removeQueriesMock).not.toHaveBeenCalled();
  });

  it('consumes ephemeral preview from queryClient cache, renders notice banner and geometry, and clears cache on fixed origin selection (ECO-2311)', async () => {
    const { useQueryClient } = require('@tanstack/react-query');
    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: true },
      },
      dispatch: jest.fn(),
    });

    const getQueryDataMock = jest.fn().mockReturnValue({
      originType: 'map-selection-preview',
      previewData: {
        distance_m: 15400,
        duration_s: 1200,
        provider: 'dynamic_preview',
        geojson: { type: 'LineString', coordinates: [[-54.7083, -2.4431], [-54.9, -2.5]] },
        bounds: { min_lat: -2.5, max_lat: -2.4, min_lng: -54.9, max_lng: -54.7 },
      },
    });
    const removeQueriesMock = jest.fn();
    (useQueryClient as jest.Mock).mockReturnValue({
      getQueryData: getQueryDataMock,
      removeQueries: removeQueriesMock,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const textContents = root.findAllByType(Text).map((node) => textValue(node.props.children));

    // Notice banner should be visible
    expect(textContents).toContain('Trajeto sugerido a partir do seu ponto de partida');
    expect(textContents.join(' ')).toContain('15.4 km');
    expect(textContents.join(' ')).toContain('20 min');

    // QueryClient ephemeral preview key should have been consumed
    expect(removeQueriesMock).toHaveBeenCalledWith({
      queryKey: ['routes', 'ephemeral-preview', 'route-pindobal'],
    });

    // Selecting a fixed origin restores official origin and clears ephemeral preview
    const originButtons = root.findAll((node) => node.type === TouchableOpacity && node.props.accessibilityLabel?.includes('Selecionar origem'));
    await act(async () => {
      originButtons[0].props.onPress();
    });

    expect(removeQueriesMock).toHaveBeenCalledTimes(2);
  });

  it('clicking "Escolher no mapa" opens map screen with mode=select-origin and without coordinates in URL (ECO-2311)', async () => {
    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: true },
      },
      dispatch: jest.fn(),
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;
    const mapButton = root.find(
      (b) => b.type === TouchableOpacity && b.props.accessibilityLabel === 'Escolher ponto de partida no mapa'
    );
    expect(mapButton).toBeDefined();

    await act(async () => {
      mapButton.props.onPress();
    });

    expect(mockPush).toHaveBeenCalledWith(
      '/route/route-pindobal/map?originId=origin-porto&mode=select-origin'
    );
  });

  it('provides and consumes dynamic pins, legend and city_bounds on RouteMapPreview and transfers state on expand (ECO-2312)', async () => {
    const { useQueryClient } = require('@tanstack/react-query');
    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: true },
      },
      dispatch: jest.fn(),
    });

    const setQueryDataMock = jest.fn();
    const dynamicPreviewData = {
      distance_m: 15400,
      duration_s: 1200,
      provider: 'dynamic_preview',
      geojson: { type: 'LineString', coordinates: [[-54.7083, -2.4431], [-54.9, -2.5]] },
      bounds: { min_lat: -2.5, max_lat: -2.4, min_lng: -54.9, max_lng: -54.7 },
      city_bounds: { min_lat: -2.8, max_lat: -2.3, min_lng: -55.1, max_lng: -54.5 },
      pins: [
        {
          id: 'pin-dynamic-1',
          actor_id: 'actor-dynamic-1',
          name: 'Restaurante Corredor Dinâmico',
          category_slug: 'alimentacao',
          category_label: 'Alimentação',
          color: '#D97706',
          icon: 'utensils',
          latitude: -2.46,
          longitude: -54.75,
          layer: 'route_corridor',
        },
      ],
      legend: [
        {
          category_slug: 'alimentacao',
          label: 'Alimentação',
          color: '#D97706',
          icon: 'utensils',
          count: 1,
          sort_order: 1,
        },
      ],
    };

    (useQueryClient as jest.Mock).mockReturnValue({
      getQueryData: jest.fn().mockReturnValue({
        originType: 'my-location-preview',
        previewData: dynamicPreviewData,
      }),
      setQueryData: setQueryDataMock,
      removeQueries: jest.fn(),
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;

    // Expand map button should transfer previewData to memory cache
    const expandButton = root.find(
      (node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Expandir mapa da rota'
    );
    expect(expandButton).toBeTruthy();

    await act(async () => {
      expandButton.props.onPress();
    });

    expect(setQueryDataMock).toHaveBeenCalledWith(
      ['routes', 'ephemeral-preview', 'route-pindobal'],
      {
        previewData: dynamicPreviewData,
        originType: 'my-location-preview',
      }
    );
    expect(mockPush).toHaveBeenCalledWith('/route/route-pindobal/map');
  });

  it('falls back to previous valid official route and alerts user when dynamic routing preview request fails (ECO-2311)', async () => {
    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: true },
      },
      dispatch: jest.fn(),
    });

    const { apiClient } = require('../../api/client');
    const previewSpy = jest.spyOn(apiClient, 'previewRoute').mockRejectedValueOnce(new Error('Provider timeout'));
    const alertSpy = jest.spyOn(require('react-native').Alert, 'alert');

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const root = tree.root;

    // Select Aeroporto first as previous valid origin
    const originButtons = root.findAll((node) => node.type === TouchableOpacity && node.props.accessibilityLabel?.includes('Selecionar origem'));
    await act(async () => {
      originButtons[1].props.onPress();
    });

    // Simulate calling handleSelectCurrentLocation / coordinate selection failure
    const selector = root.findByType(require('../../../src/components/routes/OriginSelector').OriginSelector);
    await act(async () => {
      await selector.props.onSelectCurrentLocation({ latitude: -2.44, longitude: -54.70, accuracy: 10 });
    });

    expect(previewSpy).toHaveBeenCalledWith('route-pindobal', {
      latitude: -2.44,
      longitude: -54.70,
      travel_mode: 'DRIVE',
    });

    // Alert shown to user
    expect(alertSpy).toHaveBeenCalledWith(
      'Trajeto Sugerido Indisponível',
      expect.stringContaining('Não conseguimos calcular o trajeto sugerido')
    );

    // Selector preserves the last valid origin (Aeroporto)
    const updatedButtons = root.findAll((node) => node.type === TouchableOpacity && node.props.accessibilityLabel?.includes('Selecionar origem'));
    expect(updatedButtons[1].props.accessibilityState).toEqual({ selected: true });
  });
});
