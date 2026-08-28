import React from 'react';
import renderer, { act } from 'react-test-renderer';

import CatalogScreen from '../../../app/route/[routeId]/catalog';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useActorCategoriesQuery, useInfiniteRouteActorsQuery, useMyFavoriteActorsQuery } from '../../hooks/queries';
import { ActorCard } from '../catalog/ActorCard';

const mockToggleFavoriteActor = jest.fn();

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));

jest.mock('../common/GooglePlacePhoto', () => ({
  GooglePlacePhoto: () => null,
}));

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

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({ user: { id: 'user-1' } }),
}));

jest.mock('../../hooks/queries', () => ({
  flattenUniquePages: (pages?: Array<{ data: Array<{ id: string }> }>) => {
    const seen = new Set<string>();
    return (pages ?? []).flatMap((page) => page.data).filter((item) => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  },
  useRegionsQuery: jest.fn().mockReturnValue({ data: [] }),
  useActorCategoriesQuery: jest.fn(),
  useInfiniteRouteActorsQuery: jest.fn(),
  useMyFavoriteActorsQuery: jest.fn(),
}));

jest.mock('../../hooks/useOptimisticFavoriteActor', () => ({
  useOptimisticFavoriteActor: () => ({
    toggleFavorite: mockToggleFavoriteActor,
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
    (useMyFavoriteActorsQuery as jest.Mock).mockReturnValue({ data: [], isSuccess: true });
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

  it('derives favorite state from the authenticated favorites endpoint', async () => {
    const favoriteActor =
      (useInfiniteRouteActorsQuery as jest.Mock).mock.results[0]?.value?.data?.pages?.[0]?.data?.[1] ?? {
        id: 'actor-2',
        slug: 'ator-2',
        name: 'Ator Dois',
        category_slug: 'alimentacao',
        category_label: 'Alimentação',
        green_badge_status: 'verified',
        verification_status: 'verified',
      };
    (useMyFavoriteActorsQuery as jest.Mock).mockReturnValue({
      data: [favoriteActor],
      isSuccess: true,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<CatalogScreen />);
    });

    const favoriteCard = tree.root.findAllByType(ActorCard)[1];
    expect(favoriteCard.props.isFavorite).toBe(true);
    await act(async () => favoriteCard.props.onToggleFavorite());
    expect(mockToggleFavoriteActor).toHaveBeenCalledWith(favoriteCard.props.actor, true);
  });
});
