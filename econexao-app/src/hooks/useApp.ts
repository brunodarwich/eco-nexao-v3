import { useContext } from 'react';
import { AppContext, AppContextType } from '../state/AppContext';

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp deve ser utilizado dentro de um AppContextProvider');
  }
  return context;
};
