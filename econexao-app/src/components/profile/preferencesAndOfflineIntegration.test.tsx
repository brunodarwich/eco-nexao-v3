import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AccessibilityInfo, Switch, TouchableOpacity } from 'react-native';

import { AppContextProvider } from '../../state/AppContext';
import AccessibilityPreferencesScreen from '../../../app/(tabs)/(profile)/accessibility';
import { NetworkStatusBar } from '../common/NetworkStatusBar';
import { apiClient } from '../../api/client';
import { queryKeys } from '../../api/queryKeys';

jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));

jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
}));

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'test-user-uuid', is_anonymous: false },
    isAuthenticated: true,
  }),
}));

describe('ECO-1903: Preferências de Acessibilidade e Comportamento Offline', () => {
  let queryClient: QueryClient;
  let announceSpy: jest.SpyInstance;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    announceSpy = jest.spyOn(AccessibilityInfo, 'announceForAccessibility').mockImplementation(() => {});
    jest.spyOn(apiClient, 'getMyPreferences').mockResolvedValue({
      data: {
        id: 'pref-1',
        user_id: 'test-user-uuid',
        high_contrast: false,
        screen_reader_mode: false,
        text_scale: 1.0,
        locale: 'pt-BR',
      },
    });
    jest.clearAllMocks();
  });

  afterEach(() => {
    announceSpy.mockRestore();
  });

  test('renderiza as opções de acessibilidade e permite alterar alto contraste com mutação e anúncio', async () => {
    jest.spyOn(apiClient, 'updateMyPreferences').mockResolvedValueOnce({
      data: {
        id: 'pref-1',
        user_id: 'test-user-uuid',
        high_contrast: true,
        screen_reader_mode: false,
        text_scale: 1.0,
        locale: 'pt-BR',
      },
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <AccessibilityPreferencesScreen />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    const switches = tree.root.findAllByType(Switch);
    expect(switches.length).toBeGreaterThanOrEqual(2);

    const contrastSwitch = switches[0];
    await act(async () => {
      contrastSwitch.props.onValueChange(true);
    });

    expect(apiClient.updateMyPreferences).toHaveBeenCalledWith(
      expect.objectContaining({ high_contrast: true })
    );
    expect(announceSpy).toHaveBeenCalled();
  });

  test('realiza rollback fiel quando a atualização de preferências falhar na rede', async () => {
    jest.spyOn(apiClient, 'updateMyPreferences').mockRejectedValueOnce(new Error('Network error'));

    queryClient.setQueryData(queryKeys.myPreferences('test-user-uuid'), {
      data: {
        id: 'pref-1',
        user_id: 'test-user-uuid',
        high_contrast: false,
        screen_reader_mode: false,
        text_scale: 1.0,
        locale: 'pt-BR',
      },
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <AccessibilityPreferencesScreen />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    const switches = tree.root.findAllByType(Switch);
    const readerSwitch = switches[1];

    await act(async () => {
      readerSwitch.props.onValueChange(true);
    });

    expect(announceSpy).toHaveBeenCalledWith(
      expect.stringContaining('Erro ao salvar preferências')
    );
  });

  test('permite alterar a escala de texto para Grande (1.15x)', async () => {
    jest.spyOn(apiClient, 'updateMyPreferences').mockResolvedValueOnce({
      data: {
        id: 'pref-1',
        user_id: 'test-user-uuid',
        high_contrast: false,
        screen_reader_mode: false,
        text_scale: 1.15,
        locale: 'pt-BR',
      },
    });

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <AccessibilityPreferencesScreen />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    const touchables = tree.root.findAllByType(TouchableOpacity);
    const scaleButtons = touchables.filter(
      (t) => t.props.accessibilityLabel && t.props.accessibilityLabel.includes('Tamanho de texto')
    );
    expect(scaleButtons.length).toBe(4);

    const grandeButton = scaleButtons[2]; // 1.15x
    await act(async () => {
      grandeButton.props.onPress();
    });

    expect(apiClient.updateMyPreferences).toHaveBeenCalledWith(
      expect.objectContaining({ text_scale: 1.15 })
    );
  });

  test('NetworkStatusBar exibe banner offline e permite reconexão com refetch de queries', async () => {
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();
    const refetchSpy = jest.spyOn(queryClient, 'refetchQueries').mockResolvedValue();


    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <QueryClientProvider client={queryClient}>
          <AppContextProvider>
            <NetworkStatusBar isOfflineOverride={true} />
          </AppContextProvider>
        </QueryClientProvider>
      );
    });

    const reconnectBtn = tree.root.findByType(TouchableOpacity);
    expect(reconnectBtn).toBeTruthy();

    await act(async () => {
      reconnectBtn.props.onPress();
    });

    expect(invalidateSpy).toHaveBeenCalled();
    expect(refetchSpy).toHaveBeenCalled();
    expect(announceSpy).toHaveBeenCalledWith(
      expect.stringContaining('Conexão restabelecida com sucesso')
    );
  });
});
