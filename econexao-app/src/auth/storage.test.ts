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

  describe('Web', () => {
    beforeEach(() => {
      Platform.OS = 'web';
    });

    it('armazena e recupera valores em memória sem acessar SecureStore', async () => {
      await authStorage.setItem('web-key', 'web-token-xyz');
      expect(SecureStore.setItemAsync).not.toHaveBeenCalled();

      const retrieved = await authStorage.getItem('web-key');
      expect(retrieved).toBe('web-token-xyz');
      expect(SecureStore.getItemAsync).not.toHaveBeenCalled();

      await authStorage.removeItem('web-key');
      expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();

      const empty = await authStorage.getItem('web-key');
      expect(empty).toBeNull();
    });
  });
});
