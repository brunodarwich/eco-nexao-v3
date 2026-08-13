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
import { Actor } from '../../types';
import { Badge } from '../common/Badge';
import { makeAccessibleButton } from '../../utils/accessibility';

interface ActorCardProps {
  actor: Actor;
  onPress?: () => void;
  onToggleFavorite?: () => void;
  isFavorite?: boolean;
  focusOnMount?: boolean;
}

export const ActorCard: React.FC<ActorCardProps> = ({
  actor,
  onPress,
  onToggleFavorite,
  isFavorite = false,
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

  return (
    <View style={styles.card}>
      <Pressable
        ref={pressableRef}
        style={styles.cardPressable}
        onPress={onPress}
        {...makeAccessibleButton(
          `Ator local ${actor.name}`,
          `${actor.subCategory}. Avaliação ${actor.rating}. Endereço ${actor.address}. Toque para ver detalhes.`
        )}
      >
        <View style={styles.imageContainer}>
          <Image source={actor.imageUrl} style={styles.image} resizeMode="cover" />
          <View style={styles.badgeRow}>
            {actor.greenBadge && <Badge type="greenSeal" label="Selo Verde" />}
          </View>
        </View>

        <View style={styles.content}>
          <View style={styles.headerRow}>
            <Text style={styles.categoryTag}>{actor.subCategory.toUpperCase()}</Text>
            <View style={styles.ratingRow}>
              <Ionicons name="star" size={14} color={theme.colors.brandSun} />
              <Text style={styles.ratingText}>
                {actor.rating} ({actor.reviewCount})
              </Text>
            </View>
          </View>

          <Text style={styles.name}>{actor.name}</Text>
          <Text style={styles.address} numberOfLines={1}>
            <Ionicons name="location-outline" size={13} color={theme.colors.brandSage} /> {actor.address}
          </Text>

          <Text style={styles.description} numberOfLines={2}>
            {actor.description}
          </Text>

          {actor.accessibilityFeatures.length > 0 && (
            <View style={styles.a11yRow}>
              <Ionicons name="accessibility" size={12} color={theme.colors.brandLeaf} />
              <Text style={styles.a11yText} numberOfLines={1}>
                {actor.accessibilityFeatures.join(' • ')}
              </Text>
            </View>
          )}
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
            isFavorite ? 'Remover ator dos favoritos' : 'Salvar ator nos favoritos'
          )}
        >
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={18}
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
    height: 160,
    width: '100%',
    position: 'relative',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  image: {
    width: '100%',
    height: '100%',
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
  description: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 10,
  },
  a11yRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: theme.colors.surfaceContainerLow,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: theme.radii.sm,
    alignSelf: 'flex-start',
  },
  a11yText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandLeaf,
    fontSize: 11,
    fontWeight: '600',
  },
});
