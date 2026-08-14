import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, AccessibilityInfo } from 'react-native';
import { onlineManager, useQueryClient } from '@tanstack/react-query';
import { getNetworkStateAsync, useNetworkState } from 'expo-network';
import { useAppTheme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';

export interface NetworkStatusBarProps {
  isOfflineOverride?: boolean;
  onReconnect?: () => void;
}

export const NetworkStatusBar: React.FC<NetworkStatusBarProps> = ({
  isOfflineOverride,
  onReconnect,
}) => {
  const queryClient = useQueryClient();
  const theme = useAppTheme();
  const networkState = useNetworkState();
  const [isReconnecting, setIsReconnecting] = useState(false);
  const isOffline =
    isOfflineOverride ??
    (networkState.isConnected === false || networkState.isInternetReachable === false);

  const handleReconnect = async () => {
    setIsReconnecting(true);
    AccessibilityInfo.announceForAccessibility('Tentando restabelecer conexão com o servidor...');
    try {
      if (onReconnect) {
        await onReconnect();
      }
      const currentState = await getNetworkStateAsync();
      if (currentState.isConnected === false || currentState.isInternetReachable === false) {
        throw new Error('offline');
      }
      onlineManager.setOnline(true);
      await queryClient.invalidateQueries();
      await queryClient.refetchQueries({ type: 'active' });
      AccessibilityInfo.announceForAccessibility('Conexão restabelecida com sucesso.');
    } catch {
      AccessibilityInfo.announceForAccessibility('Ainda sem conexão com o servidor.');
    } finally {
      setIsReconnecting(false);
    }
  };

  if (!isOffline) {
    return null;
  }

  return (
    <View
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
      style={[
        styles.container,
        {
          backgroundColor: theme.isHighContrast ? '#5C1D00' : '#8A3B00',
          borderColor: theme.isHighContrast ? '#FFFFFF' : '#FFDCC1',
        },
      ]}
    >
      <View style={styles.textContainer}>
        <Text style={[styles.title, theme.typography.labelMd, { color: '#FFFFFF' }]}>
          Modo Offline
        </Text>
        <Text style={[styles.message, theme.typography.bodySm, { color: '#FFE0CC' }]}>
          Dados já carregados podem estar desatualizados. Ações de escrita ficam bloqueadas até a reconexão.
        </Text>
      </View>

      <TouchableOpacity
        {...makeAccessibleButton(
          'Tentar reconectar',
          'Atualiza os dados e verifica o status da conexão com os servidores do ECOnexão'
        )}
        style={[styles.reconnectButton, { backgroundColor: '#FFFFFF' }]}
        onPress={handleReconnect}
        disabled={isReconnecting}
      >
        <Text style={[styles.reconnectText, { color: '#8A3B00', fontWeight: '700' }]}>
          {isReconnecting ? 'Conectando...' : 'Reconectar'}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  textContainer: {
    flex: 1,
    paddingRight: 12,
  },
  title: {
    fontWeight: '700',
    marginBottom: 2,
  },
  message: {
    lineHeight: 16,
  },
  reconnectButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  reconnectText: {
    fontSize: 13,
  },
});
