import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { apiClient } from '../../api/client';
import { AccessibleModal } from '../common/AccessibleModal';
import {
  EditorialAlertSchema,
  PublishGuardResultSchema,
  ReconciliationCandidateSchema,
  StatusTransitionRequest,
  StatusTransitionSchema,
} from '../../api/types';
import { useAdminContextQuery } from '../../hooks/queries';
import { useAppTheme } from '../../theme/useAppTheme';

export type ReviewSubTab = 'guard_transitions' | 'reconciliation' | 'alerts';

export interface WorkflowReviewQueueProps {
  initialSubTab?: ReviewSubTab;
}

export const WorkflowReviewQueue: React.FC<WorkflowReviewQueueProps> = ({
  initialSubTab = 'guard_transitions',
}) => {
  const { colors } = useAppTheme();
  const { data: adminContext } = useAdminContextQuery(true);
  const [subTab, setSubTab] = useState<ReviewSubTab>(initialSubTab);

  const scopes = adminContext?.access?.scopes || [];
  const capabilities = Array.from(new Set(scopes.flatMap((s) => s.capabilities || [])));
  const canPublish = capabilities.includes('content.publish');

  // ---------------------------------------------------------------------------
  // State: Guard & Transitions
  // ---------------------------------------------------------------------------
  const [resourceType, setResourceType] = useState<'route' | 'actor' | 'region'>('route');
  const [resourceId, setResourceId] = useState('');
  const [guardResult, setGuardResult] = useState<PublishGuardResultSchema | null>(null);
  const [guardLoading, setGuardLoading] = useState(false);
  const [transitionLoading, setTransitionLoading] = useState(false);
  const [transitionSuccess, setTransitionSuccess] = useState<StatusTransitionSchema | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  // Transition Modal state
  const [transitionModalVisible, setTransitionModalVisible] = useState(false);
  const [targetStatus, setTargetStatus] = useState<StatusTransitionRequest['target_status']>('review');
  const [transitionReason, setTransitionReason] = useState('');

  // ---------------------------------------------------------------------------
  // State: Reconciliation
  // ---------------------------------------------------------------------------
  const [candidates, setCandidates] = useState<ReconciliationCandidateSchema[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<ReconciliationCandidateSchema | null>(null);
  const [decisionModalVisible, setDecisionModalVisible] = useState(false);
  const [decisionType, setDecisionType] = useState<'accept' | 'reject' | 'merge'>('merge');
  const [decisionReason, setDecisionReason] = useState('');
  const [decisionTargetActorId, setDecisionTargetActorId] = useState('');
  const [decisionLoading, setDecisionLoading] = useState(false);

  // ---------------------------------------------------------------------------
  // State: Editorial Alerts
  // ---------------------------------------------------------------------------
  const [alerts, setAlerts] = useState<EditorialAlertSchema[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [resolveModalVisible, setResolveModalVisible] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<EditorialAlertSchema | null>(null);
  const [resolutionNote, setResolutionNote] = useState('');
  const [resolveLoading, setResolveLoading] = useState(false);

  // Load sub-tab specific data
  useEffect(() => {
    if (subTab === 'reconciliation') {
      loadCandidates();
    } else if (subTab === 'alerts') {
      loadAlerts();
    }
  }, [subTab]);

  const loadCandidates = async () => {
    setCandidatesLoading(true);
    setFeedbackError(null);
    try {
      const res = await apiClient.getReconciliationCandidates({ status: 'pending' });
      setCandidates(res.data || []);
    } catch (err: any) {
      setFeedbackError(err.message || 'Erro ao carregar candidatos de reconciliação.');
    } finally {
      setCandidatesLoading(false);
    }
  };

  const loadAlerts = async () => {
    setAlertsLoading(true);
    setFeedbackError(null);
    try {
      const res = await apiClient.getEditorialAlerts({ is_active: true });
      setAlerts(res.data || []);
    } catch (err: any) {
      setFeedbackError(err.message || 'Erro ao carregar alertas editoriais.');
    } finally {
      setAlertsLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Handlers: Publish Guard
  // ---------------------------------------------------------------------------
  const handleCheckPublishGuard = async () => {
    if (!resourceId.trim()) {
      setFeedbackError('Informe o UUID do recurso para avaliar o Publish Guard.');
      return;
    }
    setGuardLoading(true);
    setFeedbackError(null);
    setGuardResult(null);
    setTransitionSuccess(null);
    try {
      const res = await apiClient.getPublishGuardStatus(resourceType, resourceId.trim());
      setGuardResult(res.data);
    } catch (err: any) {
      setFeedbackError(err.message || 'Erro ao avaliar critérios do Publish Guard.');
    } finally {
      setGuardLoading(false);
    }
  };

  const openTransitionModal = (statusTo: StatusTransitionRequest['target_status']) => {
    setTargetStatus(statusTo);
    setTransitionReason('');
    setFeedbackError(null);
    setTransitionModalVisible(true);
  };

  const handleExecuteTransition = async () => {
    if (!resourceId.trim()) {
      setFeedbackError('UUID do recurso não especificado.');
      return;
    }
    if ((targetStatus === 'draft' || targetStatus === 'archived') && !transitionReason.trim()) {
      setFeedbackError('Justificativa obrigatória para rejeição, despublicação ou descarte.');
      return;
    }

    setTransitionLoading(true);
    setFeedbackError(null);
    try {
      const res = await apiClient.transitionResourceStatus(resourceType, resourceId.trim(), {
        target_status: targetStatus,
        reason: transitionReason.trim() || undefined,
      });
      setTransitionSuccess(res.data);
      setTransitionModalVisible(false);
      handleCheckPublishGuard();
    } catch (err: any) {
      setFeedbackError(err.message || 'Falha ao executar transição de estado.');
    } finally {
      setTransitionLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Handlers: Reconciliation Decision
  // ---------------------------------------------------------------------------
  const openDecisionModal = (candidate: ReconciliationCandidateSchema, decision: 'accept' | 'reject' | 'merge') => {
    setSelectedCandidate(candidate);
    setDecisionType(decision);
    setDecisionReason('');
    setDecisionTargetActorId(candidate.actor_id_a || '');
    setFeedbackError(null);
    setDecisionModalVisible(true);
  };

  const handleExecuteDecision = async () => {
    if (!selectedCandidate) return;
    if (!decisionReason.trim()) {
      setFeedbackError('A justificativa é obrigatória para qualquer decisão de reconciliação.');
      return;
    }
    if (decisionType === 'merge' && !decisionTargetActorId.trim()) {
      setFeedbackError('Informe o UUID do ator primário de destino para a fusão.');
      return;
    }

    setDecisionLoading(true);
    setFeedbackError(null);
    try {
      await apiClient.decideReconciliationCandidate(selectedCandidate.id, {
        decision: decisionType,
        reason: decisionReason.trim(),
        target_actor_id: decisionType === 'merge' ? decisionTargetActorId.trim() : undefined,
      });
      setDecisionModalVisible(false);
      loadCandidates();
    } catch (err: any) {
      setFeedbackError(err.message || 'Erro ao registrar decisão de reconciliação.');
    } finally {
      setDecisionLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Handlers: Alert Resolution
  // ---------------------------------------------------------------------------
  const openResolveModal = (alert: EditorialAlertSchema) => {
    setSelectedAlert(alert);
    setResolutionNote('');
    setFeedbackError(null);
    setResolveModalVisible(true);
  };

  const handleExecuteResolveAlert = async () => {
    if (!selectedAlert) return;
    if (!resolutionNote.trim()) {
      setFeedbackError('A nota de resolução é obrigatória.');
      return;
    }

    setResolveLoading(true);
    setFeedbackError(null);
    try {
      await apiClient.resolveEditorialAlert(selectedAlert.id, {
        resolution_note: resolutionNote.trim(),
      });
      setResolveModalVisible(false);
      loadAlerts();
    } catch (err: any) {
      setFeedbackError(err.message || 'Erro ao resolver alerta.');
    } finally {
      setResolveLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Sub-Navigation */}
      <View style={styles.subTabBar} accessibilityRole="tablist">
        <TouchableOpacity
          style={[styles.subTabButton, subTab === 'guard_transitions' && styles.subTabButtonActive]}
          onPress={() => setSubTab('guard_transitions')}
          accessibilityRole="tab"
          accessibilityState={{ selected: subTab === 'guard_transitions' }}
          accessibilityLabel="Aba Publicação e Publish Guard"
        >
          <Text style={[styles.subTabText, subTab === 'guard_transitions' && styles.subTabTextActive]}>
            Publish Guard & Status
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.subTabButton, subTab === 'reconciliation' && styles.subTabButtonActive]}
          onPress={() => setSubTab('reconciliation')}
          accessibilityRole="tab"
          accessibilityState={{ selected: subTab === 'reconciliation' }}
          accessibilityLabel="Aba Reconciliação de Duplicatas"
        >
          <Text style={[styles.subTabText, subTab === 'reconciliation' && styles.subTabTextActive]}>
            Reconciliação ({candidates.length})
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.subTabButton, subTab === 'alerts' && styles.subTabButtonActive]}
          onPress={() => setSubTab('alerts')}
          accessibilityRole="tab"
          accessibilityState={{ selected: subTab === 'alerts' }}
          accessibilityLabel="Aba Alertas Editoriais"
        >
          <Text style={[styles.subTabText, subTab === 'alerts' && styles.subTabTextActive]}>
            Alertas ({alerts.length})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Global Error Banner */}
      {feedbackError && (
        <View style={styles.errorBanner} accessibilityRole="alert">
          <Text style={styles.errorBannerText}>{feedbackError}</Text>
        </View>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* SUB-TAB 1: Publish Guard & State Transitions */}
      {/* --------------------------------------------------------------------- */}
      {subTab === 'guard_transitions' && (
        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Governança Editorial & Publish Guard (ADR 0006)</Text>
          <Text style={styles.sectionSubtitle}>
            Valide critérios obrigatórios de completude territorial, geometria, mídia e dados de contato antes de transicionar ou publicar.
          </Text>

          {/* Form to Inspect */}
          <View style={styles.card}>
            <Text style={styles.cardLabel}>Tipo de Recurso</Text>
            <View style={styles.typeSelectorRow}>
              {(['route', 'actor', 'region'] as const).map((type) => (
                <TouchableOpacity
                  key={type}
                  style={[styles.typeOption, resourceType === type && styles.typeOptionActive]}
                  onPress={() => {
                    setResourceType(type);
                    setGuardResult(null);
                  }}
                  accessibilityRole="radio"
                  accessibilityState={{ selected: resourceType === type }}
                  accessibilityLabel={`Tipo ${type}`}
                >
                  <Text style={[styles.typeOptionText, resourceType === type && styles.typeOptionTextActive]}>
                    {type.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.cardLabel}>UUID do Recurso</Text>
            <TextInput
              style={styles.input}
              placeholder="Ex: 550e8400-e29b-41d4-a716-446655440000"
              value={resourceId}
              onChangeText={setResourceId}
              autoCapitalize="none"
              autoCorrect={false}
              accessibilityLabel="UUID do recurso"
            />

            <TouchableOpacity
              style={styles.primaryButton}
              onPress={handleCheckPublishGuard}
              disabled={guardLoading}
              accessibilityRole="button"
              accessibilityLabel="Avaliar Requisitos do Publish Guard"
            >
              {guardLoading ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <Text style={styles.primaryButtonText}>Avaliar Requisitos do Publish Guard</Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Guard Result Details */}
          {guardResult && (
            <View style={styles.resultCard}>
              <View style={styles.resultHeader}>
                <Text style={styles.resultTitle}>
                  Status Atual: <Text style={styles.statusBadgeText}>{String(guardResult.current_status || 'draft').toUpperCase()}</Text>
                </Text>
                <View
                  style={[
                    styles.eligibilityBadge,
                    guardResult.is_eligible ? styles.badgeSuccess : styles.badgeWarning,
                  ]}
                >
                  <Text style={styles.eligibilityText}>
                    {guardResult.is_eligible ? 'Elegível para Publicação' : 'Bloqueado pelo Publish Guard'}
                  </Text>
                </View>
              </View>

              {/* Requirement Checklist */}
              <Text style={styles.checkListTitle}>Requisitos Pendentes:</Text>
              {guardResult.missing_requirements && guardResult.missing_requirements.length > 0 ? (
                guardResult.missing_requirements.map((req, idx) => (
                  <View key={idx} style={styles.checkItem}>
                    <Text style={styles.checkIconFail}>✗</Text>
                    <View style={styles.checkTextCol}>
                      <Text style={styles.checkName}>{req}</Text>
                    </View>
                  </View>
                ))
              ) : (
                <View style={styles.checkItem}>
                  <Text style={styles.checkIconSuccess}>✓</Text>
                  <View style={styles.checkTextCol}>
                    <Text style={styles.checkName}>Todos os critérios de completude atendidos!</Text>
                  </View>
                </View>
              )}

              {/* Warnings */}
              {guardResult.warnings && guardResult.warnings.length > 0 && (
                <View style={{ marginTop: 8 }}>
                  <Text style={styles.checkListTitle}>Avisos Não Impeditivos:</Text>
                  {guardResult.warnings.map((warn, idx) => (
                    <View key={idx} style={styles.checkItem}>
                      <Text style={styles.checkIconWarning}>⚠</Text>
                      <View style={styles.checkTextCol}>
                        <Text style={styles.checkMessage}>{warn}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              )}

              {/* Transition Action Buttons */}
              <View style={styles.actionRow}>
                <TouchableOpacity
                  style={[styles.actionButton, styles.buttonReview]}
                  onPress={() => openTransitionModal('review')}
                  accessibilityRole="button"
                  accessibilityLabel="Solicitar Revisão"
                >
                  <Text style={styles.actionButtonText}>Enviar p/ Revisão</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[
                    styles.actionButton,
                    styles.buttonPublish,
                    (!canPublish || !guardResult.is_eligible) && styles.buttonDisabled,
                  ]}
                  onPress={() => openTransitionModal('published')}
                  disabled={!canPublish || !guardResult.is_eligible}
                  accessibilityRole="button"
                  accessibilityLabel="Publicar Recurso"
                >
                  <Text style={styles.actionButtonText}>Publicar</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionButton, styles.buttonReject]}
                  onPress={() => openTransitionModal('draft')}
                  accessibilityRole="button"
                  accessibilityLabel="Rejeitar ou Retornar para Rascunho"
                >
                  <Text style={styles.actionButtonText}>Retornar Rascunho</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionButton, styles.buttonArchive]}
                  onPress={() => openTransitionModal('archived')}
                  accessibilityRole="button"
                  accessibilityLabel="Arquivar Recurso"
                >
                  <Text style={styles.actionButtonText}>Arquivar</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {transitionSuccess && (
            <View style={styles.successCard}>
              <Text style={styles.successTitle}>Transição Concluída com Sucesso!</Text>
              <Text style={styles.successText}>
                Novo Estado: {String(transitionSuccess.new_status).toUpperCase()} (Versão: {transitionSuccess.version})
              </Text>
            </View>
          )}
        </View>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* SUB-TAB 2: Reconciliation Candidates */}
      {/* --------------------------------------------------------------------- */}
      {subTab === 'reconciliation' && (
        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Reconciliação de Candidatos Duplicados</Text>
          <Text style={styles.sectionSubtitle}>
            Proibido auto-merge por regra de negócio. Revise pares suspeitos e registre decisão auditada com justificativa.
          </Text>

          {candidatesLoading ? (
            <ActivityIndicator size="large" color={colors.brandForest || '#059669'} style={{ marginTop: 24 }} />
          ) : candidates.length === 0 ? (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyTitle}>Nenhum candidato a duplicata pendente</Text>
              <Text style={styles.emptyText}>Todas as reconciliações territoriais estão em dia.</Text>
            </View>
          ) : (
            candidates.map((cand) => (
              <View key={cand.id} style={styles.candidateCard}>
                <View style={styles.candidateHeader}>
                  <Text style={styles.candidateTitle}>Candidato: {cand.id}</Text>
                  <View style={styles.scoreBadge}>
                    <Text style={styles.scoreText}>Score: {Math.round((cand.score || 0) * 100)}%</Text>
                  </View>
                </View>

                <Text style={styles.candidateDetails}>
                  Ator A: {cand.actor_id_a}
                </Text>
                <Text style={styles.candidateDetails}>
                  Ator B: {cand.actor_id_b}
                </Text>

                <View style={styles.candidateActions}>
                  <TouchableOpacity
                    style={[styles.smallButton, styles.buttonMerge]}
                    onPress={() => openDecisionModal(cand, 'merge')}
                    accessibilityRole="button"
                    accessibilityLabel="Mesclar Duplicata"
                  >
                    <Text style={styles.smallButtonText}>Mesclar (Merge)</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.smallButton, styles.buttonAccept]}
                    onPress={() => openDecisionModal(cand, 'accept')}
                    accessibilityRole="button"
                    accessibilityLabel="Aceitar como Distintos"
                  >
                    <Text style={styles.smallButtonText}>Aceitar (Distintos)</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.smallButton, styles.buttonRejectCandidate]}
                    onPress={() => openDecisionModal(cand, 'reject')}
                    accessibilityRole="button"
                    accessibilityLabel="Rejeitar Duplicata"
                  >
                    <Text style={styles.smallButtonText}>Rejeitar</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}
        </View>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* SUB-TAB 3: Editorial Alerts */}
      {/* --------------------------------------------------------------------- */}
      {subTab === 'alerts' && (
        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Alertas Territoriais & Desvios de Rota</Text>
          <Text style={styles.sectionSubtitle}>
            Avisos de interdição, alertas climáticos e notas comunitárias ativas nas rotas eco-turísticas.
          </Text>

          {alertsLoading ? (
            <ActivityIndicator size="large" color={colors.brandForest || '#059669'} style={{ marginTop: 24 }} />
          ) : alerts.length === 0 ? (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyTitle}>Nenhum alerta ativo no momento</Text>
              <Text style={styles.emptyText}>Todas as rotas comunitárias operando normalmente.</Text>
            </View>
          ) : (
            alerts.map((al) => (
              <View key={al.id} style={styles.alertCard}>
                <View style={styles.alertHeader}>
                  <Text style={styles.alertTitle}>{al.title}</Text>
                  <View
                    style={[
                      styles.severityBadge,
                      al.severity === 'critical'
                        ? styles.badgeCritical
                        : al.severity === 'warning'
                        ? styles.badgeWarning
                        : styles.badgeInfo,
                    ]}
                  >
                    <Text style={styles.severityText}>{String(al.severity || 'info').toUpperCase()}</Text>
                  </View>
                </View>

                <Text style={styles.alertMessage}>{al.message}</Text>
                {al.route_id ? <Text style={styles.alertRoute}>Rota vinculada: {al.route_id}</Text> : null}

                <TouchableOpacity
                  style={[styles.smallButton, styles.buttonResolve]}
                  onPress={() => openResolveModal(al)}
                  accessibilityRole="button"
                  accessibilityLabel="Resolver Alerta"
                >
                  <Text style={styles.smallButtonText}>Resolver Alerta</Text>
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Modal: State Transition */}
      {/* --------------------------------------------------------------------- */}
      <AccessibleModal
        visible={transitionModalVisible}
        transparent
        animationType="slide"
        onClose={() => setTransitionModalVisible(false)}
        accessibilityLabel="Confirmar transição editorial"
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Confirmar Transição Editorial</Text>
            <Text style={styles.modalSubtitle}>
              Transicionar recurso [{resourceType}] para o estado [{targetStatus.toUpperCase()}].
            </Text>

            <Text style={styles.cardLabel}>Justificativa / Motivo</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Descreva a razão desta transição..."
              value={transitionReason}
              onChangeText={setTransitionReason}
              multiline
              numberOfLines={3}
              accessibilityLabel="Campo de justificativa de transição"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalButton, styles.buttonCancel]}
                onPress={() => setTransitionModalVisible(false)}
                accessibilityRole="button"
                accessibilityLabel="Cancelar transição"
              >
                <Text style={[styles.modalButtonText, { color: '#475569' }]}>Cancelar</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.buttonConfirm]}
                onPress={handleExecuteTransition}
                disabled={transitionLoading}
                accessibilityRole="button"
                accessibilityLabel="Confirmar transição"
              >
                {transitionLoading ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={styles.modalButtonText}>Confirmar</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </AccessibleModal>

      {/* --------------------------------------------------------------------- */}
      {/* Modal: Reconciliation Decision */}
      {/* --------------------------------------------------------------------- */}
      <AccessibleModal
        visible={decisionModalVisible}
        transparent
        animationType="slide"
        onClose={() => setDecisionModalVisible(false)}
        accessibilityLabel="Decisão de reconciliação"
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Decisão de Reconciliação ({decisionType.toUpperCase()})</Text>
            <Text style={styles.modalSubtitle}>
              Candidato ID: {selectedCandidate?.id}
            </Text>

            {decisionType === 'merge' && (
              <>
                <Text style={styles.cardLabel}>UUID do Ator Primário (Destino)</Text>
                <TextInput
                  style={styles.input}
                  placeholder="UUID do ator primário..."
                  value={decisionTargetActorId}
                  onChangeText={setDecisionTargetActorId}
                  accessibilityLabel="UUID do ator de destino para merge"
                />
              </>
            )}

            <Text style={styles.cardLabel}>Justificativa Obrigatória</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Explique o motivo técnico ou editorial desta decisão..."
              value={decisionReason}
              onChangeText={setDecisionReason}
              multiline
              numberOfLines={3}
              accessibilityLabel="Campo de justificativa de reconciliação"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalButton, styles.buttonCancel]}
                onPress={() => setDecisionModalVisible(false)}
                accessibilityRole="button"
                accessibilityLabel="Cancelar decisão"
              >
                <Text style={[styles.modalButtonText, { color: '#475569' }]}>Cancelar</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.buttonConfirm]}
                onPress={handleExecuteDecision}
                disabled={decisionLoading}
                accessibilityRole="button"
                accessibilityLabel="Salvar decisão de reconciliação"
              >
                {decisionLoading ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={styles.modalButtonText}>Registrar Decisão</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </AccessibleModal>

      {/* --------------------------------------------------------------------- */}
      {/* Modal: Resolve Alert */}
      {/* --------------------------------------------------------------------- */}
      <AccessibleModal
        visible={resolveModalVisible}
        transparent
        animationType="slide"
        onClose={() => setResolveModalVisible(false)}
        accessibilityLabel="Resolver alerta editorial"
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Resolver Alerta Editorial</Text>
            <Text style={styles.modalSubtitle}>{selectedAlert?.title}</Text>

            <Text style={styles.cardLabel}>Nota Explicativa de Resolução</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Descreva as medidas tomadas ou normalização do trajeto..."
              value={resolutionNote}
              onChangeText={setResolutionNote}
              multiline
              numberOfLines={3}
              accessibilityLabel="Nota de resolução do alerta"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalButton, styles.buttonCancel]}
                onPress={() => setResolveModalVisible(false)}
                accessibilityRole="button"
                accessibilityLabel="Cancelar resolução"
              >
                <Text style={[styles.modalButtonText, { color: '#475569' }]}>Cancelar</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.buttonConfirm]}
                onPress={handleExecuteResolveAlert}
                disabled={resolveLoading}
                accessibilityRole="button"
                accessibilityLabel="Confirmar resolução do alerta"
              >
                {resolveLoading ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={styles.modalButtonText}>Concluir Resolução</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </AccessibleModal>
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
  subTabBar: {
    flexDirection: 'row',
    backgroundColor: '#E2E8F0',
    borderRadius: 8,
    padding: 4,
    marginBottom: 16,
  },
  subTabButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 6,
  },
  subTabButtonActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  subTabText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  subTabTextActive: {
    color: '#0F172A',
  },
  errorBanner: {
    backgroundColor: '#FEE2E2',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444',
    marginBottom: 16,
  },
  errorBannerText: {
    color: '#991B1B',
    fontSize: 14,
    fontWeight: '500',
  },
  sectionContainer: {
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 16,
    lineHeight: 18,
  },
  card: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  cardLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
  },
  typeSelectorRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  typeOption: {
    flex: 1,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 6,
    alignItems: 'center',
  },
  typeOptionActive: {
    backgroundColor: '#0F172A',
    borderColor: '#0F172A',
  },
  typeOptionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  typeOptionTextActive: {
    color: '#FFFFFF',
  },
  input: {
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#0F172A',
    backgroundColor: '#FFFFFF',
    marginBottom: 14,
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  primaryButton: {
    backgroundColor: '#059669',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  resultCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    marginBottom: 16,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  resultTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  statusBadgeText: {
    color: '#2563EB',
  },
  eligibilityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeSuccess: {
    backgroundColor: '#DCFCE7',
  },
  badgeWarning: {
    backgroundColor: '#FEF3C7',
  },
  badgeCritical: {
    backgroundColor: '#FEE2E2',
  },
  badgeInfo: {
    backgroundColor: '#E0F2FE',
  },
  eligibilityText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#0F172A',
  },
  checkListTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 8,
  },
  checkItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  checkIconSuccess: {
    color: '#16A34A',
    fontWeight: '700',
    fontSize: 14,
    marginRight: 8,
  },
  checkIconFail: {
    color: '#DC2626',
    fontWeight: '700',
    fontSize: 14,
    marginRight: 8,
  },
  checkIconWarning: {
    color: '#D97706',
    fontWeight: '700',
    fontSize: 14,
    marginRight: 8,
  },
  checkTextCol: {
    flex: 1,
  },
  checkName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1E293B',
  },
  checkMessage: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 1,
  },
  actionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
  },
  actionButton: {
    flex: 1,
    minWidth: '45%',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonReview: {
    backgroundColor: '#3B82F6',
  },
  buttonPublish: {
    backgroundColor: '#10B981',
  },
  buttonReject: {
    backgroundColor: '#F59E0B',
  },
  buttonArchive: {
    backgroundColor: '#64748B',
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  successCard: {
    backgroundColor: '#ECFDF5',
    padding: 14,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#10B981',
    marginBottom: 16,
  },
  successTitle: {
    color: '#065F46',
    fontWeight: '700',
    fontSize: 14,
  },
  successText: {
    color: '#047857',
    fontSize: 13,
    marginTop: 2,
  },
  emptyCard: {
    backgroundColor: '#FFFFFF',
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#334155',
  },
  emptyText: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4,
  },
  candidateCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
  },
  candidateHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  candidateTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  scoreBadge: {
    backgroundColor: '#E0E7FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  scoreText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#3730A3',
  },
  candidateDetails: {
    fontSize: 13,
    color: '#475569',
    marginBottom: 4,
  },
  candidateActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  smallButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  buttonMerge: {
    backgroundColor: '#8B5CF6',
  },
  buttonAccept: {
    backgroundColor: '#059669',
  },
  buttonRejectCandidate: {
    backgroundColor: '#EF4444',
  },
  buttonResolve: {
    backgroundColor: '#0284C7',
    marginTop: 10,
  },
  smallButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  alertCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  alertTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  severityText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0F172A',
  },
  alertMessage: {
    fontSize: 13,
    color: '#334155',
    lineHeight: 18,
  },
  alertRoute: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    justifyContent: 'center',
    padding: 20,
  },
  modalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 6,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 16,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonCancel: {
    backgroundColor: '#F1F5F9',
  },
  buttonConfirm: {
    backgroundColor: '#0F172A',
  },
  modalButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
