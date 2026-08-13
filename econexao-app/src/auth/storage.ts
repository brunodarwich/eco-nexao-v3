import type { SupportedStorage } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const memory = new Map<string, string>();

export const authStorage: SupportedStorage = {
  getItem: async (key: string): Promise<string | null> => {
    if (Platform.OS !== 'web') {
      try {
        return await SecureStore.getItemAsync(key);
      } catch {
        return null;
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
    memory.set(key, value);
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
    memory.delete(key);
  },
};
