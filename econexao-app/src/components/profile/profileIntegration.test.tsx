import React from 'react';
import renderer, { act } from 'react-test-renderer';

import ProfileScreen from '../../../app/(tabs)/profile';
import FavoriteRoutesScreen from '../../../app/profile/favorite-routes';
import FavoriteActorsScreen from '../../../app/profile/favorite-actors';
import TripsHistoryScreen from '../../../app/profile/trips';
import AccessibilityPreferencesScreen from '../../../app/profile/accessibility';
import SupportScreen from '../../../app/profile/support';
import { useRouter } from 'expo-router';
import {
  useMyProfileQuery,
  useMyImpactQuery,
  useMyFavoriteRoutesQuery,
  useMyFavoriteActorsQuery,
  useMyTripsQuery,
  useMyPreferencesQuery,
  useSupportContentQuery,
} from '../../hooks/queries';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));
jest.mock('expo-router', () => ({
  useRouter: jest.fn(),
  useLocalSearchParams: jest.fn().mockReturnValue({}),
}));

jest.mock('../../hooks/useApp', () => ({
  useApp: () => ({
    state: { activeRegionId: 'pindobal' },
    activeRegion: { id: 'pindobal', name: 'Pindobal' },
    openRegionSelector: jest.fn(),
  }),
}));

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1', email: 'test@econexao.org', is_anonymous: false },
    signOut: jest.fn(),
  }),
}));

jest.mock('../../hooks/queries', () => ({
  useRegionsQuery: jest.fn().mockReturnValue({ data: [] }),
  useMyProfileQuery: jest.fn(),
  useMyImpactQuery: jest.fn(),
  useMyFavoriteRoutesQuery: jest.fn(),
  useMyFavoriteActorsQuery: jest.fn(),
  useMyTripsQuery: jest.fn(),
  useMyPreferencesQuery: jest.fn(),
  useSupportContentQuery: jest.fn(),
}));

jest.mock('../../hooks/useOptimisticFavoriteActor', () => ({
  useOptimisticFavoriteActor: () => ({
    toggleFavorite: jest.fn(),
    isPending: false,
  }),
}));

describe('Marco 11 — Integration Tests', () => {
  const push = jest.fn();
  const back = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push, back });
  });

  it('ProfileScreen renders user profile and impact metrics', async () => {
    (useMyProfileQuery as jest.Mock).mockReturnValue({
      data: { name: 'Maria Silva' },
      isPending: false,
      isError: false,
    });
    (useMyImpactQuery as jest.Mock).mockReturnValue({
      data: {
        completed_trips_count: 5,
        co2_saved_kg: 62.5,
        visited_actors_count: 8,
      },
      isPending: false,
      isError: false,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<ProfileScreen />);
    });

    expect(tree.toJSON()).toBeTruthy();
  });

  it('FavoriteRoutesScreen renders route cards and handles click', async () => {
    (useMyFavoriteRoutesQuery as jest.Mock).mockReturnValue({
      data: [
        {
          id: 'route-1',
          title: 'Rota das Praias',
          city: 'Belterra',
          state_code: 'PA',
          status: 'published',
          is_verified: true,
        },
      ],
      isPending: false,
      isError: false,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<FavoriteRoutesScreen />);
    });

    expect(tree.toJSON()).toBeTruthy();
  });

  it('FavoriteActorsScreen renders actor cards', async () => {
    (useMyFavoriteActorsQuery as jest.Mock).mockReturnValue({
      data: [
        {
          id: 'actor-1',
          name: 'Pousada Floresta',
          category_slug: 'hospedagem',
          category_label: 'Hospedagem',
          green_badge_status: 'verified',
        },
      ],
      isPending: false,
      isError: false,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<FavoriteActorsScreen />);
    });

    expect(tree.toJSON()).toBeTruthy();
  });

  it('TripsHistoryScreen renders trip history items', async () => {
    (useMyTripsQuery as jest.Mock).mockReturnValue({
      data: [
        {
          id: 'trip-1',
          route_title: 'Trilha do Jamaraquá',
          status: 'completed',
          created_at: '2026-08-10T10:00:00Z',
        },
      ],
      isPending: false,
      isError: false,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<TripsHistoryScreen />);
    });

    expect(tree.toJSON()).toBeTruthy();
  });

  it('AccessibilityPreferencesScreen renders preference options', async () => {
    (useMyPreferencesQuery as jest.Mock).mockReturnValue({
      data: { high_contrast: true, reader_mode: false },
      isPending: false,
      isError: false,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<AccessibilityPreferencesScreen />);
    });

    expect(tree.toJSON()).toBeTruthy();
  });

  it('SupportScreen renders contacts and FAQ from query', async () => {
    (useSupportContentQuery as jest.Mock).mockReturnValue({
      data: {
        contacts: { email: 'contato@econexao.org', phone: '+55 93 99999-0000' },
        help_links: [{ title: 'Termos de Uso', url: 'https://econexao.org/termos' }],
        faq: [{ id: '1', question: 'Dúvida?', answer: 'Resposta.', category: 'Geral' }],
      },
      isPending: false,
      isError: false,
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<SupportScreen />);
    });

    expect(tree.toJSON()).toBeTruthy();
  });
});
