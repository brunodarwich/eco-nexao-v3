import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useActorCategoriesQuery, useRouteActorsQuery } from '../../hooks/queries';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';
import { ActorCard } from '../catalog/ActorCard';
import { CategoryFilters } from '../catalog/CategoryFilters';
import { ErrorStateView, LoadingView } from '../common/UIStateViews';

interface LocalCatalogPreviewProps {
  routeId: string;
  originId?: string;
  onOpenActor: (actorId: string) => void;
  onOpenCatalog: (category?: string) => void;
}

export const LocalCatalogPreview: React.FC<LocalCatalogPreviewProps> = ({
  routeId,
  originId,
  onOpenActor,
  onOpenCatalog,
}) => {
  const [selectedCategory, setSelectedCategory] = useState('');
  const categories = useActorCategoriesQuery();
  const actors = useRouteActorsQuery(routeId, {
    origin_id: originId,
    category: selectedCategory || undefined,
    limit: 3,
  });

  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text style={styles.title} accessibilityRole="header">Catálogo Local</Text>
        {!actors.isPending && !actors.isError && (
          <Text style={styles.totalText}>
            {actors.data?.meta?.total ?? 0} {(actors.data?.meta?.total ?? 0) === 1 ? 'ator' : 'atores'}
          </Text>
        )}
      </View>

      {categories.data && categories.data.length > 0 && (
        <View style={styles.filtersWrapper}>
          <CategoryFilters
            categories={categories.data}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
          />
        </View>
      )}

      {actors.isPending ? (
        <LoadingView message="Carregando catálogo local..." />
      ) : actors.isError ? (
        <ErrorStateView
          message="Não foi possível carregar o catálogo local."
          onRetry={() => void actors.refetch()}
        />
      ) : actors.data?.data.length ? (
        <View style={styles.cards}>
          {actors.data.data.map((actor) => (
            <ActorCard
              key={actor.id}
              actor={actor}
              variant="compact"
              onPress={() => onOpenActor(actor.id)}
            />
          ))}
        </View>
      ) : (
        <View style={styles.emptyCard}>
          <Ionicons name="storefront-outline" size={22} color={theme.colors.brandSage} />
          <Text style={styles.emptyText}>
            Nenhum ator encontrado{selectedCategory ? ' nesta categoria' : ' nesta origem'}.
          </Text>
        </View>
      )}

      <TouchableOpacity
        style={styles.catalogButton}
        onPress={() => onOpenCatalog(selectedCategory || undefined)}
        {...makeAccessibleButton(
          'Ver catálogo completo',
          'Abre todos os atores desta rota preservando a origem e o filtro selecionado.'
        )}
      >
        <Text style={styles.catalogButtonText}>Ver catálogo completo</Text>
        <Ionicons name="arrow-forward" size={18} color={theme.colors.brandForest} />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  section: { gap: 10, width: '100%', maxWidth: '100%' },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: 12,
  },
  title: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
  },
  totalText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
  },
  filtersWrapper: {
    width: '100%',
    maxWidth: '100%',
    overflow: 'hidden',
  },
  cards: { gap: 10 },
  emptyCard: {
    minHeight: 88,
    backgroundColor: theme.colors.surfaceContainerLow,
    borderRadius: theme.radii.lg,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
  },
  emptyText: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    textAlign: 'center',
  },
  catalogButton: {
    minHeight: 52,
    borderRadius: theme.radii.lg,
    backgroundColor: theme.colors.surfaceWhite,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
  },
  catalogButtonText: {
    ...theme.typography.labelMd,
    color: theme.colors.brandForest,
    fontWeight: '700',
  },
});
