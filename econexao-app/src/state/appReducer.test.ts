import { appReducer, initialAppState } from './appReducer';

describe('AppContext state contract', () => {
  it('contém somente região e preferências globais', () => {
    expect(Object.keys(initialAppState).sort()).toEqual(['accessibility', 'activeRegionId']);
  });

  it('não possui coleções de dados remotos no reducer (delegado ao TanStack Query)', () => {
    const stateKeys = Object.keys(initialAppState);
    const remoteCollections = ['routes', 'actors', 'categories', 'userProfile', 'alerts', 'origins'];
    remoteCollections.forEach((collection) => {
      expect(stateKeys).not.toContain(collection);
    });
  });

  it('atualiza região e acessibilidade sem mutar o estado anterior', () => {
    const region = appReducer(initialAppState, { type: 'SET_ACTIVE_REGION', payload: 'region-a' });
    const accessible = appReducer(region, { type: 'SET_ACCESSIBILITY', payload: { highContrast: true } });
    expect(initialAppState.activeRegionId).toBeNull();
    expect(region.activeRegionId).toBe('region-a');
    expect(accessible.accessibility.highContrast).toBe(true);
  });
});

