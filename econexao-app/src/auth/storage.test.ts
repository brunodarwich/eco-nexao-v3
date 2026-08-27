import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import { authStorage } from './storage';

jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
  WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'WHEN_UNLOCKED_THIS_DEVICE_ONLY',
}));

describe('authStorage', () => {
  const originalPlatform = Platform.OS;

  afterEach(() => {
    Platform.OS = originalPlatform;
    jest.clearAllMocks();
  });

  describe('Nativo (iOS / Android)', () => {
    beforeEach(() => {
      Platform.OS = 'ios';
    });

    it('busca valor usando expo-secure-store', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('secure-token-123');
      const val = await authStorage.getItem('key1');
      expect(val).toBe('secure-token-123');
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('key1');
    });

    it('retorna null se expo-secure-store rejeitar', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(new Error('store failure'));
      const val = await authStorage.getItem('key1');
      expect(val).toBeNull();
    });

    it('grava valor com opção WHEN_UNLOCKED_THIS_DEVICE_ONLY', async () => {
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);
      await authStorage.setItem('key1', 'secret-val');
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('key1', 'secret-val', {
        keychainAccessible: 'WHEN_UNLOCKED_THIS_DEVICE_ONLY',
      });
    });

    it('trata erro de setItem sem lançar exceção não capturada', async () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      (SecureStore.setItemAsync as jest.Mock).mockRejectedValue(new Error('write protected'));
      await expect(authStorage.setItem('key1', 'secret-val')).resolves.toBeUndefined();
      expect(warnSpy).toHaveBeenCalled();
      warnSpy.mockRestore();
    });

    it('remove chave usando deleteItemAsync', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);
      await authStorage.removeItem('key1');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('key1');
    });
  });

  describe('Web (ADR 0007)', () => {
    let mockLocalStorageMap: Map<string, string>;

    beforeEach(() => {
      Platform.OS = 'web';
      mockLocalStorageMap = new Map<string, string>();
      const mockStorage: Storage = {
        getItem: jest.fn((k: string) => mockLocalStorageMap.get(k) ?? null),
        setItem: jest.fn((k: string, v: string) => mockLocalStorageMap.set(k, v)),
        removeItem: jest.fn((k: string) => mockLocalStorageMap.delete(k)),
        clear: jest.fn(() => mockLocalStorageMap.clear()),
        key: jest.fn((i: number) => Array.from(mockLocalStorageMap.keys())[i] ?? null),
        length: 0,
      };
      Object.defineProperty(global, 'window', {
        value: { localStorage: mockStorage },
        writable: true,
        configurable: true,
      });
    });

    afterEach(() => {
      // @ts-expect-error cleanup window
      delete global.window;
    });

    it('persiste no window.localStorage sem acessar SecureStore', async () => {
      await authStorage.setItem('econexao-token', 'token-payload-xyz');
      expect(window.localStorage.setItem).toHaveBeenCalledWith('econexao-token', 'token-payload-xyz');
      expect(SecureStore.setItemAsync).not.toHaveBeenCalled();

      const retrieved = await authStorage.getItem('econexao-token');
      expect(retrieved).toBe('token-payload-xyz');
      expect(window.localStorage.getItem).toHaveBeenCalledWith('econexao-token');
    });

    it('recupera a sessão gravada em localStorage após simulação de reload (reset de memória)', async () => {
      // 1. Grava no localStorage
      mockLocalStorageMap.set('econexao-auth-session', 'persisted-session-12345');

      // 2. Consulta via authStorage
      const recovered = await authStorage.getItem('econexao-auth-session');
      expect(recovered).toBe('persisted-session-12345');
    });

    it('remove chave do localStorage corretamente', async () => {
      mockLocalStorageMap.set('econexao-auth-session', 'persisted-session-12345');
      await authStorage.removeItem('econexao-auth-session');
      expect(window.localStorage.removeItem).toHaveBeenCalledWith('econexao-auth-session');

      const val = await authStorage.getItem('econexao-auth-session');
      expect(val).toBeNull();
    });

    it('faz fallback para memória se window.localStorage não estiver disponível ou falhar', async () => {
      // Simula ausência de window
      // @ts-expect-error remove window
      delete global.window;

      await authStorage.setItem('fallback-key', 'mem-val');
      const val = await authStorage.getItem('fallback-key');
      expect(val).toBe('mem-val');
      expect(SecureStore.getItemAsync).not.toHaveBeenCalled();
    });
  });
});
