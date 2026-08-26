import { appReducer, initialAppState } from './appReducer';

describe('AppContext state contract', () => {
  it('contém somente região, preferências globais e feature flags', () => {
    expect(Object.keys(initialAppState).sort()).toEqual(['accessibility', 'activeRegionId', 'featureFlags']);
    expect(initialAppState.featureFlags.dynamicRouting).toBe(false);
  });

  it('não possui coleções de dados remotos no reducer (delegado ao TanStack Query)', () => {
    const stateKeys = Object.keys(initialAppState);
    const remoteCollections = ['routes', 'actors', 'categories', 'userProfile', 'alerts', 'origins'];
    remoteCollections.forEach((collection) => {
      expect(stateKeys).not.toContain(collection);
    });
  });

  it('atualiza região, acessibilidade e feature flags sem mutar o estado anterior', () => {
    const region = appReducer(initialAppState, { type: 'SET_ACTIVE_REGION', payload: 'region-a' });
    const accessible = appReducer(region, { type: 'SET_ACCESSIBILITY', payload: { highContrast: true } });
    const withFlags = appReducer(accessible, { type: 'SET_FEATURE_FLAGS', payload: { dynamicRouting: true } });
    expect(initialAppState.activeRegionId).toBeNull();
    expect(initialAppState.featureFlags.dynamicRouting).toBe(false);
    expect(region.activeRegionId).toBe('region-a');
    expect(accessible.accessibility.highContrast).toBe(true);
    expect(withFlags.featureFlags.dynamicRouting).toBe(true);
  });
});
