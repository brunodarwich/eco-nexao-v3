import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { Text, TouchableOpacity } from 'react-native';

import RouteDetailScreen from '../../../app/route/[routeId]/index';
import { useRouteDetailQuery, useRouteAlertsQuery, useRouteActorsQuery } from '../../hooks/queries';
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

jest.mock('expo-router', () => ({
  useRouter: jest.fn(),
  useLocalSearchParams: jest.fn(),
}));

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
}));

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
  });

  it('renders route details, origin simulator, stats, alerts, and preview actors', async () => {
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

    // Find action buttons: "Abrir mapa" and "Ver catálogo"
    const mapBtn = root.find((node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Abrir mapa interativo da rota');
    const catalogBtn = root.find((node) => node.type === TouchableOpacity && node.props.accessibilityLabel === 'Ver catálogo completo de atores');

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
      limit: 3,
    });

    const buttons = tree.root.findAllByType(TouchableOpacity);
    await act(async () => {
      buttons.find((node) => node.props.accessibilityLabel === 'Abrir mapa interativo da rota')!
        .props.onPress();
      buttons.find((node) => node.props.accessibilityLabel === 'Ver catálogo completo de atores')!
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
        node.props.accessibilityLabel === 'Abrir Pousada Canto da Floresta no mapa'
    );
    await act(async () => actorPreview.props.onPress());

    expect(mockPush).toHaveBeenCalledWith(
      '/route/route-pindobal/map?originId=origin-porto&actorId=actor-1'
    );
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

  it('does not invent practical route data when the API omits it', async () => {
    (useRouteDetailQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      error: null,
      data: {
        ...mockRouteDetailData,
        best_season: null,
        connectivity: null,
        road_access: null,
        payment_info: null,
      },
      refetch: jest.fn(),
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<RouteDetailScreen />);
    });

    const contents = tree.root.findAllByType(Text).map((node) => node.props.children);
    expect(contents.filter((value) => value === 'Não informado')).toHaveLength(4);
    expect(contents).not.toContain('Ano todo');
    expect(contents).not.toContain('3G/4G parcial');
  });
});
