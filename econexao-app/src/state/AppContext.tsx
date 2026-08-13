import React, { createContext, useReducer, useEffect, ReactNode } from 'react';
import { appReducer, AppAction, AppState, initialAppState } from './appReducer';
import { useBootstrapQuery } from '../hooks/queries';
import { useAuth } from '../hooks/useAuth';

export interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);

function AppStateSync({ children, dispatch, activeRegionId }: { children: ReactNode; dispatch: React.Dispatch<AppAction>; activeRegionId: string | null }) {
  const { user } = useAuth();
  const userId = user?.id ?? '';
  const bootstrap = useBootstrapQuery(userId);

  useEffect(() => {
    if (bootstrap.data) {
      const serverActiveRegionId = bootstrap.data.active_region?.id || bootstrap.data.supported_regions?.[0]?.id;
      if (serverActiveRegionId && serverActiveRegionId !== activeRegionId) {
        dispatch({ type: 'SET_ACTIVE_REGION', payload: serverActiveRegionId });
      }
    }
  }, [bootstrap.data, activeRegionId, dispatch]);

  return <>{children}</>;
}

export const AppContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialAppState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      <AppStateSync dispatch={dispatch} activeRegionId={state.activeRegionId}>
        {children}
      </AppStateSync>
    </AppContext.Provider>
  );
};
