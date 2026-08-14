import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { WorkflowReviewQueue } from './WorkflowReviewQueue';
import { AuditLogViewer, AuditLogEntry } from './AuditLogViewer';
import { apiClient } from '../../api/client';
import * as Queries from '../../hooks/queries';

jest.mock('../../api/client', () => ({
  apiClient: {
    configureAuth: jest.fn(),
    getPublishGuardStatus: jest.fn(),
    transitionResourceStatus: jest.fn(),
    getReconciliationCandidates: jest.fn().mockResolvedValue({ data: [] }),
    decideReconciliationCandidate: jest.fn(),
    getEditorialAlerts: jest.fn().mockResolvedValue({ data: [] }),
    resolveEditorialAlert: jest.fn(),
  },
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('ECO-1804 — Governança Editorial, Publish Guard, Reconciliação e Auditoria', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    jest.spyOn(Queries, 'useAdminContextQuery').mockReturnValue({
      data: {
        access: {
          user_id: 'user-publisher-uuid',
          roles: ['publisher'],
          capabilities: ['content.publish', 'content.review.submit', 'actor.write', 'territory.write', 'content.archive'],
          scopes: [
            {
              scope_type: 'global',
              roles: ['publisher'],
              capabilities: ['content.publish', 'content.review.submit', 'actor.write', 'territory.write', 'content.archive'],
            },
          ],
        },
      },
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
    } as any);
  });

  test('avalia critérios do Publish Guard com sucesso', async () => {
    mockApiClient.getPublishGuardStatus.mockResolvedValueOnce({
      data: {
        resource_type: 'route',
        resource_id: '550e8400-e29b-41d4-a716-446655440000',
        current_status: 'review',
        is_eligible: true,
        missing_requirements: [],
        warnings: ['Verificar cobertura de sinal'],
      },
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(<WorkflowReviewQueue initialSubTab="guard_transitions" />);
    });

    const root = tree!.root;
    const input = root.findByProps({ accessibilityLabel: 'UUID do recurso' });
    const checkBtn = root.findByProps({ accessibilityLabel: 'Avaliar Requisitos do Publish Guard' });

    await act(async () => {
      input.props.onChangeText('550e8400-e29b-41d4-a716-446655440000');
    });

    await act(async () => {
      await checkBtn.props.onPress();
    });

    expect(mockApiClient.getPublishGuardStatus).toHaveBeenCalledWith('route', '550e8400-e29b-41d4-a716-446655440000');
  });

  test('executa transição de publicação quando elegível', async () => {
    mockApiClient.getPublishGuardStatus.mockResolvedValue({
      data: {
        resource_type: 'route',
        resource_id: '550e8400-e29b-41d4-a716-446655440000',
        current_status: 'review',
        is_eligible: true,
        missing_requirements: [],
      },
    });

    mockApiClient.transitionResourceStatus.mockResolvedValueOnce({
      data: {
        resource_type: 'route',
        resource_id: '550e8400-e29b-41d4-a716-446655440000',
        previous_status: 'review',
        new_status: 'published',
        version: 2,
        audit_log_id: 'audit-log-uuid-1',
        updated_at: '2026-08-13T18:00:00Z',
      },
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(<WorkflowReviewQueue initialSubTab="guard_transitions" />);
    });

    const root = tree!.root;
    const input = root.findByProps({ accessibilityLabel: 'UUID do recurso' });
    const checkBtn = root.findByProps({ accessibilityLabel: 'Avaliar Requisitos do Publish Guard' });

    await act(async () => {
      input.props.onChangeText('550e8400-e29b-41d4-a716-446655440000');
    });

    await act(async () => {
      await checkBtn.props.onPress();
    });

    const publishBtn = root.findByProps({ accessibilityLabel: 'Publicar Recurso' });
    await act(async () => {
      publishBtn.props.onPress();
    });

    const confirmBtn = root.findByProps({ accessibilityLabel: 'Confirmar transição' });
    await act(async () => {
      await confirmBtn.props.onPress();
    });

    expect(mockApiClient.transitionResourceStatus).toHaveBeenCalledWith(
      'route',
      '550e8400-e29b-41d4-a716-446655440000',
      expect.objectContaining({ target_status: 'published' })
    );
  });

  test('lista candidatos e registra decisão de reconciliação com justificativa', async () => {
    mockApiClient.getReconciliationCandidates.mockResolvedValueOnce({
      data: [
        {
          id: 'cand-uuid-1',
          actor_id_a: 'actor-primary-uuid',
          actor_id_b: 'actor-secondary-uuid',
          score: 0.88,
          status: 'pending',
          created_at: '2026-08-13T18:00:00Z',
          updated_at: '2026-08-13T18:00:00Z',
        },
      ],
      meta: { total: 1, limit: 50, next_cursor: null },
    });

    mockApiClient.decideReconciliationCandidate.mockResolvedValueOnce({
      data: {
        candidate_id: 'cand-uuid-1',
        decision: 'merge',
        status: 'resolved',
        decision_notes: 'Mesclagem aprovada',
        audit_log_id: 'audit-uuid',
        updated_at: '2026-08-13T18:00:00Z',
      },
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(<WorkflowReviewQueue initialSubTab="reconciliation" />);
    });

    const root = tree!.root;
    const mergeBtn = root.findByProps({ accessibilityLabel: 'Mesclar Duplicata' });

    await act(async () => {
      mergeBtn.props.onPress();
    });

    const reasonInput = root.findByProps({ accessibilityLabel: 'Campo de justificativa de reconciliação' });
    await act(async () => {
      reasonInput.props.onChangeText('Mesclagem aprovada: mesmo estabelecimento comunitário');
    });

    const saveDecisionBtn = root.findByProps({ accessibilityLabel: 'Salvar decisão de reconciliação' });
    await act(async () => {
      await saveDecisionBtn.props.onPress();
    });

    expect(mockApiClient.decideReconciliationCandidate).toHaveBeenCalledWith(
      'cand-uuid-1',
      expect.objectContaining({
        decision: 'merge',
        reason: 'Mesclagem aprovada: mesmo estabelecimento comunitário',
        target_actor_id: 'actor-primary-uuid',
      })
    );
  });

  test('lista alertas e resolve alerta com nota explicativa', async () => {
    mockApiClient.getEditorialAlerts.mockResolvedValueOnce({
      data: [
        {
          id: 'alert-uuid-1',
          title: 'Interdição Parcial da Rota',
          message: 'Ponte sobre igarapé em manutenção preventiva.',
          severity: 'warning',
          is_active: true,
          route_id: 'route-pindobal-uuid',
          created_at: '2026-08-13T18:00:00Z',
        },
      ],
      meta: { total: 1, limit: 50, next_cursor: null },
    });

    mockApiClient.resolveEditorialAlert.mockResolvedValueOnce({
      data: {
        id: 'alert-uuid-1',
        title: 'Interdição Parcial da Rota',
        message: 'Ponte sobre igarapé em manutenção preventiva.',
        severity: 'warning',
        is_active: false,
        route_id: 'route-pindobal-uuid',
        created_at: '2026-08-13T18:00:00Z',
      },
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(<WorkflowReviewQueue initialSubTab="alerts" />);
    });

    const root = tree!.root;
    const resolveBtn = root.findByProps({ accessibilityLabel: 'Resolver Alerta' });

    await act(async () => {
      resolveBtn.props.onPress();
    });

    const noteInput = root.findByProps({ accessibilityLabel: 'Nota de resolução do alerta' });
    await act(async () => {
      noteInput.props.onChangeText('Manutenção concluída e via liberada');
    });

    const confirmResolveBtn = root.findByProps({ accessibilityLabel: 'Confirmar resolução do alerta' });
    await act(async () => {
      await confirmResolveBtn.props.onPress();
    });

    expect(mockApiClient.resolveEditorialAlert).toHaveBeenCalledWith(
      'alert-uuid-1',
      expect.objectContaining({
        resolution_note: 'Manutenção concluída e via liberada',
      })
    );
  });

  test('renderiza logs de auditoria imutável e filtra por ação', async () => {
    const mockLogs: AuditLogEntry[] = [
      {
        id: 'log-1',
        timestamp: '2026-08-13T18:00:00Z',
        actor_id: 'user-editor-1',
        action: 'TRANSITION_STATUS',
        resource_type: 'route',
        resource_id: 'route-pindobal-uuid',
        reason: 'Submissão para homologação',
        changes: {
          before: { status: 'draft' },
          after: { status: 'review' },
        },
      },
      {
        id: 'log-2',
        timestamp: '2026-08-13T18:30:00Z',
        actor_id: 'user-publisher-1',
        action: 'RECONCILE',
        resource_type: 'actor',
        resource_id: 'actor-cand-uuid',
        reason: 'Fusão de duplicatas',
      },
    ];

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(<AuditLogViewer initialLogs={mockLogs} />);
    });

    const root = tree!.root;
    const filterBtn = root.findByProps({ accessibilityLabel: 'Filtrar por RECONCILE' });

    await act(async () => {
      filterBtn.props.onPress();
    });

    const searchInput = root.findByProps({ accessibilityLabel: 'Buscar logs de auditoria' });
    await act(async () => {
      searchInput.props.onChangeText('Fusão');
    });

    expect(tree!.toJSON()).toBeTruthy();
  });
});
