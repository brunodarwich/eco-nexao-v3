import React from 'react';
import { Stack } from 'expo-router';
import { theme } from '../../../src/theme/theme';

export default function ExploreStackLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.surfaceBackground },
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="route/[routeId]/index" options={{ headerShown: false }} />
      <Stack.Screen name="route/[routeId]/map" options={{ headerShown: false }} />
      <Stack.Screen name="route/[routeId]/catalog" options={{ headerShown: false }} />
      <Stack.Screen name="actor/[actorId]" options={{ headerShown: false }} />
    </Stack>
  );
}
