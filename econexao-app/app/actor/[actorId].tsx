import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
  Image,
  TouchableOpacity,
  Linking,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../src/components/common/AppHeader';
import { Badge } from '../../src/components/common/Badge';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../src/components/common/UIStateViews';
import { GooglePlacePhoto } from '../../src/components/common/GooglePlacePhoto';
import { useActorDetailQuery } from '../../src/hooks/queries';
import { useMyFavoriteActorsQuery } from '../../src/hooks/queries';
import { useOptimisticFavoriteActor } from '../../src/hooks/useOptimisticFavoriteActor';
import { useAuth } from '../../src/hooks/useAuth';
import { theme } from '../../src/theme/theme';
import { makeAccessibleButton } from '../../src/utils/accessibility';
import type { ActorSummary } from '../../src/api/types';

export default function ActorDetailScreen() {
  const router = useRouter();
  const { actorId = '', originId } = useLocalSearchParams<{
    actorId: string;
    originId?: string;
  }>();

  const actorQuery = useActorDetailQuery(actorId);
  const { user } = useAuth();
  const favoriteActorsQuery = useMyFavoriteActorsQuery(user?.id);
  const { toggleFavorite, isPending: isFavPending } = useOptimisticFavoriteActor();

  const actor = actorQuery.data;

  const openExternalLink = async (url: string, label: string) => {
    try {
      const supported = await Linking.canOpenURL(url);
      if (supported) {
        await Linking.openURL(url);
      } else {
        Alert.alert('Link Indisponível', `Não foi possível abrir o link de ${label}: ${url}`);
      }
    } catch {
      Alert.alert('Erro ao Abrir Link', `Ocorreu um erro ao tentar abrir ${label}.`);
    }
  };

  const handlePhoneCall = () => {
    if (!actor?.phone) return;
    const cleanPhone = actor.phone.replace(/[^\d+]/g, '');
    if (!cleanPhone) {
      Alert.alert('Telefone Inválido', 'O número de telefone informado não é válido.');
      return;
    }
    openExternalLink(`tel:${cleanPhone}`, 'telefone');
  };

  const handleOpenWebsite = () => {
    if (!actor?.website) return;
    const url = actor.website.startsWith('http') ? actor.website : `https://${actor.website}`;
    openExternalLink(url, 'website');
  };

  const handleOpenInstagram = () => {
    if (!actor?.instagram) return;
    const handle = actor.instagram.replace(/^@/, '');
    const url = `https://instagram.com/${handle}`;
    openExternalLink(url, 'Instagram');
  };

  const handleOpenMap = () => {
    if (!actor?.latitude || !actor?.longitude) return;
    const lat = actor.latitude;
    const lng = actor.longitude;
    const label = encodeURIComponent(actor.name);
    const url = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}&query_place_id=${actor.google_place_id || ''}`;
    openExternalLink(url, 'mapa');
  };

  if (actorQuery.isPending) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Detalhe do Ator" />
        <LoadingView message="Carregando detalhes do estabelecimento..." />
      </View>
    );
  }

  if (actorQuery.isError || !actor) {
    return (
      <View style={styles.container}>
        <AppHeader showBack onBackPress={() => router.back()} title="Detalhe do Ator" />
        <ErrorStateView
          title="Ator não encontrado"
          message="Não foi possível carregar as informações deste estabelecimento."
          onRetry={() => void actorQuery.refetch()}
        />
      </View>
    );
  }

  const greenSeal = actor.green_badge_status === 'verified';
  const categoryLabel = actor.category?.label || (actor as any).category_label || (actor as any).category_slug || 'Geral';
  const categorySlug = actor.category?.slug || (actor as any).category_slug || 'outros';
  const isFavorite = actor.is_favorite
    || (favoriteActorsQuery.data?.some((favorite) => favorite.id === actor.id) ?? false);
  const actorSummary: ActorSummary = {
    id: actor.id,
    slug: actor.slug,
    name: actor.name,
    category_slug: categorySlug,
    category_label: categoryLabel,
    address: actor.address,
    latitude: actor.latitude,
    longitude: actor.longitude,
    green_badge_status: actor.green_badge_status,
    verification_status: actor.verification_status,
    google_rating: actor.google_rating,
    cover_image_url: actor.cover_image_url,
    cover_media: actor.cover_media,
    is_favorite: isFavorite,
  };
  const coverImageUrl = actor.cover_media?.url ?? actor.cover_image_url;

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title={actor.name} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Cover / Image Banner */}
        <View style={styles.bannerContainer}>
          {coverImageUrl ? (
            <Image
              source={{ uri: coverImageUrl }}
              style={styles.bannerImage}
              resizeMode="cover"
              accessibilityLabel={actor.cover_media?.alt_text ?? `Imagem de ${actor.name}`}
            />
          ) : actor.id ? (
            <GooglePlacePhoto actorId={actor.id} alt={`Foto de ${actor.name}`} />
          ) : (
            <View style={styles.bannerPlaceholder} accessibilityLabel="Imagem não disponível">
              <Ionicons name="storefront-outline" size={48} color={theme.colors.brandSage} />
            </View>
          )}
          <View style={styles.bannerOverlay}>
            <View style={styles.badgeRow}>
              {greenSeal && <Badge type="greenSeal" label="Selo Verde Consciente" />}
              {actor.verification_status === 'verified' && (
                <Badge type="semturInventory" label="Inventário SEMTUR" />
              )}
            </View>

            {favoriteActorsQuery.isSuccess ? (
              <TouchableOpacity
                style={styles.favFloatingButton}
                onPress={() => toggleFavorite(actorSummary, isFavorite)}
                disabled={isFavPending}
                {...makeAccessibleButton(
                  isFavorite ? 'Remover dos favoritos' : 'Salvar nos favoritos'
                )}
              >
                <Ionicons
                  name={isFavorite ? 'heart' : 'heart-outline'}
                  size={22}
                  color={isFavorite ? theme.colors.error : theme.colors.onSurface}
                />
              </TouchableOpacity>
            ) : null}
          </View>
        </View>

        {/* Main Info */}
        <View style={styles.cardSection}>
          <View style={styles.categoryRatingRow}>
            <Text style={styles.categoryTag}>{categoryLabel.toUpperCase()}</Text>
            {actor.google_rating != null && (
              <View style={styles.ratingBadge}>
                <Ionicons name="star" size={14} color={theme.colors.brandSun} />
                <Text style={styles.ratingText}>
                  {actor.google_rating.toFixed(1)} Google
                  {actor.google_review_count ? ` (${actor.google_review_count})` : ''}
                </Text>
              </View>
            )}
          </View>
          <Text style={styles.title}>{actor.name}</Text>

          <View style={styles.locationRow}>
            <Ionicons name="location-outline" size={16} color={theme.colors.brandSage} />
            <Text style={styles.addressText}>
              {[actor.address, actor.city, actor.state_code].filter(Boolean).join(', ') ||
                'Endereço não informado'}
            </Text>
          </View>

          {actor.description && (
            <Text style={styles.description}>{actor.description}</Text>
          )}
        </View>

        {/* SEMTUR Institutional Provenance Note (ADR 0014 §2.6) */}
        {actor.verification_status === 'verified' && (
          <View
            style={styles.semturSection}
            accessible
            accessibilityRole="text"
            accessibilityLabel="Origem dos dados: Inventário SEMTUR"
          >
            <View style={styles.semturHeader}>
              <Ionicons name="bookmark-outline" size={16} color="#334155" />
              <Text style={styles.semturTitle}>Inventário SEMTUR</Text>
            </View>
            <Text style={styles.semturDescription}>
              Este estabelecimento consta no Inventário Turístico divulgado pela Secretaria Municipal de Turismo de Santarém (SEMTUR). As informações refletem o registro público catalogado e estão sujeitas a alterações pelos responsáveis.
            </Text>
          </View>
        )}

        {/* Media Gallery */}
        {Boolean(actor.gallery && actor.gallery.length > 0) && (
          <View style={styles.cardSection}>
            <Text style={styles.sectionTitle}>Galeria de Fotos</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.galleryScroller}
            >
              {actor.gallery!.map((item, index) => (
                <View key={item.url || index} style={styles.galleryItem}>
                  <Image
                    source={{ uri: item.derivatives?.card ?? item.url }}
                    style={styles.galleryImage}
                    resizeMode="cover"
                    accessible
                    accessibilityLabel={item.alt_text || `Foto ${index + 1} de ${actor.name}`}
                  />
                  {item.credit ? (
                    <Text style={styles.galleryCredit} numberOfLines={1}>
                      Foto: {item.credit}
                    </Text>
                  ) : null}
                </View>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Action Buttons / Contacts (ECO-1005) */}
        <View style={styles.cardSection}>
          <Text style={styles.sectionTitle}>Contatos e Localização</Text>
          <View style={styles.contactsGrid}>
            {actor.phone && (
              <TouchableOpacity
                style={styles.contactChip}
                onPress={handlePhoneCall}
                {...makeAccessibleButton('Ligar para telefone', actor.phone)}
              >
                <Ionicons name="call-outline" size={18} color={theme.colors.brandForest} />
                <Text style={styles.contactChipText} numberOfLines={1}>
                  {actor.phone}
                </Text>
              </TouchableOpacity>
            )}

            {actor.website && (
              <TouchableOpacity
                style={styles.contactChip}
                onPress={handleOpenWebsite}
                {...makeAccessibleButton('Abrir site oficial')}
              >
                <Ionicons name="globe-outline" size={18} color={theme.colors.brandForest} />
                <Text style={styles.contactChipText} numberOfLines={1}>
                  Website
                </Text>
              </TouchableOpacity>
            )}

            {actor.instagram && (
              <TouchableOpacity
                style={styles.contactChip}
                onPress={handleOpenInstagram}
                {...makeAccessibleButton('Abrir perfil do Instagram')}
              >
                <Ionicons name="logo-instagram" size={18} color={theme.colors.brandForest} />
                <Text style={styles.contactChipText} numberOfLines={1}>
                  {actor.instagram}
                </Text>
              </TouchableOpacity>
            )}

            {Boolean(actor.latitude && actor.longitude) && (
              <TouchableOpacity
                style={[styles.contactChip, styles.mapChip]}
                onPress={handleOpenMap}
                {...makeAccessibleButton('Abrir no Google Maps', 'Ver localização no aplicativo do Google Maps')}
              >
                <Ionicons name="map-outline" size={18} color={theme.colors.surfaceWhite} />
                <Text style={[styles.contactChipText, styles.mapChipText]} numberOfLines={1}>
                  Abrir no Google Maps
                </Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {actor.cover_media?.credit ? (
          <Text style={styles.mediaCredit}>Crédito da imagem principal: {actor.cover_media.credit}</Text>
        ) : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surfaceBackground,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  bannerContainer: {
    height: 200,
    width: '100%',
    position: 'relative',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  bannerPlaceholder: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.surfaceContainerLow,
  },
  bannerOverlay: {
    position: 'absolute',
    top: 12,
    left: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 6,
  },
  favFloatingButton: {
    width: 40,
    height: 40,
    borderRadius: theme.radii.full,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    ...theme.shadows.card,
  },
  cardSection: {
    backgroundColor: theme.colors.surfaceWhite,
    marginTop: 12,
    marginHorizontal: theme.spacing.marginMobile,
    padding: theme.spacing.marginMobile,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
    ...theme.shadows.card,
  },
  categoryRatingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  ratingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: theme.radii.full,
  },
  ratingText: {
    ...theme.typography.labelSm,
    color: '#92400E',
    fontWeight: '700',
    fontSize: 12,
  },
  categoryTag: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  title: {
    ...theme.typography.headlineMd,
    color: theme.colors.brandDeep,
    marginBottom: 8,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 12,
  },
  addressText: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    flex: 1,
  },
  description: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurface,
    lineHeight: 22,
  },
  semturSection: {
    backgroundColor: '#F8FAFC',
    marginTop: 12,
    marginHorizontal: theme.spacing.marginMobile,
    padding: 14,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    gap: 6,
  },
  semturHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  semturTitle: {
    ...theme.typography.labelMd,
    color: '#334155',
    fontWeight: '700',
  },
  semturDescription: {
    ...theme.typography.bodySm,
    color: '#475569',
    lineHeight: 18,
    fontSize: 12,
  },
  galleryScroller: {
    paddingVertical: 6,
    gap: 12,
  },
  galleryItem: {
    width: 220,
    backgroundColor: theme.colors.surfaceContainerLow,
    borderRadius: theme.radii.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
  },
  galleryImage: {
    width: '100%',
    height: 140,
  },
  galleryCredit: {
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 11,
    padding: 6,
    backgroundColor: theme.colors.surfaceWhite,
  },
  sectionTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandForest,
    marginBottom: 12,
  },
  contactsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  contactChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: theme.colors.surfaceContainerLow,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: theme.radii.lg,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
    minHeight: theme.spacing.touchMin,
  },
  mapChip: {
    backgroundColor: theme.colors.brandForest,
    borderColor: theme.colors.brandForest,
  },
  contactChipText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '600',
  },
  mapChipText: {
    color: theme.colors.surfaceWhite,
  },
  mediaCredit: {
    marginHorizontal: theme.spacing.marginMobile,
    marginTop: 8,
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 12,
  },
});
