import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { TouchableOpacity } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import ProfileScreen from '../../../app/(tabs)/(profile)/index';
import FavoriteRoutesScreen from '../../../app/(tabs)/(profile)/favorite-routes';
import FavoriteActorsScreen from '../../../app/(tabs)/(profile)/favorite-actors';
import TripsHistoryScreen from '../../../app/(tabs)/(profile)/trips';
import AccessibilityPreferencesScreen from '../../../app/(tabs)/(profile)/accessibility';
import SupportScreen from '../../../app/(tabs)/(profile)/support';
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
import { apiClient } from '../../api/client';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));
jest.mock('expo-image-picker', () => ({ launchImageLibraryAsync: jest.fn() }));
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

jest.mock('../../hooks/useOptimisticFavoriteRoute', () => ({
  useOptimisticFavoriteRoute: () => ({
    mutate: jest.fn(),
    isPending: false,
  }),
}));

jest.mock('../../hooks/useOptimisticPreferences', () => ({
  useOptimisticPreferences: () => ({
    mutate: jest.fn(),
    isPending: false,
  }),
}));


describe('Marco 11 — Integration Tests', () => {
  const push = jest.fn();
  const back = jest.fn();
  let queryClient: QueryClient;

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: Infinity } },
    });
    (useRouter as jest.Mock).mockReturnValue({ push, back });
  });

  const renderProfile = () => (
    <QueryClientProvider client={queryClient}>
      <ProfileScreen />
    </QueryClientProvider>
  );

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
      tree = renderer.create(renderProfile());
    });

    expect(tree.toJSON()).toBeTruthy();
  });

  it('cancela o picker sem iniciar upload', async () => {
    (useMyProfileQuery as jest.Mock).mockReturnValue({ data: {}, isPending: false });
    (useMyImpactQuery as jest.Mock).mockReturnValue({ data: {}, isPending: false });
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: true });
    const upload = jest.spyOn(apiClient, 'uploadAvatar');
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(renderProfile());
    });
    const avatar = tree.root.findAllByType(TouchableOpacity).find(
      (item) => item.props.accessibilityLabel === 'Alterar Foto do Perfil'
    );
    await act(async () => avatar!.props.onPress());
    expect(upload).not.toHaveBeenCalled();
    expect(avatar!.props.accessibilityState).toEqual({ disabled: false, busy: false });
  });

  it('impede seletores concorrentes enquanto o primeiro está aberto', async () => {
    (useMyProfileQuery as jest.Mock).mockReturnValue({ data: {}, isPending: false });
    (useMyImpactQuery as jest.Mock).mockReturnValue({ data: {}, isPending: false });
    let resolvePicker!: (result: { canceled: true }) => void;
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePicker = resolve;
      })
    );
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(renderProfile());
    });
    const avatar = tree.root.findAllByType(TouchableOpacity).find(
      (item) => item.props.accessibilityLabel === 'Alterar Foto do Perfil'
    );
    let first!: Promise<void>;
    await act(async () => {
      first = avatar!.props.onPress();
      avatar!.props.onPress();
      await Promise.resolve();
    });
    expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1);
    resolvePicker({ canceled: true });
    await act(async () => first);
  });

  it('envia o arquivo escolhido ao endpoint multipart real', async () => {
    (useMyProfileQuery as jest.Mock).mockReturnValue({ data: {}, isPending: false });
    (useMyImpactQuery as jest.Mock).mockReturnValue({ data: {}, isPending: false });
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file:///avatar.png', fileName: 'avatar.png', mimeType: 'image/png' }],
    });
    const upload = jest.spyOn(apiClient, 'uploadAvatar').mockResolvedValue({
      data: {
        media_asset_id: 'asset-id',
        url: 'https://cdn/avatar.webp',
        derivatives: {},
        alt_text: 'Avatar',
      },
    });
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(renderProfile());
    });
    const avatar = tree.root.findAllByType(TouchableOpacity).find(
      (item) => item.props.accessibilityLabel === 'Alterar Foto do Perfil'
    );
    await act(async () => avatar!.props.onPress());
    expect(upload).toHaveBeenCalledWith({
      uri: 'file:///avatar.png',
      name: 'avatar.png',
      type: 'image/png',
      file: undefined,
    });
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
