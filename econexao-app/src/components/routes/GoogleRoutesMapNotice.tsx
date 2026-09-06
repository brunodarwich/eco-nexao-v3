import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import * as Linking from 'expo-linking';

import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';

const GOOGLE_MAPS_TERMS_URL = 'https://maps.google.com/help/terms_maps/';

interface GoogleRoutesMapNoticeProps {
  distanceMeters: number;
  durationSeconds: number;
}

export const GoogleRoutesMapNotice: React.FC<GoogleRoutesMapNoticeProps> = ({
  distanceMeters,
  durationSeconds,
}) => (
  <View
    style={styles.container}
    accessibilityRole="alert"
    accessibilityLiveRegion="polite"
    accessibilityLabel="Trajeto calculado pelo Google Maps sem exibição sobre o mapa OpenStreetMap"
  >
    <Text style={styles.title}>Trajeto calculado pelo Google Maps</Text>
    <Text style={styles.body}>
      A visualização deste percurso no mapa estará disponível quando o mapa Google estiver habilitado.
    </Text>
    <Text style={styles.metrics}>
      Distância estimada: {(distanceMeters / 1000).toFixed(1)} km • Tempo: ~{Math.round(durationSeconds / 60)} min
    </Text>
    <TouchableOpacity
      onPress={() => void Linking.openURL(GOOGLE_MAPS_TERMS_URL)}
      {...makeAccessibleButton(
        'Google Maps — consultar termos adicionais',
        'Abre os Termos Adicionais do Google Maps'
      )}
      accessibilityRole="link"
    >
      <Text style={styles.attribution}>Google Maps</Text>
    </TouchableOpacity>
  </View>
);

const styles = StyleSheet.create({
  container: {
    minHeight: 180,
    justifyContent: 'center',
    alignItems: 'flex-start',
    gap: 10,
    padding: 20,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: theme.colors.outlineVariant,
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  title: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    fontWeight: '700',
  },
  body: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
  },
  metrics: {
    ...theme.typography.labelMd,
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
  attribution: {
    ...theme.typography.labelMd,
    color: theme.colors.brandForest,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
});
