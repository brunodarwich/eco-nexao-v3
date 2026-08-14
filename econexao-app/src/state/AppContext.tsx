import React, { createContext, useReducer, useEffect, ReactNode } from 'react';
import { appReducer, AppAction, AppState, initialAppState } from './appReducer';
import { useBootstrapQuery, useMyPreferencesQuery } from '../hooks/queries';
import { useAuth } from '../hooks/useAuth';


export interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);

function AppStateSync({
  children,
  dispatch,
  activeRegionId,
  accessibility,
}: {
  children: ReactNode;
  dispatch: React.Dispatch<AppAction>;
  activeRegionId: string | null;
  accessibility: import('./appReducer').AccessibilityPreferences;
}) {
  const { user } = useAuth();
  const userId = user?.id ?? '';
  const bootstrap = useBootstrapQuery(userId);
  const prefsQuery = useMyPreferencesQuery(userId);

  useEffect(() => {
    if (bootstrap.data) {
      const serverActiveRegionId = bootstrap.data.active_region?.id || bootstrap.data.supported_regions?.[0]?.id;
      if (serverActiveRegionId && serverActiveRegionId !== activeRegionId) {
        dispatch({ type: 'SET_ACTIVE_REGION', payload: serverActiveRegionId });
      }
    }
  }, [bootstrap.data, activeRegionId, dispatch]);

  useEffect(() => {
    if (prefsQuery.data) {
      const prefs = prefsQuery.data;
      if (
        prefs.screen_reader_mode !== accessibility.screenReaderMode ||
        prefs.high_contrast !== accessibility.highContrast ||
        (prefs.text_scale && prefs.text_scale !== accessibility.textScale) ||
        (prefs.locale && prefs.locale !== accessibility.locale)
      ) {
        dispatch({
          type: 'SET_ACCESSIBILITY',
          payload: {
            screenReaderMode: prefs.screen_reader_mode ?? false,
            highContrast: prefs.high_contrast ?? false,
            textScale: prefs.text_scale ?? 1.0,
            locale: prefs.locale ?? 'pt-BR',
          },
        });
      }
    }
  }, [prefsQuery.data, accessibility, dispatch]);

  return <>{children}</>;
}

export const AppContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialAppState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      <AppStateSync
        dispatch={dispatch}
        activeRegionId={state.activeRegionId}
        accessibility={state.accessibility}
      >
        {children}
      </AppStateSync>
    </AppContext.Provider>
  );
};

