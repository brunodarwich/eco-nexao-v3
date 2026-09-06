import { Platform } from 'react-native';
import * as Linking from 'expo-linking';

export interface ParsedOAuthCallback {
  type: 'success' | 'error' | 'cancel' | 'none';
  code?: string;
  accessToken?: string;
  refreshToken?: string;
  error?: string;
  errorDescription?: string;
}

/**
 * Retorna a URI canonica de redirecionamento OAuth.
 * No ambiente Web utiliza a origem do navegador (window.location.origin).
 * No ambiente nativo utiliza o esquema registrado pelo expo-linking.
 */
export function getOAuthRedirectUri(): string {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined' && window.location?.origin) {
      return `${window.location.origin}/`;
    }
    return 'http://localhost:8081/';
  }
  return Linking.createURL('/');
}

/**
 * Faz o parsing de uma URL ou string de busca/hash em busca de parametros de retorno OAuth.
 */
export function parseOAuthUrl(rawUrl: string): ParsedOAuthCallback {
  if (!rawUrl) return { type: 'none' };

  try {
    const dummyBase = 'https://app.econexao.local';
    const parsed = new URL(
      rawUrl.startsWith('http')
        ? rawUrl
        : `${dummyBase}/${rawUrl.replace(/^[/?#]/, '')}`
    );

    const params = new URLSearchParams(parsed.search);

    let hashParams = new URLSearchParams();
    if (parsed.hash && parsed.hash.length > 1) {
      hashParams = new URLSearchParams(parsed.hash.substring(1));
    }

    const error = params.get('error') || hashParams.get('error');
    const errorDescription =
      params.get('error_description') ||
      hashParams.get('error_description') ||
      undefined;

    if (error) {
      if (
        error === 'access_denied' ||
        error === 'user_cancelled' ||
        errorDescription?.includes('denied') ||
        errorDescription?.includes('cancel')
      ) {
        return {
          type: 'cancel',
          error,
          errorDescription: errorDescription ?? 'Autenticacao cancelada pelo usuario.',
        };
      }
      return {
        type: 'error',
        error,
        errorDescription: errorDescription ?? 'Erro no retorno da autenticacao.',
      };
    }

    const code = params.get('code') || hashParams.get('code');
    if (code) {
      return {
        type: 'success',
        code,
      };
    }

    const accessToken = params.get('access_token') || hashParams.get('access_token');
    const refreshToken = params.get('refresh_token') || hashParams.get('refresh_token');
    if (accessToken) {
      return {
        type: 'success',
        accessToken,
        refreshToken: refreshToken ?? undefined,
      };
    }

    return { type: 'none' };
  } catch {
    return { type: 'none' };
  }
}

/**
 * Verifica se a janela Web atual possui parametros de retorno OAuth.
 */
export function getWebLocationOAuthCallback(): ParsedOAuthCallback {
  if (Platform.OS !== 'web' || typeof window === 'undefined' || !window.location) {
    return { type: 'none' };
  }
  return parseOAuthUrl(window.location.href);
}

/**
 * Limpa os parametros de busca e hash OAuth da URL do navegador sem recarregar a pagina.
 */
export function cleanWebOAuthUrl(): void {
  if (Platform.OS !== 'web' || typeof window === 'undefined' || !window.history?.replaceState) {
    return;
  }
  try {
    const cleanUrl = window.location.origin + window.location.pathname;
    window.history.replaceState({}, document.title, cleanUrl);
  } catch {
    // Silently ignore
  }
}
