import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Pressable, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import type { RouteSummary } from '../../api/types';
import { Badge } from '../common/Badge';
import { makeAccessibleButton } from '../../utils/accessibility';

interface CompactRouteCardProps {
  route: RouteSummary;
  onPress: () => void;
  onToggleFavorite?: () => void;
  isFavorite?: boolean;
}

export const CompactRouteCard: React.FC<CompactRouteCardProps> = ({
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
          {route.cover_image_url ? <Image source={{ uri: route.cover_image_url }} style={styles.image} resizeMode="cover" accessibilityLabel={`Imagem da rota ${route.title}`} /> : <View style={styles.imagePlaceholder}><Ionicons name="map-outline" size={36} color={theme.colors.brandSage} /></View>}
          <View style={styles.gradientOverlay} />

          <View style={styles.topRow}>
            {route.is_verified ? (
              <Badge type="verified" label="Verificada" />
            ) : (
              <View />
            )}
          </View>
        </View>

        <View style={styles.contentContainer}>
          <View style={styles.categoryRow}>
            <Text style={styles.categoryText} numberOfLines={1}>
              {route.best_season ?? ''}
            </Text>
          </View>

          <Text style={styles.title} numberOfLines={1}>
            {route.title}
          </Text>

          <View style={styles.footerRow}>
            <View style={styles.infoBadge}>
              <Ionicons name="navigate-outline" size={13} color={theme.colors.brandSage} />
              <Text style={styles.infoText} numberOfLines={1}>
                {[route.city, route.state_code].filter(Boolean).join(', ')}
              </Text>
            </View>
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
            name={isFavorite ? 'bookmark' : 'bookmark-outline'}
            size={18}
            color={isFavorite ? theme.colors.brandForest : theme.colors.onSurfaceVariant}
          />
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    width: 240,
    backgroundColor: theme.colors.surfaceWhite,
    borderRadius: theme.radii.xl,
    overflow: 'hidden',
    position: 'relative',
    ...theme.shadows.card,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
    marginRight: theme.spacing.stackMd,
  },
  cardPressable: {
    width: '100%',
  },
  imageContainer: {
    height: 130,
    width: '100%',
    position: 'relative',
    backgroundColor: theme.colors.surfaceContainerLow,
    justifyContent: 'space-between',
    padding: 8,
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
  imagePlaceholder: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  gradientOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(28, 59, 15, 0.15)',
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    zIndex: 5,
  },
  favoriteButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 32,
    height: 32,
    borderRadius: theme.radii.full,
    backgroundColor: 'rgba(249, 250, 247, 0.92)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 2,
    elevation: 2,
  },
  contentContainer: {
    padding: 12,
    gap: 4,
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    textTransform: 'uppercase',
    fontWeight: '700',
    letterSpacing: 0.5,
    fontSize: 11,
  },
  title: {
    ...theme.typography.titleMd,
    color: theme.colors.brandDeep,
    fontWeight: '700',
    marginTop: 2,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
  },
  infoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  infoText: {
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 12,
  },
});
