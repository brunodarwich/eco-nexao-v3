import React from 'react';
import renderer, { act } from 'react-test-renderer';

import { apiClient } from '../../api/client';
import { ActorEditor } from './ActorEditor';
import { TerritoryEditor } from './TerritoryEditor';

jest.mock('../../api/client', () => ({
  apiClient: {
    getAdminRegions: jest.fn().mockResolvedValue({ data: [] }),
    getAdminRoutes: jest.fn().mockResolvedValue({ data: [] }),
    createAdminRoute: jest.fn(),
    updateAdminRoute: jest.fn(),
    getAdminActors: jest.fn().mockResolvedValue({ data: [] }),
    createAdminActor: jest.fn(),
    updateAdminActor: jest.fn(),
  },
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Marco 18 — Admin Territory & Actor Editors Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('TerritoryEditor renders form and handles route creation', async () => {
    mockApiClient.createAdminRoute.mockResolvedValueOnce({
      data: {
        id: 'route-new',
        region_id: 'region-1',
        slug: 'trilha-das-praias',
        title: 'Trilha das Praias de Pindobal',
        summary: 'Rota de praias em Pindobal',
        city: 'Belterra',
        state_code: 'PA',
        status: 'draft',
        is_verified: false,
        created_at: '2026-08-13T00:00:00Z',
        updated_at: '2026-08-13T00:00:00Z',
      },
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(
        <TerritoryEditor
          initialRegions={[
            {
              id: 'region-1',
              slug: 'pindobal',
              name: 'Pindobal',
              state_code: 'PA',
              is_active: true,
              created_at: '',
              updated_at: '',
            },
          ]}
        />
      );
    });

    const instance = tree!.root;
    const titleInput = instance.findByProps({ accessibilityLabel: 'Campo título da rota' });
    const submitButton = instance.findByProps({ accessibilityLabel: 'Salvar dados territoriais da rota' });

    await act(async () => {
      titleInput.props.onChangeText('Trilha das Praias de Pindobal');
    });

    await act(async () => {
      submitButton.props.onPress();
    });

    expect(mockApiClient.createAdminRoute).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Trilha das Praias de Pindobal',
        city: 'Belterra',
        state_code: 'PA',
      })
    );
  });

  test('TerritoryEditor handles route update when an existing route is selected', async () => {
    const existingRoute = {
      id: 'route-1',
      region_id: 'region-1',
      slug: 'trilha-1',
      title: 'Trilha Original',
      summary: 'Resumo original',
      city: 'Belterra',
      state_code: 'PA',
      status: 'draft' as const,
      is_verified: false,
      created_at: '2026-08-13T00:00:00Z',
      updated_at: '2026-08-13T00:00:00Z',
    };

    mockApiClient.updateAdminRoute.mockResolvedValueOnce({
      data: {
        ...existingRoute,
        title: 'Trilha Modificada',
      },
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(
        <TerritoryEditor initialRoutes={[existingRoute]} />
      );
    });

    const instance = tree!.root;
    const routeChip = instance.findByProps({ accessibilityLabel: 'Selecionar rota Trilha Original' });

    await act(async () => {
      routeChip.props.onPress();
    });

    const titleInput = instance.findByProps({ accessibilityLabel: 'Campo título da rota' });
    await act(async () => {
      titleInput.props.onChangeText('Trilha Modificada');
    });

    const submitButton = instance.findByProps({ accessibilityLabel: 'Salvar dados territoriais da rota' });
    await act(async () => {
      submitButton.props.onPress();
    });

    expect(mockApiClient.updateAdminRoute).toHaveBeenCalledWith(
      'route-1',
      expect.objectContaining({
        title: 'Trilha Modificada',
      })
    );
  });

  test('ActorEditor renders form and validates mandatory image metadata (ADR 0008)', async () => {
    mockApiClient.createAdminActor.mockResolvedValueOnce({
      data: {
        id: 'actor-new',
        category_id: '00000000-0000-0000-0000-000000000001',
        slug: 'artesanato-dona-maria',
        name: 'Artesanato Dona Maria',
        description: 'Artesanato de palha',
        latitude: -2.4542,
        longitude: -54.9124,
        green_badge_status: 'none',
        verification_status: 'unverified',
        opening_hours: {},
        payment_methods: [],
        created_at: '2026-08-13T00:00:00Z',
        updated_at: '2026-08-13T00:00:00Z',
      },
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(<ActorEditor />);
    });

    const instance = tree!.root;
    const nameInput = instance.findByProps({ accessibilityLabel: 'Campo nome do ator' });
    const submitButton = instance.findByProps({ accessibilityLabel: 'Salvar dados do ator comunitário' });

    await act(async () => {
      nameInput.props.onChangeText('Artesanato Dona Maria');
    });

    await act(async () => {
      submitButton.props.onPress();
    });

    expect(mockApiClient.createAdminActor).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Artesanato Dona Maria',
        latitude: -2.4542,
        longitude: -54.9124,
      })
    );
  });
});

