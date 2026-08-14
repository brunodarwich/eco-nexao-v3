import React from 'react';
import renderer, { act } from 'react-test-renderer';

import CatalogScreen from '../../../app/route/[routeId]/catalog';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useActorCategoriesQuery, useInfiniteRouteActorsQuery } from '../../hooks/queries';
import { ActorCard } from '../catalog/ActorCard';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));

jest.mock('expo-router', () => ({
  useLocalSearchParams: jest.fn(),
  useRouter: jest.fn(),
}));

jest.mock('../../hooks/useApp', () => ({
  useApp: () => ({
    state: { activeRegionId: 'pindobal' },
    activeRegion: { id: 'pindobal', name: 'Pindobal' },
    openRegionSelector: jest.fn(),
    isRegionModalOpen: false,
    closeRegionSelector: jest.fn(),
  }),
}));

jest.mock('../../hooks/queries', () => ({
  useRegionsQuery: jest.fn().mockReturnValue({ data: [] }),
  useActorCategoriesQuery: jest.fn(),
  useInfiniteRouteActorsQuery: jest.fn(),
}));

jest.mock('../../hooks/useOptimisticFavoriteActor', () => ({
  useOptimisticFavoriteActor: () => ({
    toggleFavorite: jest.fn(),
    isPending: false,
  }),
}));

describe('CatalogScreen route context', () => {
  const push = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push, back: jest.fn() });
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      routeId: 'route-pindobal',
      originId: 'origin-porto',
      actorId: 'actor-2',
    });
    (useActorCategoriesQuery as jest.Mock).mockReturnValue({ data: [] });
    (useInfiniteRouteActorsQuery as jest.Mock).mockReturnValue({
      isPending: false,
      isError: false,
      hasNextPage: false,
      isFetchingNextPage: false,
      data: {
        pages: [
          {
            data: [
              {
                id: 'actor-1',
                slug: 'ator-1',
                name: 'Ator Um',
                category_slug: 'hospedagem',
                category_label: 'Hospedagem',
                green_badge_status: 'none',
                verification_status: 'verified',
              },
              {
                id: 'actor-2',
                slug: 'ator-2',
                name: 'Ator Dois',
                category_slug: 'alimentacao',
                category_label: 'Alimentação',
                green_badge_status: 'verified',
                verification_status: 'verified',
              },
            ],
            meta: { total: 2, limit: 20 },
          },
        ],
      },
      refetch: jest.fn(),
    });
  });

  it('requests actors for the preserved origin and focuses the requested actor', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<CatalogScreen />);
    });

    expect(useInfiniteRouteActorsQuery).toHaveBeenCalledWith(
      'route-pindobal',
      expect.objectContaining({ origin_id: 'origin-porto' })
    );
    const cards = tree.root.findAllByType(ActorCard);
    expect(cards).toHaveLength(2);
    expect(cards[0].props.focusOnMount).toBe(false);
    expect(cards[1].props.focusOnMount).toBe(true);
  });

  it('preserves origin context when the focused actor opens', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<CatalogScreen />);
    });

    const focusedCard = tree.root.findAllByType(ActorCard)[1];
    await act(async () => focusedCard.props.onPress());

    expect(push).toHaveBeenCalledWith('/actor/actor-2?originId=origin-porto');
  });
});

