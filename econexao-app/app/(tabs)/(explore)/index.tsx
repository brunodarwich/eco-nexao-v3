import React, { useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ImageBackground,
  Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { RegionSelectorModal } from '../../../src/components/common/RegionSelectorModal';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { CompactRouteCard } from '../../../src/components/routes/CompactRouteCard';
import { useApp } from '../../../src/hooks/useApp';
import { useAuth } from '../../../src/hooks/useAuth';
import { useRegionsQuery, useRoutesQuery } from '../../../src/hooks/queries';
import { useOptimisticFavoriteRoute } from '../../../src/hooks/useOptimisticFavoriteRoute';
import { theme } from '../../../src/theme/theme';
import { makeAccessibleButton } from '../../../src/utils/accessibility';

const HERO_FULL_BG = require('../../../assets/images/alter_do_chao_hero.jpg');

export default function HomeScreen() {
  const router = useRouter();
  const { state } = useApp();
  const { user } = useAuth();
  const [isRegionModalOpen, setIsRegionModalOpen] = useState(false);

  const regionsQuery = useRegionsQuery();

  const activeRegionId = state.activeRegionId ?? regionsQuery.data?.[0]?.id;
  const activeRegion = regionsQuery.data?.find((r) => r.id === activeRegionId);
  const hasNoRegions = regionsQuery.isSuccess && !activeRegionId;

  const featuredQuery = useRoutesQuery(activeRegionId, { limit: 10 });
  const savedQuery = useRoutesQuery(activeRegionId, { saved: true }, user?.id);

  const { toggleFavorite } = useOptimisticFavoriteRoute();

  const savedRouteIds = new Set(savedQuery.data?.data.map((r) => r.id));

  return (
    <View style={styles.screenContainer}>
      <AppHeader />

      <ImageBackground
        source={HERO_FULL_BG}
        style={styles.fullScreenBackground}
        imageStyle={styles.fullScreenBackgroundImage}
        resizeMode="cover"
      >
        {/* Scrim Overlay contínuo com escurecimento progressivo para legibilidade AAA */}
        <View style={styles.scrimOverlay} />

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Espaçamento aéreo do céu da Amazônia (conforme referência visual) */}
          <View style={styles.heroTopSpacer} />

          {/* Bloco do Hero */}
          <View style={styles.heroBlock}>
            <View style={styles.heroTextContainer}>
              <Text style={styles.heroTitle}>
                Conecte-se{'\n'}à oferta real{'\n'}da Amazônia.
              </Text>
              <Text style={styles.heroSubtitle}>
                Descubra roteiros autênticos e sustentáveis, guiados por quem vive e preserva a floresta.
              </Text>
            </View>

            <View style={styles.heroControls}>
              {/* Pílula de seleção de região */}
              <TouchableOpacity
                style={styles.regionSelectorPill}
                onPress={() => setIsRegionModalOpen(true)}
                {...makeAccessibleButton(
                  `Região atual: ${activeRegion?.name ?? 'Santarém / Alter do Chão'}`,
                  'Toque para selecionar outra região'
                )}
              >
                <Ionicons name="location-sharp" size={17} color={theme.colors.surfaceWhite} />
                <Text style={styles.regionPillText} numberOfLines={1}>
                  {activeRegion?.name ?? 'Santarém / Alter do Chão'}
                </Text>
                <Ionicons name="chevron-down" size={16} color={theme.colors.surfaceWhite} />
              </TouchableOpacity>

              {/* Botão de ação primário CTA */}
              <TouchableOpacity
                style={styles.ctaButton}
                onPress={() => router.push('/(tabs)/(routes)')}
                {...makeAccessibleButton('Descobrir rotas', 'Navega para o catálogo de rotas')}
              >
                <Text style={styles.ctaButtonText}>Descobrir Rotas</Text>
                <Ionicons name="arrow-forward" size={18} color={theme.colors.onPrimary} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Seção 1: Rotas em Destaque */}
          <View style={styles.carouselSection}>
            <View style={styles.sectionHeaderRow}>
              <Text style={styles.sectionTitleOnImage}>Rotas em Destaque</Text>
              <TouchableOpacity
                onPress={() => router.push('/(tabs)/(routes)')}
                style={styles.seeAllLink}
                {...makeAccessibleButton('Ver todas as rotas em destaque')}
              >
                <Text style={styles.seeAllTextOnImage}>Ver todas</Text>
                <Ionicons name="chevron-forward" size={15} color="rgba(255, 255, 255, 0.85)" />
              </TouchableOpacity>
            </View>

            {regionsQuery.isPending ? (
              <View style={styles.stateWrapper}>
                <LoadingView message="Carregando regiões..." />
              </View>
            ) : regionsQuery.isError ? (
              <View style={styles.stateWrapper}>
                <ErrorStateView
                  message="Não foi possível carregar as regiões disponíveis."
                  onRetry={() => void regionsQuery.refetch()}
                />
              </View>
            ) : hasNoRegions ? (
              <View style={styles.stateWrapper}>
                <EmptyStateView
                  title="Nenhuma região disponível"
                  message="O ambiente ainda não possui regiões cadastradas."
                />
              </View>
            ) : featuredQuery.isPending ? (
              <View style={styles.stateWrapper}>
                <LoadingView message="Carregando rotas em destaque..." />
              </View>
            ) : featuredQuery.isError ? (
              <View style={styles.stateWrapper}>
                <ErrorStateView
                  message="Não foi possível carregar as rotas em destaque."
                  onRetry={() => void featuredQuery.refetch()}
                />
              </View>
            ) : featuredQuery.data?.data.length ? (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.carouselScroll}
              >
                {featuredQuery.data.data.map((route) => {
                  const isFav = savedRouteIds.has(route.id);
                  return (
                    <CompactRouteCard
                      key={route.id}
                      route={route}
                      isFavorite={isFav}
                      onPress={() => router.push(`/route/${route.id}`)}
                      onToggleFavorite={() => toggleFavorite(route.id, isFav)}
                    />
                  );
                })}
              </ScrollView>
            ) : (
              <View style={styles.stateWrapper}>
                <EmptyStateView
                  title="Nenhuma rota em destaque"
                  message="Não há rotas cadastradas para a região selecionada."
                />
              </View>
            )}
          </View>

          {/* Seção 2: Rotas Salvas */}
          <View style={styles.carouselSection}>
            <View style={styles.sectionHeaderRow}>
              <Text style={styles.sectionTitleOnImage}>Rotas Salvas</Text>
              {savedQuery.data?.data?.length ? (
                <TouchableOpacity
                  onPress={() => router.push('/(tabs)/(routes)')}
                  style={styles.seeAllLink}
                  {...makeAccessibleButton('Ver todas as rotas salvas')}
                >
                  <Text style={styles.seeAllTextOnImage}>Ver todas</Text>
                  <Ionicons name="chevron-forward" size={15} color="rgba(255, 255, 255, 0.85)" />
                </TouchableOpacity>
              ) : null}
            </View>

            {regionsQuery.isPending ? (
              <View style={styles.stateWrapper}>
                <LoadingView message="Carregando regiões..." />
              </View>
            ) : regionsQuery.isError ? (
              <View style={styles.stateWrapper}>
                <ErrorStateView
                  message="Não foi possível carregar as regiões disponíveis."
                  onRetry={() => void regionsQuery.refetch()}
                />
              </View>
            ) : hasNoRegions ? (
              <View style={styles.stateWrapper}>
                <EmptyStateView
                  title="Nenhuma região disponível"
                  message="Cadastre uma região para explorar e salvar rotas."
                />
              </View>
            ) : savedQuery.isPending ? (
              <View style={styles.stateWrapper}>
                <LoadingView message="Carregando rotas salvas..." />
              </View>
            ) : savedQuery.isError ? (
              <View style={styles.stateWrapper}>
                <ErrorStateView
                  message="Não foi possível carregar suas rotas salvas."
                  onRetry={() => void savedQuery.refetch()}
                />
              </View>
            ) : savedQuery.data?.data.length ? (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.carouselScroll}
              >
                {savedQuery.data.data.map((route) => (
                  <CompactRouteCard
                    key={route.id}
                    route={route}
                    isFavorite={true}
                    onPress={() => router.push(`/route/${route.id}`)}
                    onToggleFavorite={() => toggleFavorite(route.id, true)}
                  />
                ))}
              </ScrollView>
            ) : (
              <View style={styles.stateWrapper}>
                <EmptyStateView
                  title="Nenhuma rota salva"
                  message="Explore as rotas e toque no marcador para salvar seus destinos preferidos."
                />
              </View>
            )}
          </View>
        </ScrollView>
      </ImageBackground>

      <RegionSelectorModal
        visible={isRegionModalOpen}
        onClose={() => setIsRegionModalOpen(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screenContainer: {
    flex: 1,
    backgroundColor: theme.colors.surfaceBackground,
  },
  fullScreenBackground: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  fullScreenBackgroundImage: {
    width: '100%',
    height: '100%',
  },
  scrimOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(15, 33, 8, 0.48)',
  },
  scrollContent: {
    paddingBottom: 72,
  },
  heroTopSpacer: {
    height: 110,
  },
  heroBlock: {
    paddingHorizontal: theme.spacing.marginMobile,
    gap: 20,
    marginBottom: 36,
  },
  heroTextContainer: {
    gap: 10,
  },
  heroTitle: {
    ...theme.typography.displayLg,
    color: theme.colors.surfaceWhite,
    fontWeight: '800',
    fontSize: 36,
    lineHeight: 42,
    textShadowColor: 'rgba(0, 0, 0, 0.55)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 6,
  },
  heroSubtitle: {
    ...theme.typography.bodyMd,
    color: 'rgba(255, 255, 255, 0.92)',
    fontSize: 15,
    lineHeight: 22,
    maxWidth: '90%',
    textShadowColor: 'rgba(0, 0, 0, 0.45)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  heroControls: {
    gap: 14,
    marginTop: 6,
  },
  regionSelectorPill: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.22)',
    paddingVertical: 9,
    paddingHorizontal: 16,
    borderRadius: theme.radii.full,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.4)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  regionPillText: {
    ...theme.typography.labelSm,
    color: theme.colors.surfaceWhite,
    fontWeight: '600',
    fontSize: 14,
  },
  ctaButton: {
    backgroundColor: theme.colors.brandForest,
    paddingVertical: 15,
    paddingHorizontal: 24,
    borderRadius: theme.radii.full,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 4,
  },
  ctaButtonText: {
    ...theme.typography.titleMd,
    color: theme.colors.onPrimary,
    fontWeight: '700',
    fontSize: 16,
  },
  carouselSection: {
    marginBottom: 32,
    gap: 14,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.marginMobile,
  },
  sectionTitleOnImage: {
    ...theme.typography.headlineMd,
    color: theme.colors.surfaceWhite,
    fontWeight: '700',
    fontSize: 20,
    textShadowColor: 'rgba(0, 0, 0, 0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  seeAllLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  seeAllTextOnImage: {
    ...theme.typography.labelSm,
    color: 'rgba(255, 255, 255, 0.85)',
    fontWeight: '600',
    fontSize: 13,
  },
  carouselScroll: {
    paddingHorizontal: theme.spacing.marginMobile,
    paddingVertical: 4,
  },
  stateWrapper: {
    marginHorizontal: theme.spacing.marginMobile,
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
    borderRadius: theme.radii.xl,
    padding: 16,
  },
});
