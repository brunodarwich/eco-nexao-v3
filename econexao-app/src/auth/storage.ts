import type { SupportedStorage } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const memory = new Map<string, string>();

function getWebLocalStorage(): Storage | null {
  if (typeof window !== 'undefined' && window.localStorage) {
    try {
      return window.localStorage;
    } catch {
      return null;
    }
  }
  return null;
}

export const authStorage: SupportedStorage = {
  getItem: async (key: string): Promise<string | null> => {
    if (typeof Platform !== 'undefined' && Platform?.OS && Platform.OS !== 'web') {
      try {
        return await SecureStore.getItemAsync(key);
      } catch {
        return null;
      }
    }
    const storage = getWebLocalStorage();
    if (storage) {
      try {
        return storage.getItem(key);
      } catch {
        return memory.get(key) ?? null;
      }
    }
    return memory.get(key) ?? null;
  },

  setItem: async (key: string, value: string): Promise<void> => {
    if (Platform.OS !== 'web') {
      try {
        await SecureStore.setItemAsync(key, value, {
          keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
        });
      } catch (err) {
        console.warn('SecureStore setItem failed:', err instanceof Error ? err.message : String(err));
      }
      return;
    }
    const storage = getWebLocalStorage();
    if (storage) {
      try {
        storage.setItem(key, value);
      } catch {
        memory.set(key, value);
      }
    } else {
      memory.set(key, value);
    }
  },

  removeItem: async (key: string): Promise<void> => {
    if (Platform.OS !== 'web') {
      try {
        await SecureStore.deleteItemAsync(key);
      } catch {
        // ignore errors on deletion of missing key
      }
      return;
    }
    const storage = getWebLocalStorage();
    if (storage) {
      try {
        storage.removeItem(key);
      } catch {
        memory.delete(key);
      }
    }
    memory.delete(key);
  },
};
