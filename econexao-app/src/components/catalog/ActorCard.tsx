import React, { useEffect, useRef } from 'react';
import {
  AccessibilityInfo,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Pressable,
  Image,
  Platform,
  findNodeHandle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import type { ActorSummary } from '../../api/types';
import { Badge } from '../common/Badge';
import { makeAccessibleButton } from '../../utils/accessibility';

export interface ActorCardProps {
  actor: ActorSummary;
  onPress?: () => void;
  onToggleFavorite?: () => void;
  isFavorite?: boolean;
  focusOnMount?: boolean;
}

export const ActorCard: React.FC<ActorCardProps> = ({
  actor,
  onPress,
  onToggleFavorite,
  isFavorite,
  focusOnMount = false,
}) => {
  const pressableRef = useRef<View>(null);

  useEffect(() => {
    if (!focusOnMount || !pressableRef.current) return;

    if (Platform.OS === 'web') {
      (pressableRef.current as unknown as { focus?: () => void }).focus?.();
      return;
    }

    const reactTag = findNodeHandle(pressableRef.current);
    if (reactTag != null) AccessibilityInfo.setAccessibilityFocus(reactTag);
  }, [focusOnMount]);

  const effectiveIsFavorite = isFavorite ?? false;
  const categoryName = actor.category_label.toUpperCase();
  const hasGreenSeal = actor.green_badge_status === 'verified';
  const ratingValue = actor.google_rating;
  const imageUrl = actor.cover_media?.derivatives?.card ?? actor.cover_media?.url ?? actor.cover_image_url;

  return (
    <View style={styles.card}>
      <Pressable
        ref={pressableRef}
        style={styles.cardPressable}
        onPress={onPress}
        {...makeAccessibleButton(
          `Estabelecimento ${actor.name}`,
          `${categoryName}. ${actor.address ? `Endereço: ${actor.address}.` : ''} ${ratingValue ? `Avaliação ${ratingValue}.` : ''} Toque para ver detalhes.`
        )}
      >
        <View style={styles.imageContainer}>
          {imageUrl ? (
            <Image source={{ uri: imageUrl }} style={styles.image} resizeMode="cover" />
          ) : (
            <View style={styles.placeholderImage}>
              <Ionicons name="storefront-outline" size={40} color={theme.colors.brandSage} />
            </View>
          )}

          <View style={styles.badgeRow}>
            {hasGreenSeal && <Badge type="greenSeal" label="Selo Verde" />}
          </View>
        </View>

        <View style={styles.content}>
          <View style={styles.headerRow}>
            <Text style={styles.categoryTag}>{categoryName}</Text>
            {ratingValue != null && (
              <View style={styles.ratingRow}>
                <Ionicons name="star" size={14} color={theme.colors.brandSun} />
                <Text style={styles.ratingText}>{ratingValue.toFixed(1)} Google</Text>
              </View>
            )}
          </View>

          <Text style={styles.name}>{actor.name}</Text>
          {actor.address ? (
            <Text style={styles.address} numberOfLines={1}>
              <Ionicons name="location-outline" size={13} color={theme.colors.brandSage} /> {actor.address}
            </Text>
          ) : null}

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
            effectiveIsFavorite ? 'Remover ator dos favoritos' : 'Salvar ator nos favoritos'
          )}
        >
          <Ionicons
            name={effectiveIsFavorite ? 'heart' : 'heart-outline'}
            size={18}
            color={effectiveIsFavorite ? theme.colors.error : theme.colors.onSurface}
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
    height: 160,
    width: '100%',
    position: 'relative',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholderImage: {
    width: '100%',
    height: '100%',
    backgroundColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeRow: {
    position: 'absolute',
    top: 12,
    left: 12,
    zIndex: 10,
  },
  favoriteButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 34,
    height: 34,
    borderRadius: theme.radii.full,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 20,
  },
  content: {
    padding: theme.spacing.marginMobile,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  categoryTag: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  ratingText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontWeight: '700',
  },
  name: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    marginBottom: 4,
  },
  address: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    marginBottom: 8,
  },
});
