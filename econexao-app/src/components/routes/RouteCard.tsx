import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Pressable, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import type { RouteSummary } from '../../api/types';
import { Badge } from '../common/Badge';
import { makeAccessibleButton } from '../../utils/accessibility';

interface RouteCardProps {
  route: RouteSummary;
  onPress: () => void;
  onToggleFavorite?: () => void;
  isFavorite?: boolean;
}

export const RouteCard: React.FC<RouteCardProps> = ({
  route,
  onPress,
  onToggleFavorite,
  isFavorite = false,
}) => {
  return (
    <View style={styles.card}>
      <Pressable
        style={styles.cardPressable}
        onPress={onPress}
        {...makeAccessibleButton(
          `Rota ${route.title}`,
          `${route.city}, ${route.state_code}. Toque para ver os detalhes.`
        )}
      >
        <View style={styles.imageContainer}>
          <Image
            source={route.cover_image_url ? { uri: route.cover_image_url } : require('../../../assets/images/hero_tapajos_sunset.jpg')}
            style={styles.image}
            resizeMode="cover"
          />
          <View style={styles.gradientOverlay} />

          <View style={styles.topRow}>
            {route.is_verified && <Badge type="verified" label="Verificada" />}
          </View>

          <View style={styles.bottomOverlayContent}>
            <View style={styles.locationRow}>
              <Ionicons name="location-sharp" size={14} color={theme.colors.onPrimaryContainer} />
              <Text style={styles.locationText}>
                {route.city}, {route.state_code}
              </Text>
            </View>
            <Text style={styles.title}>{route.title}</Text>
            {route.summary ? <Text style={styles.metaText} numberOfLines={2}>{route.summary}</Text> : null}
          </View>
        </View>
      </Pressable>

      {onToggleFavorite && (
        <TouchableOpacity
          style={styles.favoriteButton}
          onPress={(e) => {
            e.stopPropagation();
            onToggleFavorite();
          }}
          {...makeAccessibleButton(
            isFavorite ? 'Remover dos favoritos' : 'Salvar rota nos favoritos'
          )}
        >
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={20}
            color={isFavorite ? theme.colors.error : theme.colors.onSurface}
          />
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.xl,
    overflow: 'hidden',
    marginBottom: theme.spacing.stackMd,
    position: 'relative',
    ...theme.shadows.card,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
  },
  cardPressable: {
    width: '100%',
  },
  imageContainer: {
    height: 220,
    width: '100%',
    position: 'relative',
    justifyContent: 'space-between',
    padding: theme.spacing.marginMobile,
  },
  image: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: '100%',
    height: '100%',
  },
  gradientOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(28, 59, 15, 0.45)',
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    zIndex: 10,
  },
  favoriteButton: {
    position: 'absolute',
    top: theme.spacing.marginMobile,
    right: theme.spacing.marginMobile,
    width: 38,
    height: 38,
    borderRadius: theme.radii.full,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 20,
  },
  bottomOverlayContent: {
    zIndex: 10,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 2,
  },
  locationText: {
    ...theme.typography.labelSm,
    color: theme.colors.onPrimaryContainer,
    fontWeight: '700',
  },
  title: {
    ...theme.typography.headlineMd,
    color: theme.colors.surfaceWhite,
    marginBottom: 6,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    ...theme.typography.labelSm,
    color: 'rgba(255, 255, 255, 0.9)',
  },
});
