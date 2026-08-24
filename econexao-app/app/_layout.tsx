import React, { useContext } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import {
  useFonts,
  HankenGrotesk_400Regular,
  HankenGrotesk_500Medium,
  HankenGrotesk_600SemiBold,
  HankenGrotesk_700Bold,
  HankenGrotesk_800ExtraBold,
} from '@expo-google-fonts/hanken-grotesk';
import { AppContextProvider } from '../src/state/AppContext';
import { LoadingView, ErrorStateView } from '../src/components/common/UIStateViews';
import { theme } from '../src/theme/theme';
import { AuthContext, AuthProvider } from '../src/auth/AuthProvider';
import { ServerStateProvider } from '../src/api/ServerStateProvider';
import { NetworkStatusBar } from '../src/components/common/NetworkStatusBar';
import { ErrorBoundary } from '../src/components/common/ErrorBoundary';

function LayoutContent() {
  return (
    <>
      <StatusBar style="dark" />
      <NetworkStatusBar />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: theme.colors.surfaceBackground },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="admin/index"
          options={{ headerShown: false, title: 'Painel Editorial' }}
        />
      </Stack>
    </>
  );
}

function AuthGate({ children }: React.PropsWithChildren) {
  const auth = useContext(AuthContext);
  if (!auth || auth.status === 'initializing') {
    return <LoadingView message="Criando uma sessão segura..." />;
  }
  if (auth.status === 'error' || auth.status === 'signed_out') {
    return (
      <ErrorStateView
        message={
          auth.status === 'signed_out'
            ? 'Sua sessão foi encerrada. Tente novamente para criar uma nova sessão.'
            : auth.error?.message ?? 'Não foi possível iniciar sua sessão.'
        }
        onRetry={auth.retry}
      />
    );
  }
  return <>{children}</>;
}

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    HankenGrotesk_400Regular,
    HankenGrotesk_500Medium,
    HankenGrotesk_600SemiBold,
    HankenGrotesk_700Bold,
    HankenGrotesk_800ExtraBold,
  });

  if (!fontsLoaded) {
    return <LoadingView message="Carregando tipografia e recursos do ECOnexão..." />;
  }

  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <AuthProvider>
          <ServerStateProvider>
            <AuthGate>
              <AppContextProvider>
                <LayoutContent />
              </AppContextProvider>
            </AuthGate>
          </ServerStateProvider>
        </AuthProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}
