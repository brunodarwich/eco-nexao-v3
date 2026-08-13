import { useContext } from 'react';

import { AuthContext } from '../auth/AuthProvider';

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth deve ser utilizado dentro de AuthProvider.');
  return value;
}
