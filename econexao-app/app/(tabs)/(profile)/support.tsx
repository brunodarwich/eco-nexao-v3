import React from 'react';
import { ScrollView, StyleSheet, Text, View, TouchableOpacity, Linking, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { EmptyStateView, ErrorStateView, LoadingView } from '../../../src/components/common/UIStateViews';
import { useSupportContentQuery } from '../../../src/hooks/queries';
import { theme } from '../../../src/theme/theme';
import { makeAccessibleButton } from '../../../src/utils/accessibility';

export default function SupportScreen() {
  const router = useRouter();
  const supportQuery = useSupportContentQuery();

  const handleOpenUrl = async (url?: string, title?: string) => {
    if (!url) return;
    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
      } else {
        Alert.alert('Link Indisponível', `Não foi possível abrir ${title || 'o link'}.`);
      }
    } catch {
      Alert.alert('Erro', `Falha ao tentar acessar ${title || 'o recurso'}.`);
    }
  };

  const support = supportQuery.data;
  const contacts = support?.contacts;
  const helpLinks = support?.help_links ?? [];
  const faqList = support?.faq ?? [];

  return (
    <View style={styles.container}>
      <AppHeader showBack onBackPress={() => router.back()} title="Ajuda e Suporte" />

      <ScrollView contentContainerStyle={styles.content}>
        {supportQuery.isPending ? (
          <LoadingView message="Carregando dados de suporte..." />
        ) : supportQuery.isError ? (
          <ErrorStateView
            title="Erro ao carregar suporte"
            message="Não foi possível obter os contatos de suporte no momento."
            onRetry={() => void supportQuery.refetch()}
          />
        ) : (
          <>
            {/* Contacts Section */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Canais Oficiais de Atendimento</Text>
              <Text style={styles.cardDescription}>
                Entre em contato com nossa equipe editorial para sugestões, correções ou suporte ao aplicativo.
              </Text>

              {contacts?.email && (
                <TouchableOpacity
                  style={styles.actionChip}
                  onPress={() => handleOpenUrl(`mailto:${contacts.email}`, 'E-mail de Suporte')}
                  {...makeAccessibleButton('Enviar e-mail para o suporte', contacts.email)}
                >
                  <Ionicons name="mail-outline" size={20} color={theme.colors.brandForest} />
                  <Text style={styles.chipText}>{contacts.email}</Text>
                </TouchableOpacity>
              )}

              {contacts?.phone && (
                <TouchableOpacity
                  style={styles.actionChip}
                  onPress={() => handleOpenUrl(`tel:${contacts.phone.replace(/[^\d+]/g, '')}`, 'Telefone')}
                  {...makeAccessibleButton('Ligar para atendimento', contacts.phone)}
                >
                  <Ionicons name="call-outline" size={20} color={theme.colors.brandForest} />
                  <Text style={styles.chipText}>{contacts.phone}</Text>
                </TouchableOpacity>
              )}

              {contacts?.operating_hours && (
                <View style={styles.infoBox}>
                  <Ionicons name="time-outline" size={16} color={theme.colors.brandForest} />
                  <Text style={styles.infoText}>{contacts.operating_hours}</Text>
                </View>
              )}
            </View>

            {/* Help Links & Documentation Section */}
            {helpLinks.length > 0 && (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Links e Documentos</Text>
                {helpLinks.map((link, idx) => (
                  <TouchableOpacity
                    key={idx}
                    style={styles.actionChip}
                    onPress={() => handleOpenUrl(link.url, link.title)}
                    {...makeAccessibleButton(`Abrir ${link.title}`)}
                  >
                    <Ionicons name="document-text-outline" size={20} color={theme.colors.brandForest} />
                    <Text style={styles.chipText}>{link.title}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* FAQ Section */}
            {faqList.length > 0 && (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Perguntas Frequentes (FAQ)</Text>
                {faqList.map((item) => (
                  <View key={item.id} style={styles.faqItem}>
                    <Text style={styles.faqQuestion}>{item.question}</Text>
                    <Text style={styles.faqAnswer}>{item.answer}</Text>
                  </View>
                ))}
              </View>
            )}
          </>
        )}
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
  card: {
    backgroundColor: theme.colors.surfaceWhite,
    padding: theme.spacing.marginMobile,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
    gap: 12,
    ...theme.shadows.card,
  },
  cardTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandForest,
  },
  cardDescription: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 20,
  },
  actionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: theme.colors.surfaceContainerLow,
    padding: 12,
    borderRadius: theme.radii.lg,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
  },
  chipText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontWeight: '600',
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(117, 155, 113, 0.1)',
    padding: 10,
    borderRadius: theme.radii.lg,
    marginTop: 4,
  },
  infoText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandForest,
    flex: 1,
  },
  faqItem: {
    backgroundColor: theme.colors.surfaceContainerLow,
    padding: 12,
    borderRadius: theme.radii.lg,
    gap: 4,
  },
  faqQuestion: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    fontSize: 14,
  },
  faqAnswer: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 13,
    lineHeight: 18,
  },
});
