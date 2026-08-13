import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, TouchableOpacity, Modal, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { AppHeader } from '../../src/components/common/AppHeader';
import { Badge } from '../../src/components/common/Badge';
import { LoadingView } from '../../src/components/common/UIStateViews';
import { apiClient } from '../../src/api/client';
import { useMyImpactQuery, useMyProfileQuery } from '../../src/hooks/queries';
import { useAuth } from '../../src/hooks/useAuth';
import { theme } from '../../src/theme/theme';
import { makeAccessibleButton } from '../../src/utils/accessibility';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const profileQuery = useMyProfileQuery(user?.id);
  const impactQuery = useMyImpactQuery(user?.id);

  const profile = profileQuery.data;
  const impact = impactQuery.data;

  const [isSealModalVisible, setIsSealModalVisible] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const isAnonymous = user?.is_anonymous ?? true;
  const userName = profile?.name || (isAnonymous ? 'Visitante Consciente' : 'Usuário ECOnexão');

  const handleAvatarPress = async () => {
    try {
      setIsUploading(true);
      const res = await apiClient.createAvatarUploadUrl({
        filename: 'avatar.jpg',
        mime_type: 'image/jpeg',
      });
      Alert.alert(
        'Upload de Avatar',
        `URL assinada gerada com sucesso (${res.data.expires_in}s). Seleção de arquivo iniciada.`
      );
    } catch {
      Alert.alert('Erro no Upload', 'Não foi possível solicitar a URL para upload do avatar.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <View style={styles.container}>
      <AppHeader title="Meu Perfil" />

      <ScrollView contentContainerStyle={styles.content}>
        {/* Profile Info Header (ECO-1101) */}
        <View style={styles.profileHeaderCard}>
          <View style={styles.avatarRow}>
            <TouchableOpacity
              style={styles.avatarContainer}
              onPress={handleAvatarPress}
              disabled={isUploading}
              {...makeAccessibleButton('Alterar Foto do Perfil', 'Toque para selecionar uma foto')}
            >
              <Ionicons name="person" size={32} color={theme.colors.brandForest} />
              <View style={styles.avatarEditBadge}>
                <Ionicons name="camera" size={12} color={theme.colors.surfaceWhite} />
              </View>
            </TouchableOpacity>

            <View style={styles.profileTextInfo}>
              <Text style={styles.userName}>{userName}</Text>
              <Text style={styles.userRole}>
                {isAnonymous ? 'Sessão Convidado' : user?.email ?? 'Conta Autenticada'}
              </Text>
              
              <TouchableOpacity
                onPress={() => setIsSealModalVisible(true)}
                style={styles.badgeRow}
                {...makeAccessibleButton('Selo Consciente', 'Toque para ver a verificação do selo')}
              >
                <Badge type="greenSeal" label="Selo Consciente" />
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Impact Metrics (ECO-1101) */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Meu Impacto Ecológico</Text>

          {impactQuery.isPending ? (
            <LoadingView message="Carregando indicadores..." />
          ) : (
            <View style={styles.impactGrid}>
              <TouchableOpacity
                style={styles.impactItem}
                onPress={() => router.push('/profile/trips')}
                {...makeAccessibleButton('Viagens Registradas', 'Ver histórico completo de viagens')}
              >
                <Ionicons name="footsteps" size={22} color={theme.colors.brandForest} />
                <Text style={styles.impactNumber}>
                  {impact?.completed_trips_count ?? impact?.total_trips_count ?? 0}
                </Text>
                <Text style={styles.impactLabel}>Viagens Registradas</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.impactItem}
                onPress={() => router.push('/profile/trips')}
                {...makeAccessibleButton('CO2 Evitado', 'Ver estimativa de CO2 evitado')}
              >
                <Ionicons name="leaf" size={22} color={theme.colors.brandForest} />
                <Text style={styles.impactNumber}>{impact?.co2_saved_kg ?? 0} kg</Text>
                <Text style={styles.impactLabel}>CO₂ Evitado Est.</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.impactItem}
                onPress={() => router.push('/profile/favorite-actors')}
                {...makeAccessibleButton('Atores Visitados', 'Ver atores visitados e favoritos')}
              >
                <Ionicons name="business" size={22} color={theme.colors.brandForest} />
                <Text style={styles.impactNumber}>{impact?.visited_actors_count ?? 0}</Text>
                <Text style={styles.impactLabel}>Atores Visitados</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Functional Menu Links (ECO-1102 .. ECO-1108) */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Minha Conta & Preferências</Text>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => router.push('/profile/favorite-routes')}
            {...makeAccessibleButton('Rotas Salvas', 'Visualizar suas rotas favoritadas')}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="bookmark-outline" size={20} color={theme.colors.brandForest} />
              <Text style={styles.menuText}>Rotas Salvas</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.onSurfaceVariant} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => router.push('/profile/favorite-actors')}
            {...makeAccessibleButton('Atores Favoritos', 'Visualizar estabelecimentos salvos')}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="heart-outline" size={20} color={theme.colors.brandForest} />
              <Text style={styles.menuText}>Atores Favoritos</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.onSurfaceVariant} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => router.push('/profile/trips')}
            {...makeAccessibleButton('Histórico de Viagens', 'Ver passeios e trajetos realizados')}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="compass-outline" size={20} color={theme.colors.brandForest} />
              <Text style={styles.menuText}>Histórico de Viagens</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.onSurfaceVariant} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => router.push('/profile/accessibility')}
            {...makeAccessibleButton('Acessibilidade', 'Ajustar opções visuais e de contraste')}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="accessibility-outline" size={20} color={theme.colors.brandForest} />
              <Text style={styles.menuText}>Acessibilidade</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.onSurfaceVariant} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => router.push('/profile/support')}
            {...makeAccessibleButton('Ajuda & Suporte', 'Acessar documentação e contatos')}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="help-circle-outline" size={20} color={theme.colors.brandForest} />
              <Text style={styles.menuText}>Ajuda & Suporte</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.onSurfaceVariant} />
          </TouchableOpacity>
        </View>

        {/* Session Action (Sign Out) */}
        <TouchableOpacity
          style={styles.signOutButton}
          onPress={() => void signOut()}
          {...makeAccessibleButton('Encerrar sessão', 'Fazer logout da conta atual')}
        >
          <Ionicons name="log-out-outline" size={20} color={theme.colors.error} />
          <Text style={styles.signOutText}>Encerrar Sessão</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Selo Consciente Explanation Modal */}
      <Modal
        visible={isSealModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setIsSealModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Ionicons name="leaf" size={28} color={theme.colors.brandForest} />
              <Text style={styles.modalTitle}>Selo Verde Consciente</Text>
            </View>
            <Text style={styles.modalBody}>
              O Selo Verde é um reconhecimento concedido pela SEMTUR Belterra aos usuários e parceiros que praticam o turismo sustentável, valorizando os negócios locais e promovendo a conservação ecológica da região Tapajós-Arapiuns.
            </Text>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setIsSealModalVisible(false)}
              {...makeAccessibleButton('Fechar modal do Selo Consciente')}
            >
              <Text style={styles.modalCloseText}>Entendido</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
    paddingBottom: 32,
    gap: 16,
  },
  profileHeaderCard: {
    backgroundColor: theme.colors.surfaceWhite,
    padding: theme.spacing.marginMobile,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
    ...theme.shadows.card,
  },
  avatarRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  avatarContainer: {
    width: 64,
    height: 64,
    borderRadius: theme.radii.full,
    backgroundColor: 'rgba(117, 155, 113, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  avatarEditBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 20,
    height: 20,
    borderRadius: theme.radii.full,
    backgroundColor: theme.colors.brandForest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileTextInfo: {
    flex: 1,
  },
  userName: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
  },
  userRole: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    marginBottom: 6,
  },
  badgeRow: {
    flexDirection: 'row',
    alignSelf: 'flex-start',
  },
  sectionCard: {
    backgroundColor: theme.colors.surfaceWhite,
    padding: theme.spacing.marginMobile,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.15)',
    gap: 10,
    ...theme.shadows.card,
  },
  sectionTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandForest,
    marginBottom: 4,
  },
  impactGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  impactItem: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: theme.colors.surfaceContainerLow,
    padding: 12,
    borderRadius: theme.radii.lg,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.12)',
  },
  impactNumber: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
    marginTop: 4,
    fontWeight: '700',
  },
  impactLabel: {
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
    fontSize: 10,
    textAlign: 'center',
    marginTop: 2,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(117, 155, 113, 0.1)',
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  menuText: {
    ...theme.typography.bodyMd,
    color: theme.colors.brandDeep,
    fontWeight: '500',
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: 'rgba(186, 26, 26, 0.08)',
    padding: 14,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: 'rgba(186, 26, 26, 0.2)',
  },
  signOutText: {
    ...theme.typography.labelSm,
    color: theme.colors.error,
    fontWeight: '700',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  modalCard: {
    backgroundColor: theme.colors.surfaceWhite,
    padding: 24,
    borderRadius: theme.radii.xl,
    gap: 16,
    maxWidth: 360,
    width: '100%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  modalTitle: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandForest,
  },
  modalBody: {
    ...theme.typography.bodyMd,
    color: theme.colors.onSurface,
    lineHeight: 22,
  },
  modalCloseButton: {
    backgroundColor: theme.colors.brandForest,
    paddingVertical: 12,
    borderRadius: theme.radii.lg,
    alignItems: 'center',
  },
  modalCloseText: {
    ...theme.typography.labelSm,
    color: theme.colors.surfaceWhite,
    fontWeight: '700',
  },
});
