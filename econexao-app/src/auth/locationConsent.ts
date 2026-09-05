import { authStorage } from './storage';

export const CURRENT_LOCATION_POLICY_VERSION = '2026-09-04';
export const LOCATION_CONSENT_STORAGE_KEY = 'econexao_location_consent_v1';

export interface LocationConsentRecord {
  version: string;
  consentedAt: string;
  isAdult: boolean;
  hasConsented: boolean;
}

/**
 * Retorna o registro de consentimento de localizacao dinamica armazenado localmente.
 * Retorna null se nao existir ou se a versao nao coincidir com a versao material vigente.
 * NAO armazena nem retorna coordenadas geograficas, CPF ou data de nascimento.
 */
export async function getLocationConsent(): Promise<LocationConsentRecord | null> {
  try {
    const raw = await authStorage.getItem(LOCATION_CONSENT_STORAGE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as Partial<LocationConsentRecord>;
    if (
      parsed &&
      parsed.version === CURRENT_LOCATION_POLICY_VERSION &&
      parsed.hasConsented === true &&
      parsed.isAdult === true &&
      typeof parsed.consentedAt === 'string'
    ) {
      return {
        version: parsed.version,
        consentedAt: parsed.consentedAt,
        isAdult: parsed.isAdult,
        hasConsented: parsed.hasConsented,
      };
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Verifica de forma rapida se o usuario possui consentimento valido para a versao atual.
 */
export async function hasValidLocationConsent(): Promise<boolean> {
  const consent = await getLocationConsent();
  return Boolean(consent && consent.hasConsented && consent.isAdult);
}

/**
 * Salva o consentimento local explicito para a versao atual da politica.
 * Valida obrigatoriamente maioridade (isAdult) e consentimento afirmativo (hasConsented).
 * NENHUM dado de coordenada ou data de nascimento eh persistido.
 */
export async function saveLocationConsent(isAdult: boolean, hasConsented: boolean): Promise<boolean> {
  if (!isAdult || !hasConsented) {
    return false;
  }

  const record: LocationConsentRecord = {
    version: CURRENT_LOCATION_POLICY_VERSION,
    consentedAt: new Date().toISOString(),
    isAdult: true,
    hasConsented: true,
  };

  try {
    await authStorage.setItem(LOCATION_CONSENT_STORAGE_KEY, JSON.stringify(record));
    return true;
  } catch {
    return false;
  }
}

/**
 * Revoga o consentimento localmente, removendo o registro seguro.
 * Apos a revogacao, novos calculos dinamicos serao impedidos ate novo aceite explicito.
 * Nao apaga outras preferencias ou sessao do usuario.
 */
export async function revokeLocationConsent(): Promise<boolean> {
  try {
    await authStorage.removeItem(LOCATION_CONSENT_STORAGE_KEY);
    return true;
  } catch {
    return false;
  }
}
