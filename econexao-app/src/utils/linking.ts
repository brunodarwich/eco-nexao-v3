/**
 * Deep Linking configuration and utilities for ECOnexão.
 * Supports custom scheme (econexao://) and web universal links.
 */

export const APP_SCHEME = 'econexao';

export interface DeepLinkTarget {
  path: string;
  params?: Record<string, string>;
}

export const DeepLinkRoutes = {
  HOME: '/',
  ROUTES: '/routes',
  MAP: '/map',
  PROFILE: '/profile',
  ROUTE_DETAIL: (routeId: string) => `/route/${encodeURIComponent(routeId)}`,
  ROUTE_MAP: (routeId: string) => `/route/${encodeURIComponent(routeId)}/map`,
  ROUTE_CATALOG: (routeId: string) => `/route/${encodeURIComponent(routeId)}/catalog`,
  PROFILE_ACCESSIBILITY: '/profile/accessibility',
  PROFILE_TRIPS: '/profile/trips',
  PROFILE_LEGAL: '/profile/legal',
  ADMIN: '/admin',
} as const;

/**
 * Creates a fully-qualified custom scheme deep link URL.
 */
export function buildDeepLink(path: string, params?: Record<string, string>): string {
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path;
  let url = `${APP_SCHEME}://${normalizedPath}`;
  if (params && Object.keys(params).length > 0) {
    const query = new URLSearchParams(params).toString();
    url += `?${query}`;
  }
  return url;
}

/**
 * Parses and validates an incoming deep link URL into a structured route and parameters.
 */
export function parseDeepLink(url: string): DeepLinkTarget | null {
  try {
    if (!url) return null;
    let urlObj: URL;
    if (url.startsWith(`${APP_SCHEME}://`)) {
      // Convert custom scheme to dummy HTTP for URL parser
      urlObj = new URL(url.replace(`${APP_SCHEME}://`, 'http://localhost/'));
    } else if (url.startsWith('http://') || url.startsWith('https://')) {
      urlObj = new URL(url);
    } else if (url.startsWith('/')) {
      urlObj = new URL(`http://localhost${url}`);
    } else {
      return null;
    }

    const path = urlObj.pathname;
    const params: Record<string, string> = {};
    urlObj.searchParams.forEach((val, key) => {
      params[key] = val;
    });

    return {
      path,
      params: Object.keys(params).length > 0 ? params : undefined,
    };
  } catch {
    return null;
  }
}
