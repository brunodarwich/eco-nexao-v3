import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import {
  getLocationConsent,
  hasValidLocationConsent,
  saveLocationConsent,
  revokeLocationConsent,
  CURRENT_LOCATION_POLICY_VERSION,
  LOCATION_CONSENT_STORAGE_KEY,
} from './locationConsent';
import { authStorage } from './storage';

jest.mock('expo-secure-store', () => {
  const store = new Map<string, string>();
  return {
    getItemAsync: jest.fn((key: string) => Promise.resolve(store.get(key) ?? null)),
    setItemAsync: jest.fn((key: string, value: string) => {
      store.set(key, value);
      return Promise.resolve();
    }),
    deleteItemAsync: jest.fn((key: string) => {
      store.delete(key);
      return Promise.resolve();
    }),
    WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'WHEN_UNLOCKED_THIS_DEVICE_ONLY',
    __store: store,
  };
});

describe('Location Consent Module (LGPD / Dynamic Routing)', () => {
  beforeEach(async () => {
    (SecureStore as any).__store.clear();
    await authStorage.removeItem(LOCATION_CONSENT_STORAGE_KEY);
  });

  afterEach(async () => {
    await authStorage.removeItem(LOCATION_CONSENT_STORAGE_KEY);
  });

  it('returns false/null when no consent has been granted', async () => {
    const consent = await getLocationConsent();
    expect(consent).toBeNull();

    const valid = await hasValidLocationConsent();
    expect(valid).toBe(false);
  });

  it('fails to save when isAdult is false or hasConsented is false', async () => {
    const res1 = await saveLocationConsent(false, true);
    expect(res1).toBe(false);
    expect(await hasValidLocationConsent()).toBe(false);

    const res2 = await saveLocationConsent(true, false);
    expect(res2).toBe(false);
    expect(await hasValidLocationConsent()).toBe(false);
  });

  it('saves valid consent with current policy version and without coordinates or birthdate', async () => {
    const success = await saveLocationConsent(true, true);
    expect(success).toBe(true);

    const valid = await hasValidLocationConsent();
    expect(valid).toBe(true);

    const record = await getLocationConsent();
    expect(record).not.toBeNull();
    expect(record?.version).toBe(CURRENT_LOCATION_POLICY_VERSION);
    expect(record?.isAdult).toBe(true);
    expect(record?.hasConsented).toBe(true);
    expect(typeof record?.consentedAt).toBe('string');

    // Strict privacy verification: Ensure no coordinates or sensitive keys exist in storage
    const rawStored = await authStorage.getItem(LOCATION_CONSENT_STORAGE_KEY);
    expect(rawStored).not.toBeNull();
    const parsed = JSON.parse(rawStored!);
    expect(parsed).not.toHaveProperty('latitude');
    expect(parsed).not.toHaveProperty('longitude');
    expect(parsed).not.toHaveProperty('coords');
    expect(parsed).not.toHaveProperty('birthDate');
    expect(parsed).not.toHaveProperty('cpf');
  });

  it('invalidates consent if stored version differs from current policy version', async () => {
    const outdatedRecord = {
      version: '2026-01-01',
      consentedAt: new Date().toISOString(),
      isAdult: true,
      hasConsented: true,
    };
    await authStorage.setItem(LOCATION_CONSENT_STORAGE_KEY, JSON.stringify(outdatedRecord));

    const consent = await getLocationConsent();
    expect(consent).toBeNull();

    const valid = await hasValidLocationConsent();
    expect(valid).toBe(false);
  });

  it('revokes consent safely, returns true, and does not erase other storage keys', async () => {
    await authStorage.setItem('other_unrelated_key', 'some_value');
    await saveLocationConsent(true, true);

    expect(await hasValidLocationConsent()).toBe(true);

    const result = await revokeLocationConsent();
    expect(result).toBe(true);

    expect(await hasValidLocationConsent()).toBe(false);
    expect(await getLocationConsent()).toBeNull();

    // Verify unrelated key was preserved
    const otherVal = await authStorage.getItem('other_unrelated_key');
    expect(otherVal).toBe('some_value');
    await authStorage.removeItem('other_unrelated_key');
  });

  it('returns false when storage throws an error during revocation', async () => {
    jest.spyOn(authStorage, 'removeItem').mockRejectedValueOnce(new Error('Storage failure'));

    const result = await revokeLocationConsent();
    expect(result).toBe(false);
  });
});
