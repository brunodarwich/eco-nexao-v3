import React from 'react';
import { Modal, TouchableOpacity } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';
import { useLocalSearchParams, useRouter } from 'expo-router';

import MapScreen from '../../../app/route/[routeId]/map';
import {
  useActorCategoriesQuery,
  useRouteActorsQuery,
  useRouteMapQuery,
} from '../../hooks/queries';

jest.mock('@expo/vector-icons', () => ({
  Ionicons: () => null,
}));

jest.mock('expo-router', () => ({
  useLocalSearchParams: jest.fn(),
  useRouter: jest.fn(),
}));

jest.mock('../../hooks/queries', () => ({
  useActorCategoriesQuery: jest.fn(),
  useRouteActorsQuery: jest.fn(),
  useRouteMapQuery: jest.fn(),
}));

jest.mock('@tanstack/react-query', () => {
  const actual = jest.requireActual('@tanstack/react-query');
  return {
    ...actual,
    useQueryClient: jest.fn(),
  };
});

jest.mock('../../state/useAppContext', () => {
  const { initialAppState } = require('../../state/appReducer');
  return {
    useAppContext: jest.fn().mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: true },
      },
      dispatch: jest.fn(),
    }),
  };
});

jest.mock('../common/AppHeader', () => ({
  AppHeader: () => null,
}));

jest.mock('../../api/client', () => ({
  apiClient: {
    configureAuth: jest.fn(),
    previewRoute: jest.fn().mockResolvedValue({
      data: {
        distance_m: 10000,
        duration_s: 600,
        bounds: { min_lat: -2.5, max_lat: -2.4, min_lng: -54.9, max_lng: -54.7 },
        geojson: { type: 'LineString', coordinates: [[-54.7083, -2.4431], [-54.9, -2.5]] },
      },
    }),
  },
}));

jest.mock('./MapAdapter', () => {
  const React = require('react');
  const { TouchableOpacity, Text, View } = require('react-native');

  return {
    MapAdapter: ({
      onSelectActor,
      bounds,
      selectionMode,
      onSelectCoordinate,
      selectedCoordinate,
    }: {
      onSelectActor: (actorId: string) => void;
      bounds?: unknown;
      selectionMode?: boolean;
      onSelectCoordinate?: (coord: any) => void;
      selectedCoordinate?: any;
    }) => (
      <View>
        <Text accessibilityLabel="Bounds ativos do mapa">{JSON.stringify(bounds)}</Text>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Selecionar pin Pousada Pindobal"
          onPress={() => onSelectActor('actor-1')}
        >
          <Text>Pin</Text>
        </TouchableOpacity>
        {selectionMode && onSelectCoordinate && (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Clicar no mapa para selecionar coordenada"
            onPress={() => onSelectCoordinate({ latitude: -2.4431, longitude: -54.7083 })}
          >
            <Text>Map Click Area</Text>
          </TouchableOpacity>
        )}
      </View>
    ),
  };
});

