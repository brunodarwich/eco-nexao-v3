import React, { useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, TouchableOpacity, Alert, Image, ActivityIndicator, AccessibilityInfo } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';

import { AppHeader } from '../../../src/components/common/AppHeader';
import { AuthModal } from '../../../src/components/profile/AuthModal';
import { EditProfileModal } from '../../../src/components/profile/EditProfileModal';
import { AccountDeletionModal } from '../../../src/components/profile/AccountDeletionModal';
import { apiClient } from '../../../src/api/client';
import { useMyProfileQuery } from '../../../src/hooks/queries';
import { useAuth } from '../../../src/hooks/useAuth';
import { queryKeys } from '../../../src/api/queryKeys';
import { queryClient } from '../../../src/api/queryClient';
import { theme, useAppTheme } from '../../../src/theme/theme';

import { makeAccessibleButton } from '../../../src/utils/accessibility';

export default function ProfileScreen() {
  const router = useRouter();
  const theme = useAppTheme();
  const { user, signOut } = useAuth();
  const profileQuery = useMyProfileQuery(user?.id);
  const profile = profileQuery.data;
  const [isAuthModalVisible, setIsAuthModalVisible] = useState(false);
  const [isEditProfileModalVisible, setIsEditProfileModalVisible] = useState(false);
  const [isAccountDeletionModalVisible, setIsAccountDeletionModalVisible] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const avatarBusyRef = useRef(false);


  const isAnonymous = user?.is_anonymous ?? true;
  const userName = profile?.name || (isAnonymous ? 'Visitante' : 'Usuário ECOnexão');

  const handleAvatarPress = async () => {
    if (avatarBusyRef.current) return;
    avatarBusyRef.current = true;
    setIsUploading(true);
    try {
      AccessibilityInfo.announceForAccessibility('Abrindo seletor de foto do perfil.');
      const picker = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 1,
      });
      if (picker.canceled) return;
      const asset = picker.assets[0];
      await apiClient.uploadAvatar({
        uri: asset.uri,
        name: asset.fileName || 'avatar.jpg',
        type: asset.mimeType || 'image/jpeg',
        file: asset.file,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.myProfile(user?.id) });
      AccessibilityInfo.announceForAccessibility('Foto do perfil atualizada com sucesso.');
      Alert.alert('Foto atualizada', 'Seu avatar foi processado e publicado com segurança.');
    } catch {
      AccessibilityInfo.announceForAccessibility('Não foi possível atualizar a foto do perfil.');
      Alert.alert('Erro no upload', 'Não foi possível atualizar a foto. Tente novamente.');
    } finally {
      avatarBusyRef.current = false;
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
              accessibilityLabel={isUploading ? 'Atualizando foto do perfil' : 'Alterar Foto do Perfil'}
              accessibilityState={{ disabled: isUploading, busy: isUploading }}
            >
              {isUploading ? (
                <ActivityIndicator
                  size="small"
                  color={theme.colors.brandForest}
                  accessibilityLabel="Upload da foto em andamento"
                />
              ) : profile?.avatar?.url ? (
                <Image
                  source={{ uri: profile.avatar.url }}
                  style={styles.avatarImage}
                  accessible={false}
                />
              ) : (
                <Ionicons name="person" size={32} color={theme.colors.brandForest} />
              )}
              <View style={styles.avatarEditBadge}>
                <Ionicons name="camera" size={12} color={theme.colors.surfaceWhite} />
              </View>
            </TouchableOpacity>

            <View style={styles.profileTextInfo}>
              <View style={styles.userNameRow}>
                <Text style={styles.userName}>{userName}</Text>
                <TouchableOpacity
                  onPress={() => setIsEditProfileModalVisible(true)}
                  style={styles.editProfileIconBtn}
                  {...makeAccessibleButton('Editar informações do perfil')}
                >
                  <Ionicons name="pencil" size={16} color={theme.colors.brandForest} />
                </TouchableOpacity>
              </View>
              <Text style={styles.userRole}>
                {isAnonymous ? 'Sessão Convidado' : user?.email ?? 'Conta Autenticada'}
              </Text>
              {profile?.location && (
                <Text style={styles.userLocationText}>
                  <Ionicons name="location-outline" size={12} color={theme.colors.onSurfaceVariant} /> {profile.location}
                </Text>
              )}
            </View>
          </View>
        </View>

        {/* Functional Menu Links (ECO-1102 .. ECO-1108) */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Minha Conta & Preferências</Text>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => router.push('/(tabs)/(profile)/favorite-routes')}
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
            onPress={() => router.push('/(tabs)/(profile)/favorite-actors')}
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
            onPress={() => router.push('/(tabs)/(profile)/trips')}
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
            onPress={() => router.push('/(tabs)/(profile)/accessibility')}
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
            onPress={() => router.push('/(tabs)/(profile)/support')}
            {...makeAccessibleButton('Ajuda & Suporte', 'Acessar documentação e contatos')}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="help-circle-outline" size={20} color={theme.colors.brandForest} />
              <Text style={styles.menuText}>Ajuda & Suporte</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.onSurfaceVariant} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => router.push('/(tabs)/(profile)/legal')}
            {...makeAccessibleButton('Termos & Privacidade LGPD', 'Acessar termos de uso e política de privacidade')}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="shield-checkmark-outline" size={20} color={theme.colors.brandForest} />
              <Text style={styles.menuText}>Termos & Privacidade</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.colors.onSurfaceVariant} />
          </TouchableOpacity>
        </View>

        {/* Account Deletion & Session Action (Sign Out / LGPD) */}
        <View style={styles.footerActionsCard}>
          <TouchableOpacity
            style={styles.signOutButton}
            onPress={() => void signOut()}
            {...makeAccessibleButton('Encerrar sessão', 'Fazer logout da conta atual')}
          >
            <Ionicons name="log-out-outline" size={18} color={theme.colors.brandDeep} />
            <Text style={styles.signOutText}>Encerrar Sessão</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.deleteAccountButton}
            onPress={() => setIsAccountDeletionModalVisible(true)}
            {...makeAccessibleButton('Excluir minha conta', 'Solicitar exclusão de conta conforme a LGPD')}
          >
            <Ionicons name="trash-outline" size={16} color={theme.colors.error} />
            <Text style={styles.deleteAccountText}>Excluir Minha Conta (LGPD)</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Edit Profile Modal */}
      <EditProfileModal
        visible={isEditProfileModalVisible}
        onClose={() => setIsEditProfileModalVisible(false)}
        currentProfile={profile}
        userId={user?.id}
      />

      {/* Account Deletion Modal (LGPD) */}
      <AccountDeletionModal
        visible={isAccountDeletionModalVisible}
        onClose={() => setIsAccountDeletionModalVisible(false)}
      />

      {/* Auth & Account Linking Modal (ADR 0007 / ECO-1902) */}
      <AuthModal
        visible={isAuthModalVisible}
        onClose={() => setIsAuthModalVisible(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surfaceBackground,
  },
  guestBanner: {
    backgroundColor: '#ECFDF5',
    borderColor: '#A7F3D0',
    borderWidth: 1,
    borderRadius: theme.radii.lg,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  guestBannerTextCol: {
    flex: 1,
  },
  guestBannerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  guestBannerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#065F46',
  },
  guestBannerBody: {
    fontSize: 12,
    color: '#047857',
    lineHeight: 16,
  },
  guestBannerButton: {
    backgroundColor: '#059669',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: theme.radii.md,
    alignItems: 'center',
  },
  guestBannerButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
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
  avatarImage: {
    width: '100%',
    height: '100%',
    borderRadius: 28,
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
  userNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },

  userName: {
    ...theme.typography.headlineSm,
    color: theme.colors.brandDeep,
  },
  editProfileIconBtn: {
    padding: 4,
    borderRadius: 6,
    backgroundColor: 'rgba(51, 96, 30, 0.08)',
  },
  userLocationText: {
    ...theme.typography.labelSm,
    color: theme.colors.onSurfaceVariant,
    marginBottom: 4,
  },
  userRole: {
    ...theme.typography.bodySm,
    color: theme.colors.onSurfaceVariant,
    marginBottom: 4,
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
  footerActionsCard: {
    gap: 10,
    marginTop: 4,
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: theme.colors.surfaceContainerLow,
    padding: 14,
    borderRadius: theme.radii.xl,
    borderWidth: 1,
    borderColor: 'rgba(117, 155, 113, 0.2)',
  },
  signOutText: {
    ...theme.typography.labelSm,
    color: theme.colors.brandDeep,
    fontWeight: '700',
  },
  deleteAccountButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: 12,
    borderRadius: theme.radii.xl,
    backgroundColor: 'rgba(186, 26, 26, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(186, 26, 26, 0.15)',
  },
  deleteAccountText: {
    ...theme.typography.labelSm,
    color: theme.colors.error,
    fontWeight: '600',
    fontSize: 12,
  },

});
