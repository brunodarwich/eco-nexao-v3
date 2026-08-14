import React from 'react';
import { router } from 'expo-router';

import { AdminShell } from '../../src/components/admin/AdminShell';
import { useAuth } from '../../src/hooks/useAuth';

export default function AdminIndexScreen() {
  const { status, signOut } = useAuth();

  return (
    <AdminShell
      isAuthenticated={status === 'authenticated'}
      onGoHome={() => router.replace('/(tabs)')}
      onLogout={() => {
        void signOut().finally(() => router.replace('/(tabs)'));
      }}
    />
  );
}
