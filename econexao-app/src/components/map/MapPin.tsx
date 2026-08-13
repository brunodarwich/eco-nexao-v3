import React from 'react';
import { TouchableOpacity, StyleSheet, View, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import type { Actor, CategorySegment } from '../../types';
import type { MapPin as ApiMapPin } from '../../api/types';
import { makeAccessibleButton } from '../../utils/accessibility';

export type FlexiblePinItem = Actor | ApiMapPin;

interface MapPinProps {
  actor: FlexiblePinItem;
  isSelected?: boolean;
  onPress: () => void;
  positionOverride?: { xPercentage: number; yPercentage: number };
}

export const MapPin: React.FC<MapPinProps> = ({
  actor,
  isSelected = false,
  onPress,
  positionOverride,
}) => {
  const isApiPin = 'category_slug' in actor;
  const name = actor.name;
  const categorySlug = isApiPin ? actor.category_slug : actor.segment;

  let pinColor: string = theme.colors.brandForest;
  let iconName: keyof typeof Ionicons.glyphMap = 'location';

  if (categorySlug === 'alimentacao' || categorySlug === 'gastronomia') {
    pinColor = theme.colors.brandSun;
    iconName = 'restaurant';
  } else if (categorySlug === 'hospedagem') {
    pinColor = theme.colors.brandForest;
    iconName = 'bed';
  } else if (categorySlug === 'emergencia' || categorySlug === 'saude') {
    pinColor = theme.colors.error;
    iconName = 'medical';
  } else if (categorySlug === 'artesanato' || categorySlug === 'comercio') {
    pinColor = theme.colors.brandLeaf;
    iconName = 'basket';
  } else if (categorySlug === 'transporte') {
    pinColor = theme.colors.secondaryContainer;
    iconName = 'bus';
  }

  let xPct = 50;
  let yPct = 50;

  if (positionOverride) {
    xPct = positionOverride.xPercentage;
    yPct = positionOverride.yPercentage;
  } else if ('coordinate' in actor && actor.coordinate) {
    xPct = actor.coordinate.xPercentage;
    yPct = actor.coordinate.yPercentage;
  }

  return (
    <TouchableOpacity
      style={[
        styles.pinWrapper,
        {
          left: `${xPct}%`,
          top: `${yPct}%`,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.8}
      {...makeAccessibleButton(
        `Ponto no mapa: ${name}`,
        `Categoria: ${categorySlug}. Toque para selecionar.`
      )}
    >
      <View
        style={[
          styles.pinBadge,
          { backgroundColor: pinColor },
          isSelected && styles.selectedPin,
        ]}
      >
        <Ionicons name={iconName} size={16} color={theme.colors.onPrimary} />
      </View>
      <View style={[styles.pinTail, { borderTopColor: pinColor }]} />
      {isSelected && (
        <View style={styles.tooltip}>
          <Text style={styles.tooltipText} numberOfLines={1}>
            {name}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  pinWrapper: {
    position: 'absolute',
    alignItems: 'center',
    transform: [{ translateX: -16 }, { translateY: -32 }],
    zIndex: 20,
  },
  pinBadge: {
    width: 32,
    height: 32,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    justifyContent: 'center',
    ...theme.shadows.sm,
  },
  selectedPin: {
    transform: [{ scale: 1.25 }],
    borderWidth: 2,
    borderColor: theme.colors.surfaceWhite,
    zIndex: 30,
  },
  pinTail: {
    width: 0,
    height: 0,
    borderLeftWidth: 5,
    borderRightWidth: 5,
    borderTopWidth: 6,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    marginTop: -1,
  },
  tooltip: {
    position: 'absolute',
    bottom: 38,
    backgroundColor: theme.colors.brandDeep,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: theme.radii.sm,
    maxWidth: 150,
  },
  tooltipText: {
    ...theme.typography.labelSm,
    color: theme.colors.surfaceWhite,
    fontSize: 10,
  },
});
