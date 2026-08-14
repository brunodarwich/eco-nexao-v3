import { useContext } from 'react';
import { AppContext, AppContextType } from './AppContext';
import { initialAppState } from './appReducer';

export function useAppContext(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    return {
      state: initialAppState,
      dispatch: () => {},
    };
  }
  return context;
}
