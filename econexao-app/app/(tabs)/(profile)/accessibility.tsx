import React from 'react';
import { ScrollView, StyleSheet, Text, View, Switch, TouchableOpacity, Alert } from 'react-native';
import { useRouter } from 'expo-router';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { useMyPreferencesQuery } from '../../../src/hooks/queries';
import { useAuth } from '../../../src/hooks/useAuth';
import { useAppTheme } from '../../../src/theme/theme';
import { useOptimisticPreferences } from '../../../src/hooks/useOptimisticPreferences';
import { makeAccessibleButton, makeAccessibleHeader } from '../../../src/utils/accessibility';

const TEXT_SCALE_OPTIONS = [
  { label: 'Pequeno', value: 0.9 },
  { label: 'Padrão', value: 1.0 },
  { label: 'Grande', value: 1.15 },
  { label: 'Extra', value: 1.3 },
];

export default function AccessibilityPreferencesScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const theme = useAppTheme();
  const prefsQuery = useMyPreferencesQuery(user?.id);
  const mutatePreferences = useOptimisticPreferences();

  const highContrast = theme.isHighContrast;
  const screenReaderMode = theme.screenReaderMode;
  const textScale = theme.textScale;

  const handleToggleHighContrast = (val: boolean) => {
    mutatePreferences.mutate(
      { high_contrast: val },
      {
        onError: () => {
          Alert.alert('Erro', 'Não foi possível salvar o ajuste de alto contraste.');
        },
      }
    );
  };

  const handleToggleScreenReaderMode = (val: boolean) => {
    mutatePreferences.mutate(
      { screen_reader_mode: val },
      {
        onError: () => {
          Alert.alert('Erro', 'Não foi possível salvar o ajuste do modo leitor.');
        },
      }
    );
  };

  const handleSelectTextScale = (scale: number) => {
    mutatePreferences.mutate(
      { text_scale: scale },
      {
        onError: () => {
          Alert.alert('Erro', 'Não foi possível salvar a escala de texto.');
        },
      }
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surfaceBackground }]}>
      <AppHeader showBack onBackPress={() => router.back()} title="Acessibilidade" />

      <ScrollView contentContainerStyle={styles.content}>
        <Text
          {...makeAccessibleHeader('Opções de Visualização e Leitura', 2)}
          style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
        >
          Opções de Visualização e Leitura
        </Text>

        {/* Alto Contraste */}
        <View
          style={[
            styles.optionCard,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <View style={styles.optionTextRow}>
            <Text
              style={[
                styles.optionTitle,
                theme.typography.titleMd,
                { color: theme.colors.brandDeep, fontWeight: '700' },
              ]}
            >
              Alto Contraste
            </Text>
            <Text style={[styles.optionDescription, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
              Aumenta a relação de contraste visual dos elementos, textos e bordas para facilitar a leitura.
            </Text>
          </View>
          <Switch
            value={highContrast}
            onValueChange={handleToggleHighContrast}
            accessibilityRole="switch"
            accessibilityLabel="Alternar Alto Contraste"
            accessibilityHint="Ativa bordas reforçadas e cores de alto contraste em todo o aplicativo"
            accessibilityState={{ checked: highContrast }}
            trackColor={{ false: theme.colors.surfaceDim, true: theme.colors.brandForest }}
            thumbColor={theme.colors.surfaceWhite}
          />
        </View>

        {/* Modo Leitor de Tela */}
        <View
          style={[
            styles.optionCard,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <View style={styles.optionTextRow}>
            <Text
              style={[
                styles.optionTitle,
                theme.typography.titleMd,
                { color: theme.colors.brandDeep, fontWeight: '700' },
              ]}
            >
              Modo Leitor de Tela
            </Text>
            <Text style={[styles.optionDescription, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
              Ativa anúncios verbosos e otimiza a ordem de foco para navegação por leitores de tela (TalkBack / VoiceOver).
            </Text>
          </View>
          <Switch
            value={screenReaderMode}
            onValueChange={handleToggleScreenReaderMode}
            accessibilityRole="switch"
            accessibilityLabel="Alternar Modo Leitor de Tela"
            accessibilityHint="Prioriza semântica acessível estrita e anúncios sonoros em ações no app"
            accessibilityState={{ checked: screenReaderMode }}
            trackColor={{ false: theme.colors.surfaceDim, true: theme.colors.brandForest }}
            thumbColor={theme.colors.surfaceWhite}
          />
        </View>

        {/* Escala de Texto */}
        <View
          style={[
            styles.scaleCard,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <Text
            style={[
              styles.optionTitle,
              theme.typography.titleMd,
              { color: theme.colors.brandDeep, fontWeight: '700' },
            ]}
          >
            Tamanho do Texto
          </Text>
          <Text
            style={[
              styles.optionDescription,
              theme.typography.bodySm,
              { color: theme.colors.onSurfaceVariant, marginBottom: 12 },
            ]}
          >
            Ajuste a escala tipográfica para adaptar o tamanho dos textos às suas necessidades visuais.
          </Text>

          <View style={styles.scaleButtonsRow}>
            {TEXT_SCALE_OPTIONS.map((opt) => {
              const isSelected = Math.abs(textScale - opt.value) < 0.05;
              return (
                <TouchableOpacity
                  key={opt.value}
                  {...makeAccessibleButton(
                    `Tamanho de texto ${opt.label}`,
                    `Aplica escala de ${Math.round(opt.value * 100)}% nas fontes do aplicativo`
                  )}
                  style={[
                    styles.scaleButton,
                    {
                      backgroundColor: isSelected ? theme.colors.brandForest : theme.colors.surfaceContainerLow,
                      borderColor: theme.isHighContrast
                        ? theme.colors.brandDeep
                        : isSelected
                        ? theme.colors.brandForest
                        : 'transparent',
                    },
                  ]}
                  onPress={() => handleSelectTextScale(opt.value)}
                >
                  <Text
                    style={[
                      styles.scaleButtonText,
                      {
                        color: isSelected ? theme.colors.surfaceWhite : theme.colors.brandDeep,
                        fontWeight: isSelected ? '700' : '500',
                      },
                    ]}
                  >
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View
          style={[
            styles.infoBox,
            {
              backgroundColor: theme.isHighContrast ? 'rgba(26, 77, 10, 0.12)' : 'rgba(117, 155, 113, 0.1)',
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'transparent',
              borderWidth: theme.isHighContrast ? 1 : 0,
            },
          ]}
        >
          <Text style={[styles.infoText, theme.typography.labelSm, { color: theme.colors.brandForest }]}>
            Suas preferências são aplicadas instantaneamente e sincronizadas com a sua conta no ECOnexão.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  sectionTitle: {
    marginBottom: 4,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 16,
  },
  scaleCard: {
    padding: 16,
    borderRadius: 16,
  },
  scaleButtonsRow: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'space-between',
  },
  scaleButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    borderWidth: 1,
  },
  scaleButtonText: {
    fontSize: 13,
  },
  optionTextRow: {
    flex: 1,
    paddingRight: 12,
  },
  optionTitle: {
    marginBottom: 4,
  },
  optionDescription: {
    lineHeight: 18,
  },
  infoBox: {
    padding: 12,
    borderRadius: 12,
  },
  infoText: {
    lineHeight: 18,
  },
});
