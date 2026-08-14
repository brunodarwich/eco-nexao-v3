import {
  APP_SCHEME,
  DeepLinkRoutes,
  buildDeepLink,
  parseDeepLink,
} from './linking';

describe('ECO-1905: Deep Linking Utilities', () => {
  test('APP_SCHEME é econexao', () => {
    expect(APP_SCHEME).toBe('econexao');
  });

  test('buildDeepLink gera URLs canônicas com scheme econexao', () => {
    expect(buildDeepLink('/routes')).toBe('econexao://routes');
    expect(buildDeepLink('map')).toBe('econexao://map');
    expect(buildDeepLink(DeepLinkRoutes.ROUTE_DETAIL('trilha-jamaraqua'))).toBe(
      'econexao://route/trilha-jamaraqua'
    );
    expect(
      buildDeepLink(DeepLinkRoutes.ROUTE_CATALOG('trilha-pindobal'), { tab: 'alimentacao' })
    ).toBe('econexao://route/trilha-pindobal/catalog?tab=alimentacao');
    expect(buildDeepLink(DeepLinkRoutes.PROFILE_LEGAL)).toBe('econexao://profile/legal');
    expect(buildDeepLink(DeepLinkRoutes.ADMIN)).toBe('econexao://admin');
  });

  test('parseDeepLink processa corretamente esquemas customizados e parâmetros', () => {
    const parsed1 = parseDeepLink('econexao://route/rota-pindobal');
    expect(parsed1).toEqual({
      path: '/route/rota-pindobal',
      params: undefined,
    });

    const parsed2 = parseDeepLink('econexao://routes?search=rio&category=artesanato');
    expect(parsed2).toEqual({
      path: '/routes',
      params: { search: 'rio', category: 'artesanato' },
    });

    const parsed3 = parseDeepLink('https://econexao.org/profile/accessibility');
    expect(parsed3).toEqual({
      path: '/profile/accessibility',
      params: undefined,
    });

    expect(parseDeepLink('')).toBeNull();
    expect(parseDeepLink('invalid-scheme://foo')).toBeNull();
  });
});
