import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { useAppTheme } from '../../../src/theme/theme';
import { makeAccessibleHeader } from '../../../src/utils/accessibility';

export default function LegalAndPrivacyScreen() {
  const router = useRouter();
  const theme = useAppTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surfaceBackground }]}>
      <AppHeader showBack onBackPress={() => router.back()} title="Termos & Privacidade" />

      <ScrollView contentContainerStyle={styles.content}>
        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <Text
            {...makeAccessibleHeader('Termos de Uso Comunitário', 2)}
            style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
          >
            Termos de Uso Comunitário
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            O ECOnexão é uma plataforma comunitária aberta destinada a promover o ecoturismo sustentável, a valorização dos negócios locais e a preservação ambiental no polo turístico Tapajós-Arapiuns (Belterra, Santarém e região).
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            Todas as rotas, trilhas e pontos de interesse listados são mantidos colaborativamente com a curadoria editorial da SEMTUR e lideranças locais. O usuário compromete-se a respeitar as diretrizes de não deixar rastros, conservação da fauna e flora e valorização das comunidades tradicionais.
          </Text>
        </View>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <Text
            {...makeAccessibleHeader('Política de Privacidade e LGPD', 2)}
            style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
          >
            Privacidade e LGPD
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            O ECOnexão respeita integralmente a Lei Geral de Proteção de Dados (Lei nº 13.709/2018 - LGPD).
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            • **Navegação Anônima:** Você pode utilizar o aplicativo sem fornecer e-mail ou dados pessoais.
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            • **Coleta Mínima:** Apenas armazenamos suas preferências de acessibilidade e lista de favoritos para personalizar sua experiência.
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            • **Direito à Exclusão:** Você pode solicitar a exclusão de sua conta a qualquer momento diretamente pelo seu perfil, resultando na imediata desvinculação dos seus dados pessoais.
          </Text>
        </View>

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.colors.surfaceWhite,
              borderColor: theme.isHighContrast ? theme.colors.brandForest : 'rgba(117, 155, 113, 0.15)',
              borderWidth: theme.isHighContrast ? 2 : 1,
            },
          ]}
        >
          <Text
            {...makeAccessibleHeader('Licenças e Fontes Abertas', 2)}
            style={[styles.sectionTitle, theme.typography.headlineSm, { color: theme.colors.brandForest }]}
          >
            Licenças e Fontes
          </Text>
          <Text style={[styles.paragraph, theme.typography.bodySm, { color: theme.colors.onSurfaceVariant }]}>
            Mapas e dados geoespaciais são fornecidos sob a licença OpenStreetMap / ODbL e fotos comunitárias são atribuídas conforme a política editorial estabelecida no ADR 0008.
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
  card: {
    padding: 18,
    borderRadius: 16,
  },
  sectionTitle: {
    fontWeight: '700',
    marginBottom: 10,
  },
  paragraph: {
    lineHeight: 20,
    marginBottom: 8,
  },
});
