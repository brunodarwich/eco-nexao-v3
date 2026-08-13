import React from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import type { ActorCategory } from '../../api/types';
import { FilterChip } from '../common/FilterChip';
import { Ionicons } from '@expo/vector-icons';

interface CategoryFiltersProps {
  categories: ActorCategory[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
}

export const CategoryFilters: React.FC<CategoryFiltersProps> = ({
  selectedCategory,
  onSelectCategory,
  categories,
}) => {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      <FilterChip
        label="Tudo"
        isSelected={!selectedCategory}
        onPress={() => onSelectCategory('')}
        icon="apps-outline"
      />
      {categories.map((cat) => (
        <FilterChip
          key={cat.slug}
          label={cat.label}
          isSelected={selectedCategory === cat.slug}
          onPress={() => onSelectCategory(cat.slug)}
          icon={(cat.icon || 'leaf-outline') as keyof typeof Ionicons.glyphMap}
        />
      ))}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    alignItems: 'center',
  },
});
