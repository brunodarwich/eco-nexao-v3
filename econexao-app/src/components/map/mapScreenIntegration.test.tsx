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

jest.mock('../common/AppHeader', () => ({
  AppHeader: () => null,
}));

jest.mock('../catalog/CategoryFilters', () => ({
  CategoryFilters: () => null,
}));

jest.mock('./MapAdapter', () => {
  const React = require('react');
  const { TouchableOpacity, Text } = require('react-native');

  return {
    MapAdapter: ({ onSelectActor }: { onSelectActor: (actorId: string) => void }) => (
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Selecionar pin Pousada Pindobal"
        onPress={() => onSelectActor('actor-1')}
      >
        <Text>Pin</Text>
      </TouchableOpacity>
    ),
  };
});

describe('MapScreen actor sheet (ECO-0905)', () => {
  const push = jest.fn();

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
        bounds: null,
        pins: [
          {
            id: 'pin-1',
            actor_id: 'actor-1',
            name: 'Pousada Pindobal',
            category_slug: 'hospedagem',
            latitude: -2.5,
            longitude: -54.9,
            distance_from_origin_m: 1500,
          },
        ],
        legend: [],
      },
      refetch: jest.fn(),
    });
    (useActorCategoriesQuery as jest.Mock).mockReturnValue({ data: [] });
    (useRouteActorsQuery as jest.Mock).mockReturnValue({
      data: {
        data: [
          {
            id: 'actor-1',
            name: 'Pousada Pindobal',
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
      renderer = TestRenderer.create(<MapScreen />);
    });

    const root = renderer.root;
    const pin = root.find(
      (node) => node.props.accessibilityLabel === 'Selecionar pin Pousada Pindobal'
    );

    await act(async () => pin.props.onPress());

    const modal = root.findByType(Modal);
    expect(modal.props.visible).toBe(true);
    expect(modal.props.accessibilityViewIsModal).toBe(true);

    const backdrop = root.find(
      (node) => node.props.accessibilityLabel === 'Fechar preview do ator pelo fundo'
    );
    await act(async () => backdrop.props.onPress());

    expect(root.findByType(Modal).props.visible).toBe(false);
    expect(push).not.toHaveBeenCalled();
  });

  it('abre o catálogo preservando routeId, originId e actorId', async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<MapScreen />);
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
      '/route/route-pindobal/catalog?originId=origin-porto&actorId=actor-1'
    );
  });
});