describe('MapScreen actor sheet (ECO-0905)', () => {
  const push = jest.fn();
  let currentRenderer: TestRenderer.ReactTestRenderer | null = null;

  afterEach(async () => {
    if (currentRenderer) {
      await act(async () => {
        try {
          currentRenderer?.unmount();
        } catch {}
      });
      currentRenderer = null;
    }
    jest.clearAllTimers();
  });

  beforeEach(() => {
    jest.clearAllMocks();

    (useRouter as jest.Mock).mockReturnValue({ push, back: jest.fn() });
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
      originId: 'origin-porto',
    });
    (useRouteMapQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: {
        route_id: 'route-pindobal',
        origin_id: 'origin-porto',
        geometry: null,
        bounds: { min_lat: -2.7, max_lat: -2.5, min_lng: -55, max_lng: -54.8 },
        pins: [
          {
            id: 'pin-1',
            actor_id: 'actor-1',
            name: 'Pousada Pindobal',
            category_slug: 'hospedagem',
            category_label: 'Hospedagem',
            color: '#2563EB',
            icon: 'bed',
            latitude: -2.5,
            longitude: -54.9,
            distance_from_origin_m: 1500,
          },
        ],
        legend: [
          {
            category_slug: 'hospedagem',
            label: 'Hospedagem',
            color: '#2563EB',
            icon: 'bed',
            count: 1,
          },
        ],
      },
      refetch: jest.fn(),
    });
    (useActorCategoriesQuery as jest.Mock).mockReturnValue({
      data: [
        {
          id: 'cat-1',
          slug: 'hospedagem',
          label: 'Hospedagem',
          color: '#2563EB',
          icon: 'bed',
          sort_order: 3,
        },
      ],
    });
    (useRouteActorsQuery as jest.Mock).mockReturnValue({
      data: {
        data: [
          {
            id: 'actor-1',
            name: 'Pousada Pindobal',
            category_slug: 'hospedagem',
            category_label: 'Hospedagem',
            address: 'Praia de Pindobal',
          },
        ],
      },
    });
  });

  it('abre como modal acessível e fecha pelo backdrop sem acionar o mapa', async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const root = renderer.root;
    const pin = root.find(
      (node) => node.props.accessibilityLabel === 'Selecionar pin Pousada Pindobal'
    );

    await act(async () => pin.props.onPress());

    const modal = root.findByType(Modal);
    expect(modal.props.visible).toBe(true);
    expect(modal.props.accessibilityViewIsModal).toBe(true);

    const sheetTexts = modal.findAllByType(require('react-native').Text);
    const categoryTag = sheetTexts.find((t) => t.props.children === 'HOSPEDAGEM');
    expect(categoryTag).toBeDefined();

    const backdrop = root.find(
      (node) => node.props.accessibilityLabel === 'Fechar preview do ator pelo fundo'
    );
    await act(async () => backdrop.props.onPress());

    expect(root.findByType(Modal).props.visible).toBe(false);
    expect(push).not.toHaveBeenCalled();
  });

  it('renderiza a legenda contratual com contagem sem consultar categorias globais', async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const labels = renderer.root.findAllByType(require('react-native').Text)
      .map((node) => node.props.children);
    expect(labels).toContain('Hospedagem (1)');
    expect(useActorCategoriesQuery).not.toHaveBeenCalled();
  });

  it('mostra loading, erro com retry e vazio sem pins', async () => {
    (useRouteMapQuery as jest.Mock).mockReturnValueOnce({ isPending: true });
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => { currentRenderer = renderer = TestRenderer.create(<MapScreen />); });
    expect(renderer.root.findAllByType(require('react-native').Text)
      .some((node) => node.props.children === 'Carregando mapa da rota...')).toBe(true);
    await act(async () => { renderer.unmount(); });

    const refetch = jest.fn();
    (useRouteMapQuery as jest.Mock).mockReturnValueOnce({ isPending: false, isError: true, refetch });
    await act(async () => { currentRenderer = renderer = TestRenderer.create(<MapScreen />); });
    const retry = renderer.root.find((node) => node.props.accessibilityLabel === 'Tentar Novamente');
    await act(async () => retry.props.onPress());
    expect(refetch).toHaveBeenCalledTimes(1);
    await act(async () => { renderer.unmount(); });

    (useRouteMapQuery as jest.Mock).mockReturnValueOnce({
      isPending: false,
      isError: false,
      data: { route_id: 'route-pindobal', origin_id: 'origin-porto', geometry: null, bounds: { min_lat: -2.7, max_lat: -2.5, min_lng: -55, max_lng: -54.8 }, pins: [], legend: [] },
      refetch,
    });
    await act(async () => { currentRenderer = renderer = TestRenderer.create(<MapScreen />); });
    expect(renderer.root.findAllByType(require('react-native').Text)
      .some((node) => node.props.children === 'Nenhum ponto nesta rota')).toBe(true);
  });

  it('apresenta estado de carregamento prolongado acessível durante cold start do Render', async () => {
    jest.useFakeTimers();
    let renderer: TestRenderer.ReactTestRenderer | null = null;
    try {
      (useRouteMapQuery as jest.Mock).mockReturnValue({ isPending: true });
      await act(async () => {
        renderer = TestRenderer.create(<MapScreen />);
      });

      expect(renderer!.root.findAllByType(require('react-native').Text)
        .some((node) => node.props.children === 'Carregando mapa da rota...')).toBe(true);

      await act(async () => {
        jest.advanceTimersByTime(4500);
      });

      expect(renderer!.root.findAllByType(require('react-native').Text)
        .some((node) => node.props.children === 'Servidor de staging iniciando; isso pode levar alguns segundos.')).toBe(true);
    } finally {
      if (renderer) {
        await act(async () => {
          (renderer as TestRenderer.ReactTestRenderer).unmount();
        });
      }
      jest.clearAllTimers();
      jest.useRealTimers();
    }
  });

  it('suporta 175 pins preservando limite de 200, legenda e contagens consistentes', async () => {
    const pins175 = Array.from({ length: 175 }, (_, i) => ({
      id: `pin-${i + 1}`,
      actor_id: `actor-${i + 1}`,
      name: `Ponto ${i + 1}`,
      category_slug: i < 100 ? 'hospedagem' : 'alimentacao',
      category_label: i < 100 ? 'Hospedagem' : 'Alimentação',
      color: i < 100 ? '#2563EB' : '#D97706',
      icon: i < 100 ? 'bed' : 'utensils',
      latitude: -2.5 + (i * 0.001),
      longitude: -54.9 + (i * 0.001),
      layer: 'route_corridor',
    }));

    (useRouteMapQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: {
        route_id: 'route-pindobal',
        origin_id: 'origin-porto',
        geometry: null,
        bounds: { min_lat: -2.7, max_lat: -2.3, min_lng: -55, max_lng: -54.7 },
        city_bounds: { min_lat: -2.8, max_lat: -2.2, min_lng: -55.2, max_lng: -54.5 },
        pins: pins175,
        legend: [
          { category_slug: 'hospedagem', label: 'Hospedagem', color: '#2563EB', icon: 'bed', count: 100, sort_order: 1 },
          { category_slug: 'alimentacao', label: 'Alimentação', color: '#D97706', icon: 'utensils', count: 75, sort_order: 2 },
        ],
      },
      refetch: jest.fn(),
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const labels = renderer.root.findAllByType(require('react-native').Text)
      .map((node) => node.props.children);
    expect(labels).toContain('Hospedagem (100)');
    expect(labels).toContain('Alimentação (75)');
    expect(renderer.root.findAllByType(require('react-native').Text)
      .some((node) => node.props.children === 'Mapa temporariamente indisponível')).toBe(false);
  });

  it.each([
    ['OFFLINE', 'Mapa indisponível offline'],
    ['TIMEOUT', 'O mapa demorou para responder'],
  ])('expõe estado %s com retry acessível', async (code, expectedTitle) => {
    const refetch = jest.fn();
    (useRouteMapQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: true,
      error: { code },
      refetch,
    });
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => { currentRenderer = renderer = TestRenderer.create(<MapScreen />); });
    expect(renderer.root.findAllByType(require('react-native').Text)
      .some((node) => node.props.children === expectedTitle)).toBe(true);
    const retry = renderer.root.find((node) => node.props.accessibilityLabel === 'Tentar Novamente');
    await act(async () => retry.props.onPress());
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it('desabilita modo cidade sem city_bounds em vez de reutilizar bounds da rota', async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => { currentRenderer = renderer = TestRenderer.create(<MapScreen />); });
    const cityButton = renderer.root.find(
      (node) => node.props.accessibilityLabel === 'Modo de visualização da cidade'
    );
    expect(cityButton.props.accessibilityState).toEqual({ selected: false, disabled: true });
    expect(renderer.root.findAllByType(require('react-native').Text)
      .some((node) => node.props.children === 'A visualização da cidade não está disponível para esta origem.')).toBe(true);
  });

  it('rejeita metadata inválida com retry em vez de renderizar fallback', async () => {
    const refetch = jest.fn();
    (useRouteMapQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: {
        route_id: 'route-pindobal', origin_id: 'origin-porto', geometry: null, bounds: null,
        pins: [{ id: 'pin-1', actor_id: 'actor-1', name: 'Inválido', category_slug: 'hospedagem', category_label: 'Hospedagem', color: 'blue', icon: 'bed', latitude: -2.5, longitude: -54.9 }],
        legend: [{ category_slug: 'hospedagem', label: 'Hospedagem', color: 'blue', icon: 'bed', count: 1, sort_order: 1 }],
      },
      refetch,
    });
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => { currentRenderer = renderer = TestRenderer.create(<MapScreen />); });
    expect(renderer.root.findAllByType(require('react-native').Text)
      .some((node) => node.props.children === 'Mapa temporariamente indisponível')).toBe(true);
    expect(renderer.root.findAll((node) => node.props.accessibilityLabel === 'Selecionar pin Pousada Pindobal')).toHaveLength(0);
  });

  it('abre o catálogo preservando routeId, originId e actorId', async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const root = renderer.root;
    const pin = root.find(
      (node) => node.props.accessibilityLabel === 'Selecionar pin Pousada Pindobal'
    );
    await act(async () => pin.props.onPress());

    const catalogButton = root.find(
      (node) => node.props.accessibilityLabel === 'Ver Pousada Pindobal no catálogo'
    );
    expect(catalogButton.type).toBe(TouchableOpacity);

    await act(async () => catalogButton.props.onPress());

    expect(push).toHaveBeenCalledWith(
      '/route/route-pindobal/catalog?originId=origin-porto&actorId=actor-1&viewMode=route'
    );
  });

  it('alterna entre modo rota e modo cidade com acessibilidade e atualiza visualização', async () => {
    (useRouteMapQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      data: {
        route_id: 'route-pindobal',
        origin_id: 'origin-porto',
        geometry: null,
        bounds: { min_lat: -2.7, max_lat: -2.5, min_lng: -55, max_lng: -54.8 },
        city_bounds: { min_lat: -2.8, max_lat: -2.4, min_lng: -55.2, max_lng: -54.5 },
        pins: [
          {
            id: 'pin-1',
            actor_id: 'actor-1',
            name: 'Pousada Pindobal',
            category_slug: 'hospedagem',
            category_label: 'Hospedagem',
            color: '#2563EB',
            icon: 'bed',
            layer: 'route_corridor',
          },
          {
            id: 'pin-2',
            actor_id: 'actor-2',
            name: 'Restaurante Alter',
            category_slug: 'alimentacao',
            category_label: 'Alimentação',
            color: '#D97706',
            icon: 'utensils',
            layer: 'citywide_essential',
          },
        ],
        legend: [
          { category_slug: 'hospedagem', label: 'Hospedagem', color: '#2563EB', icon: 'bed', count: 1, sort_order: 3 },
          { category_slug: 'alimentacao', label: 'Alimentação', color: '#D97706', icon: 'utensils', count: 1, sort_order: 1 },
        ],
      },
      refetch: jest.fn(),
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const root = renderer.root;

    // Verify tabs accessibility
    const routeTab = root.find(
      (node) => node.props.accessibilityLabel === 'Modo de visualização da rota'
    );
    const cityTab = root.find(
      (node) => node.props.accessibilityLabel === 'Modo de visualização da cidade'
    );

    expect(routeTab.props.accessibilityRole).toBe('button');
    expect(routeTab.props.accessibilityState).toEqual({ selected: true, disabled: false });
    expect(cityTab.props.accessibilityRole).toBe('button');
    expect(cityTab.props.accessibilityState).toEqual({ selected: false, disabled: false });
    expect(root.find((node) => node.props.accessibilityLabel === 'Bounds ativos do mapa').props.children)
      .toBe(JSON.stringify({ min_lat: -2.7, max_lat: -2.5, min_lng: -55, max_lng: -54.8 }));

    // Switch to city mode
    await act(async () => cityTab.props.onPress());

    expect(routeTab.props.accessibilityState).toEqual({ selected: false, disabled: false });
    expect(cityTab.props.accessibilityState).toEqual({ selected: true, disabled: false });
    expect(root.find((node) => node.props.accessibilityLabel === 'Bounds ativos do mapa').props.children)
      .toBe(JSON.stringify({ min_lat: -2.8, max_lat: -2.4, min_lng: -55.2, max_lng: -54.5 }));

    // Return to route button should appear
    const returnToRouteButton = root.find(
      (node) => node.props.accessibilityLabel === 'Voltar para a rota'
    );
    expect(returnToRouteButton).toBeDefined();

    // Click return to route button
    await act(async () => returnToRouteButton.props.onPress());
    expect(routeTab.props.accessibilityState).toEqual({ selected: true, disabled: false });
    expect(cityTab.props.accessibilityState).toEqual({ selected: false, disabled: false });
    expect(root.find((node) => node.props.accessibilityLabel === 'Bounds ativos do mapa').props.children)
      .toBe(JSON.stringify({ min_lat: -2.7, max_lat: -2.5, min_lng: -55, max_lng: -54.8 }));
  });

  it('disables selection mode and ignores mode=select-origin when dynamicRouting is false (remediation ECO-2311)', async () => {
    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: false },
      },
      dispatch: jest.fn(),
    });

    (useRouter as jest.Mock).mockReturnValue({ push, back: jest.fn() });
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
      originId: 'origin-porto',
      mode: 'select-origin',
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const root = renderer.root;

    // Selection mode header must NOT be displayed
    const selectionHeaders = root.findAllByProps({ accessibilityRole: 'summary' });
    const instructionHeader = selectionHeaders.find((h) =>
      h.props.children?.some?.((c: any) => c?.props?.children?.includes?.('ponto de partida'))
    );
    expect(instructionHeader).toBeUndefined();

    // Map click area for coordinate selection should NOT be rendered
    const mapClickArea = root.findAll(
      (node) => node.props.accessibilityLabel === 'Clicar no mapa para selecionar coordenada'
    );
    expect(mapClickArea).toHaveLength(0);

    // Standard mode tabs should remain visible
    const routeTab = root.find(
      (node) => node.props.accessibilityLabel === 'Modo de visualização da rota'
    );
    expect(routeTab).toBeDefined();
  });

  it('handles origin selection mode: click map, display coordinates, confirm and cancel (ECO-2311)', async () => {
    const { useAppContext } = require('../../state/useAppContext');
    const { initialAppState } = require('../../state/appReducer');
    (useAppContext as jest.Mock).mockReturnValue({
      state: {
        ...initialAppState,
        featureFlags: { ...initialAppState.featureFlags, dynamicRouting: true },
      },
      dispatch: jest.fn(),
    });

    const back = jest.fn();
    const setQueryDataMock = jest.fn();
    const { useQueryClient } = require('@tanstack/react-query');
    (useQueryClient as jest.Mock).mockReturnValue({ setQueryData: setQueryDataMock });

    (useRouter as jest.Mock).mockReturnValue({ push, back });
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
      originId: 'origin-porto',
      mode: 'select-origin',
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const root = renderer.root;

    // In selection mode, header instruction is displayed
    const mapClickArea = root.find(
      (node) => node.props.accessibilityLabel === 'Clicar no mapa para selecionar coordenada'
    );
    expect(mapClickArea).toBeDefined();

    // Actor sheet modal should NOT open when pin is clicked in selection mode
    const pin = root.find(
      (node) => node.props.accessibilityLabel === 'Selecionar pin Pousada Pindobal'
    );
    await act(async () => pin.props.onPress());
    const modal = root.findByType(Modal);
    expect(modal.props.visible).toBe(false);

    // Select a coordinate by clicking the map
    await act(async () => mapClickArea.props.onPress());

    // Confirm and Cancel buttons should appear
    const confirmButton = root.find(
      (node) => node.props.accessibilityLabel === 'Confirmar ponto de partida escolhido'
    );
    const cancelButton = root.find(
      (node) => node.props.accessibilityLabel === 'Cancelar seleção de ponto de partida'
    );
    expect(confirmButton).toBeDefined();
    expect(cancelButton).toBeDefined();

    // Confirm selection calls api preview, stores ephemeral preview and triggers router.back
    await act(async () => confirmButton.props.onPress());
    expect(setQueryDataMock).toHaveBeenCalledWith(
      ['routes', 'ephemeral-preview', 'route-pindobal'],
      expect.objectContaining({
        originType: 'map-selection-preview',
        previewData: expect.objectContaining({
          distance_m: 10000,
          duration_s: 600,
        }),
      })
    );
    expect(back).toHaveBeenCalled();
  });

  it('renders ephemeral preview pins, geometry and bounds when expanded from dynamic preview (ECO-2312)', async () => {
    const { useQueryClient } = require('@tanstack/react-query');
    const dynamicPreviewData = {
      distance_m: 12000,
      duration_s: 900,
      provider: 'dynamic_preview',
      geojson: { type: 'LineString', coordinates: [[-54.71, -2.45], [-54.91, -2.55]] },
      bounds: { min_lat: -2.55, max_lat: -2.45, min_lng: -54.91, max_lng: -54.71 },
      city_bounds: { min_lat: -2.8, max_lat: -2.3, min_lng: -55.1, max_lng: -54.5 },
      pins: [
        {
          id: 'pin-dyn-1',
          actor_id: 'actor-dyn-1',
          name: 'Barraca Pindobal Sol',
          category_slug: 'alimentacao',
          category_label: 'Alimentação',
          color: '#D97706',
          icon: 'utensils',
          latitude: -2.50,
          longitude: -54.80,
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
      setQueryData: jest.fn(),
    });

    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      currentRenderer = renderer = TestRenderer.create(<MapScreen />);
    });

    const root = renderer.root;
    const boundsText = root.find((node) => node.props.accessibilityLabel === 'Bounds ativos do mapa');
    expect(boundsText).toBeDefined();
    expect(boundsText.props.children).toContain('-2.55');
  });
});
