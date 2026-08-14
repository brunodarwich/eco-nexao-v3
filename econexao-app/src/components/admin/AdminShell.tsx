import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { useAdminContextQuery } from '../../hooks/queries';
import { AccessDeniedView } from './AccessDeniedView';
import { ActorEditor } from './ActorEditor';
import { AdminCapabilityGate } from './AdminCapabilityGate';
import { AuditLogViewer } from './AuditLogViewer';
import { TerritoryEditor } from './TerritoryEditor';
import { WorkflowReviewQueue } from './WorkflowReviewQueue';

export interface AdminShellProps {
  isAuthenticated?: boolean;
  onGoHome?: () => void;
  onLoginRequest?: () => void;
  onLogout?: () => void;
  onRetry?: () => void;
  children?: React.ReactNode;
}

export type AdminTab = 'territory' | 'actors' | 'review' | 'audit';

export const AdminShell: React.FC<AdminShellProps> = ({
  isAuthenticated = true,
  onGoHome,
  onLoginRequest,
  onLogout,
  onRetry,
  children,
}) => {
  const { data: adminContext } = useAdminContextQuery(isAuthenticated);
  const [activeTab, setActiveTab] = useState<AdminTab>('territory');

  const scopes = adminContext?.access?.scopes || [];
  const capabilities = Array.from(new Set(scopes.flatMap((s) => s.capabilities || [])));
  const roles = Array.from(new Set(scopes.flatMap((s) => s.roles || [])));
  const primaryRole = roles[0] || 'editor';

  const canAccessTerritory = capabilities.includes('territory.read') || capabilities.includes('territory.write');
  const canAccessActors = capabilities.includes('actor.write') || capabilities.includes('territory.write');
  const canAccessReview = capabilities.includes('content.publish') || roles.includes('reviewer');
  const canAccessAudit = capabilities.includes('content.archive') || roles.includes('admin');

  const renderActiveModule = () => {
    if (children) return children;

    switch (activeTab) {
      case 'territory':
        return <TerritoryEditor />;
      case 'actors':
        return <ActorEditor />;
      case 'review':
        return <WorkflowReviewQueue />;
      case 'audit':
        return <AuditLogViewer />;
      default:
        return (
          <View style={styles.placeholderContainer}>
            <Text style={styles.placeholderTitle}>
              Módulo Editorial: {String(activeTab).toUpperCase()}
            </Text>
            <Text style={styles.placeholderSubtitle}>
              Sessão autorizada para o papel [{primaryRole}] com {capabilities.length} permissões ativas.
            </Text>
          </View>
        );
    }
  };

  return (
    <AdminCapabilityGate
      isAuthenticated={isAuthenticated}
      onGoHome={onGoHome}
      onLoginRequest={onLoginRequest}
      onRetry={onRetry}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header} accessibilityRole="header">
          <View style={styles.brandRow}>
            <Text style={styles.brandTitle}>ECOconexão Editorial</Text>
            <View style={styles.roleBadge}>
              <Text style={styles.roleText}>{primaryRole.toUpperCase()}</Text>
            </View>
          </View>

          <View style={styles.actionsRow}>
            {onGoHome && (
              <TouchableOpacity
                style={styles.navButton}
                onPress={onGoHome}
                accessibilityRole="button"
                accessibilityLabel="Ir para o app público"
                accessibilityHint="Retorna à interface principal do ECOconexão"
              >
                <Text style={styles.navButtonText}>App Público</Text>
              </TouchableOpacity>
            )}
            {onLogout && (
              <TouchableOpacity
                style={[styles.navButton, styles.logoutButton]}
                onPress={onLogout}
                accessibilityRole="button"
                accessibilityLabel="Encerrar sessão editorial"
                accessibilityHint="Desconecta a conta editorial atual"
              >
                <Text style={styles.logoutButtonText}>Sair</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Dynamic Navigation Menu */}
        <View style={styles.navigationBar} accessibilityRole="tablist">
          {canAccessTerritory && (
            <TouchableOpacity
              style={[styles.tabItem, activeTab === 'territory' && styles.activeTabItem]}
              onPress={() => setActiveTab('territory')}
              accessibilityRole="tab"
              accessibilityState={{ selected: activeTab === 'territory' }}
              accessibilityLabel="Acessar gestão de território e rotas"
              accessibilityHint="Abre o módulo de edição de regiões e rotas comunitárias"
            >
              <Text
                style={[
                  styles.tabItemText,
                  activeTab === 'territory' && styles.activeTabItemText,
                ]}
              >
                Território & Rotas
              </Text>
            </TouchableOpacity>
          )}

          {canAccessActors && (
            <TouchableOpacity
              style={[styles.tabItem, activeTab === 'actors' && styles.activeTabItem]}
              onPress={() => setActiveTab('actors')}
              accessibilityRole="tab"
              accessibilityState={{ selected: activeTab === 'actors' }}
              accessibilityLabel="Acessar gestão de atores e estabelecimentos"
              accessibilityHint="Abre o módulo de gestão de atores, POIs e mídia"
            >
              <Text
                style={[
                  styles.tabItemText,
                  activeTab === 'actors' && styles.activeTabItemText,
                ]}
              >
                Atores
              </Text>
            </TouchableOpacity>
          )}

          {canAccessReview && (
            <TouchableOpacity
              style={[styles.tabItem, activeTab === 'review' && styles.activeTabItem]}
              onPress={() => setActiveTab('review')}
              accessibilityRole="tab"
              accessibilityState={{ selected: activeTab === 'review' }}
              accessibilityLabel="Acessar fila de revisão e publicação"
              accessibilityHint="Abre a fila editorial de aprovação e publicação de conteúdos"
            >
              <Text
                style={[
                  styles.tabItemText,
                  activeTab === 'review' && styles.activeTabItemText,
                ]}
              >
                Fila de Revisão
              </Text>
            </TouchableOpacity>
          )}

          {canAccessAudit && (
            <TouchableOpacity
              style={[styles.tabItem, activeTab === 'audit' && styles.activeTabItem]}
              onPress={() => setActiveTab('audit')}
              accessibilityRole="tab"
              accessibilityState={{ selected: activeTab === 'audit' }}
              accessibilityLabel="Acessar auditoria e logs do sistema"
              accessibilityHint="Abre o registro imutável de auditoria editorial"
            >
              <Text
                style={[
                  styles.tabItemText,
                  activeTab === 'audit' && styles.activeTabItemText,
                ]}
              >
                Auditoria
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Workspace / Content Area */}
        <View style={styles.workspace}>{renderActiveModule()}</View>
      </View>
    </AdminCapabilityGate>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F1F5F9',
  },
  header: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 24,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  brandTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  roleBadge: {
    backgroundColor: '#059669',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 6,
  },
  roleText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  navButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#334155',
  },
  navButtonText: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '500',
  },
  logoutButton: {
    backgroundColor: '#7F1D1D',
  },
  logoutButtonText: {
    color: '#FEE2E2',
    fontSize: 13,
    fontWeight: '600',
  },
  navigationBar: {
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    paddingHorizontal: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  tabItem: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTabItem: {
    borderBottomColor: '#059669',
  },
  tabItemText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748B',
  },
  activeTabItemText: {
    color: '#059669',
    fontWeight: '700',
  },
  workspace: {
    flex: 1,
    padding: 24,
  },
  placeholderContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 32,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderStyle: 'dashed',
  },
  placeholderTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 8,
  },
  placeholderSubtitle: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
  },
});
