import React from 'react';
import { Stack } from 'expo-router';
import { theme } from '../../../src/theme/theme';

export default function ProfileStackLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.surfaceBackground },
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="trips" options={{ headerShown: false }} />
      <Stack.Screen name="favorite-routes" options={{ headerShown: false }} />
      <Stack.Screen name="favorite-actors" options={{ headerShown: false }} />
      <Stack.Screen name="accessibility" options={{ headerShown: false }} />
      <Stack.Screen name="support" options={{ headerShown: false }} />
      <Stack.Screen name="legal" options={{ headerShown: false }} />
      <Stack.Screen name="route/[routeId]/index" options={{ headerShown: false }} />
      <Stack.Screen name="route/[routeId]/map" options={{ headerShown: false }} />
      <Stack.Screen name="route/[routeId]/catalog" options={{ headerShown: false }} />
      <Stack.Screen name="actor/[actorId]" options={{ headerShown: false }} />
    </Stack>
  );
}
