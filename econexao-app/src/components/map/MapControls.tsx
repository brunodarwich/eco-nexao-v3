import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';

interface MapControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRecenter: () => void;
  canZoomIn?: boolean;
  canZoomOut?: boolean;
}

export const MapControls: React.FC<MapControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onRecenter,
  canZoomIn = true,
  canZoomOut = true,
}) => {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.button, !canZoomIn && styles.disabledButton]}
        onPress={onZoomIn}
        disabled={!canZoomIn}
        {...makeAccessibleButton('Aumentar zoom no mapa', 'Aumenta o nível de ampliação da câmera do mapa')}
      >
        <Ionicons
          name="add"
          size={20}
          color={canZoomIn ? theme.colors.brandForest : theme.colors.onSurfaceVariant}
        />
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, !canZoomOut && styles.disabledButton]}
        onPress={onZoomOut}
        disabled={!canZoomOut}
        {...makeAccessibleButton('Diminuir zoom no mapa', 'Reduz o nível de ampliação da câmera do mapa')}
      >
        <Ionicons
          name="remove"
          size={20}
          color={canZoomOut ? theme.colors.brandForest : theme.colors.onSurfaceVariant}
        />
      </TouchableOpacity>

      <View style={styles.divider} />

      <TouchableOpacity
        style={styles.button}
        onPress={onRecenter}
        {...makeAccessibleButton('Recentralizar mapa', 'Ajusta a câmera para enquadrar a rota inteira')}
      >
        <Ionicons name="locate" size={20} color={theme.colors.brandForest} />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.lg,
    padding: 4,
    zIndex: 30,
    ...theme.shadows.sm,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
    gap: 4,
  },
  button: {
    width: 44,
    height: 44,
    borderRadius: theme.radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  disabledButton: {
    opacity: 0.4,
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.08)',
    marginVertical: 2,
  },
});
