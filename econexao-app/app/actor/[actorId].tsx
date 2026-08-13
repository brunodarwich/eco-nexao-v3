import React, { useState } from 'react';
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
import { useActorDetailQuery } from '../../src/hooks/queries';
import { useOptimisticFavoriteActor } from '../../src/hooks/useOptimisticFavoriteActor';
import { theme } from '../../src/theme/theme';
import { makeAccessibleButton } from '../../src/utils/accessibility';

export default function ActorDetailScreen() {
  const router = useRouter();
  const { actorId = '', originId } = useLocalSearchParams<{
    actorId: string;
    originId?: string;
  }>();

  const actorQuery = useActorDetailQuery(actorId);
  const { toggleFavorite, isPending: isFavPending } = useOptimisticFavoriteActor();
  const [isFavorite, setIsFavorite] = useState(false);

  const actor = actorQuery.data;

  const handleToggleFav = () => {
    const nextState = !isFavorite;
    setIsFavorite(nextState);
    toggleFavorite(actorId, isFavorite);
  };

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
  const categoryLabel = actor.category?.label || actor.sub_category || 'Atração Local';

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title={actor.name} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Cover / Image Banner */}
        <View style={styles.bannerContainer}>
          <Image
            source={require('../../assets/images/pousada_canto_floresta.jpg')}
            style={styles.bannerImage}
            resizeMode="cover"
          />
          <View style={styles.bannerOverlay}>
            <View style={styles.badgeRow}>
              {greenSeal && <Badge type="greenSeal" label="Selo Verde Consciente" />}
              {actor.verification_status === 'verified' && (
                <Badge type="verified" label="Verificado SEMTUR" />
              )}
            </View>

            <TouchableOpacity
              style={styles.favFloatingButton}
              onPress={handleToggleFav}
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
          </View>
        </View>

        {/* Main Info */}
        <View style={styles.cardSection}>
          <Text style={styles.categoryTag}>{categoryLabel.toUpperCase()}</Text>
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
                {...makeAccessibleButton('Ver no mapa externo')}
              >
                <Ionicons name="map-outline" size={18} color={theme.colors.surfaceWhite} />
                <Text style={[styles.contactChipText, styles.mapChipText]} numberOfLines={1}>
                  Abrir no Mapa
                </Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Provenance / Source Footer */}
        <View style={styles.provenanceBox}>
          <Ionicons name="information-circle-outline" size={16} color={theme.colors.brandForest} />
          <Text style={styles.provenanceText}>
            Dados integrados do Inventário SEMTUR Belterra e enriquecidos via Google Places.
          </Text>
        </View>
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
  categoryTag: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
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
  provenanceBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginHorizontal: theme.spacing.marginMobile,
    marginTop: 16,
    padding: 12,
    backgroundColor: 'rgba(117, 155, 113, 0.08)',
    borderRadius: theme.radii.lg,
  },
  provenanceText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    flex: 1,
    fontSize: 12,
  },
});
