import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, AccessibilityInfo } from 'react-native';
import { useQueryClient, useIsFetching, useIsMutating } from '@tanstack/react-query';
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
  const [isOffline, setIsOffline] = useState(isOfflineOverride ?? false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  useEffect(() => {
    if (isOfflineOverride !== undefined) {
      setIsOffline(isOfflineOverride);
    }
  }, [isOfflineOverride]);

  const handleReconnect = async () => {
    setIsReconnecting(true);
    AccessibilityInfo.announceForAccessibility('Tentando restabelecer conexão com o servidor...');
    try {
      if (onReconnect) {
        onReconnect();
      }
      await queryClient.invalidateQueries();
      await queryClient.refetchQueries({ type: 'active' });
      setIsOffline(false);
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
          Exibindo dados locais em cache. Ações de escrita serão pausadas até a reconexão.
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
