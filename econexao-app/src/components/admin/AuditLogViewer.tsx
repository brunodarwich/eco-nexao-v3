import React, { useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { useAppTheme } from '../../theme/useAppTheme';

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor_id: string;
  action: 'CREATE' | 'UPDATE' | 'TRANSITION_STATUS' | 'RECONCILE' | 'DELETE';
  resource_type: string;
  resource_id: string;
  reason?: string;
  changes?: {
    before?: Record<string, any> | null;
    after?: Record<string, any> | null;
  };
}

export interface AuditLogViewerProps {
  initialLogs?: AuditLogEntry[];
}

export const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ initialLogs = [] }) => {
  const { colors } = useAppTheme();
  const [filterAction, setFilterAction] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const actions = ['ALL', 'TRANSITION_STATUS', 'RECONCILE', 'CREATE', 'UPDATE', 'DELETE'];

  const filteredLogs = initialLogs.filter((log) => {
    if (filterAction !== 'ALL' && log.action !== filterAction) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchResource = log.resource_id.toLowerCase().includes(q) || log.resource_type.toLowerCase().includes(q);
      const matchReason = log.reason?.toLowerCase().includes(q);
      const matchActor = log.actor_id.toLowerCase().includes(q);
      return matchResource || matchReason || matchActor;
    }
    return true;
  });

  const formatTimestamp = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleString('pt-BR', { timeZone: 'America/Manaus' });
    } catch {
      return iso;
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Trilha de Auditoria Imutável (ADR 0006)</Text>
      <Text style={styles.subtitle}>
        Registros append-only de governança editorial, publicação, reconciliação e concessão de privilégios.
      </Text>

      {/* Filter Chips */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow}>
        {actions.map((act) => (
          <TouchableOpacity
            key={act}
            style={[styles.filterChip, filterAction === act && styles.filterChipActive]}
            onPress={() => setFilterAction(act)}
            accessibilityRole="button"
            accessibilityState={{ selected: filterAction === act }}
            accessibilityLabel={`Filtrar por ${act}`}
          >
            <Text style={[styles.filterChipText, filterAction === act && styles.filterChipTextActive]}>
              {act}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Search Input */}
      <TextInput
        style={styles.searchInput}
        placeholder="Buscar por UUID de recurso, tipo, motivo ou autor..."
        value={searchQuery}
        onChangeText={setSearchQuery}
        accessibilityLabel="Buscar logs de auditoria"
      />

      {/* Logs List */}
      {filteredLogs.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>Nenhum registro de auditoria encontrado</Text>
          <Text style={styles.emptySubtitle}>
            {initialLogs.length === 0
              ? 'Nenhuma ação administrativa recente foi registrada nesta sessão.'
              : 'Nenhum log corresponde aos filtros informados.'}
          </Text>
        </View>
      ) : (
        filteredLogs.map((log) => (
          <View key={log.id} style={styles.logCard}>
            <View style={styles.logHeader}>
              <View
                style={[
                  styles.actionBadge,
                  log.action === 'TRANSITION_STATUS'
                    ? styles.badgeTransition
                    : log.action === 'RECONCILE'
                    ? styles.badgeReconcile
                    : log.action === 'CREATE'
                    ? styles.badgeCreate
                    : log.action === 'DELETE'
                    ? styles.badgeDelete
                    : styles.badgeUpdate,
                ]}
              >
                <Text style={styles.actionBadgeText}>{log.action}</Text>
              </View>
              <Text style={styles.timestampText}>{formatTimestamp(log.timestamp)}</Text>
            </View>

            <Text style={styles.resourceLine}>
              Recurso: <Text style={styles.highlightText}>[{log.resource_type.toUpperCase()}]</Text> {log.resource_id}
            </Text>
            <Text style={styles.actorLine}>Executor: {log.actor_id}</Text>

            {log.reason ? (
              <View style={styles.reasonBox}>
                <Text style={styles.reasonLabel}>Justificativa:</Text>
                <Text style={styles.reasonText}>{log.reason}</Text>
              </View>
            ) : null}

            {log.changes && (log.changes.before || log.changes.after) ? (
              <View style={styles.changesBox}>
                <Text style={styles.changesTitle}>Diferenças (Payload Snapshot):</Text>
                {log.changes.before ? (
                  <Text style={styles.beforeText}>
                    - Before: {JSON.stringify(log.changes.before)}
                  </Text>
                ) : null}
                {log.changes.after ? (
                  <Text style={styles.afterText}>
                    + After: {JSON.stringify(log.changes.after)}
                  </Text>
                ) : null}
              </View>
            ) : null}
          </View>
        ))
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  content: {
    padding: 16,
    paddingBottom: 48,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 16,
    lineHeight: 18,
  },
  filterRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#E2E8F0',
    marginRight: 8,
  },
  filterChipActive: {
    backgroundColor: '#0F172A',
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
  },
  searchInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: '#0F172A',
    marginBottom: 16,
  },
  emptyContainer: {
    backgroundColor: '#FFFFFF',
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginTop: 12,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#334155',
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
    textAlign: 'center',
  },
  logCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
  },
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeTransition: {
    backgroundColor: '#DBEAFE',
  },
  badgeReconcile: {
    backgroundColor: '#EDE9FE',
  },
  badgeCreate: {
    backgroundColor: '#DCFCE7',
  },
  badgeUpdate: {
    backgroundColor: '#FEF3C7',
  },
  badgeDelete: {
    backgroundColor: '#FEE2E2',
  },
  actionBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0F172A',
  },
  timestampText: {
    fontSize: 11,
    color: '#94A3B8',
  },
  resourceLine: {
    fontSize: 13,
    color: '#1E293B',
    marginBottom: 2,
  },
  highlightText: {
    fontWeight: '700',
    color: '#2563EB',
  },
  actorLine: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 6,
  },
  reasonBox: {
    backgroundColor: '#F1F5F9',
    padding: 8,
    borderRadius: 6,
    marginTop: 4,
    marginBottom: 6,
  },
  reasonLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#475569',
  },
  reasonText: {
    fontSize: 12,
    color: '#334155',
    marginTop: 2,
  },
  changesBox: {
    backgroundColor: '#F8FAFC',
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginTop: 4,
  },
  changesTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#475569',
    marginBottom: 4,
  },
  beforeText: {
    fontSize: 11,
    color: '#DC2626',
    fontFamily: 'monospace',
  },
  afterText: {
    fontSize: 11,
    color: '#16A34A',
    fontFamily: 'monospace',
    marginTop: 2,
  },
});
