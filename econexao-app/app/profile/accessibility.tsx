import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, Switch, TouchableOpacity, Alert } from 'react-native';
import { useRouter } from 'expo-router';

import { AppHeader } from '../../src/components/common/AppHeader';
import { apiClient } from '../../src/api/client';
import { useMyPreferencesQuery } from '../../src/hooks/queries';
import { useAuth } from '../../src/hooks/useAuth';
import { theme } from '../../src/theme/theme';
import { makeAccessibleButton } from '../../src/utils/accessibility';

export default function AccessibilityPreferencesScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const prefsQuery = useMyPreferencesQuery(user?.id);

  const prefs = prefsQuery.data;

  const [highContrast, setHighContrast] = useState(prefs?.high_contrast ?? false);
  const [readerMode, setReaderMode] = useState(prefs?.screen_reader_mode ?? false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async (updated: { high_contrast?: boolean; reader_mode?: boolean }) => {
    try {
      setIsSaving(true);
      await apiClient.updateMyPreferences(updated);
      await prefsQuery.refetch();
    } catch {
      Alert.alert('Erro', 'Não foi possível atualizar suas preferências de acessibilidade.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title="Acessibilidade" />

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>Opções de Visualização e Leitura</Text>

        <View style={styles.optionCard}>
          <View style={styles.optionTextRow}>
            <Text style={styles.optionTitle}>Alto Contraste</Text>
            <Text style={styles.optionDescription}>
              Aumenta a relação de contraste visual dos elementos e textos para melhorar a legibilidade.
            </Text>
          </View>
          <Switch
            value={highContrast}
            onValueChange={(val) => {
              setHighContrast(val);
              void handleSave({ high_contrast: val });
            }}
            disabled={isSaving}
          />
        </View>

        <View style={styles.optionCard}>
          <View style={styles.optionTextRow}>
            <Text style={styles.optionTitle}>Modo Leitor / Leitor de Tela</Text>
            <Text style={styles.optionDescription}>
              Otimiza leiautes para navegação assistiva e leitores de tela nativos.
            </Text>
          </View>
          <Switch
            value={readerMode}
            onValueChange={(val) => {
              setReaderMode(val);
              void handleSave({ reader_mode: val });
            }}
            disabled={isSaving}
          />
        </View>

        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            Suas preferências são aplicadas instantaneamente e salvas no seu perfil do ECOnexão.
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
  content: {
    padding: theme.spacing.marginMobile,
    gap: 16,
  },
  sectionTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandForest,
    marginBottom: 4,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: theme.colors.surfaceWhite,
    padding: theme.spacing.marginMobile,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
    ...theme.shadows.card,
  },
  optionTextRow: {
    flex: 1,
    paddingRight: 12,
  },
  optionTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    marginBottom: 4,
  },
  optionDescription: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 18,
  },
  infoBox: {
    backgroundColor: 'rgba(117, 155, 113, 0.1)',
    padding: 12,
    borderRadius: theme.radii.lg,
  },
  infoText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
  },
});
