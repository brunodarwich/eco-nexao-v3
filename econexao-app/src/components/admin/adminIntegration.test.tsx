import React from 'react';
import renderer, { act } from 'react-test-renderer';

import { ApiClientError } from '../../api/client';
import { useAdminContextQuery } from '../../hooks/queries';
import { AccessDeniedView } from './AccessDeniedView';
import { AdminCapabilityGate } from './AdminCapabilityGate';
import { AdminShell } from './AdminShell';

jest.mock('../../api/client', () => ({
  apiClient: {
    configureAuth: jest.fn(),
    getAdminRegions: jest.fn().mockResolvedValue({ data: [] }),
    getAdminRoutes: jest.fn().mockResolvedValue({ data: [] }),
    getAdminActors: jest.fn().mockResolvedValue({ data: [] }),
  },
  ApiClientError: class extends Error {
    public status: number;
    public code: string;
    constructor(message: string, status: number, code: string = 'API_ERROR') {
      super(message);
      this.status = status;
      this.code = code;
    }
  },
}));

jest.mock('../../hooks/queries', () => ({
  useAdminContextQuery: jest.fn(),
}));

const mockUseAdminContextQuery = useAdminContextQuery as jest.Mock;

describe('Marco 18 — Admin Shell & Capability Gate Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders AccessDeniedView with title and message when 403 occurs', () => {
    let tree: renderer.ReactTestRenderer | undefined;
    act(() => {
      tree = renderer.create(
        <AccessDeniedView
          title="Acesso Negado (403)"
          message="Credenciais insuficientes."
          onGoHome={jest.fn()}
        />
      );
    });

    const instance = tree!.root;
    const textNodes = instance.findAllByType('Text' as any);
    const content = textNodes.map((n) => n.props.children).flat().join(' ');

    expect(content).toContain('Acesso Negado (403)');
    expect(content).toContain('Credenciais insuficientes.');
  });

  test('AdminCapabilityGate renders loading progressbar when isLoading is true', () => {
    mockUseAdminContextQuery.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      refetch: jest.fn(),
    });

    let tree: renderer.ReactTestRenderer | undefined;
    act(() => {
      tree = renderer.create(
        <AdminCapabilityGate requiredCapability="territory.write">
          <div>Conteúdo Protegido</div>
        </AdminCapabilityGate>
      );
    });

    const progressBar = tree!.root.findByProps({ accessibilityRole: 'progressbar' });
    expect(progressBar).toBeTruthy();
    expect(progressBar.props.accessibilityLabel).toContain('Verificando permissões editoriais...');
  });

  test('AdminCapabilityGate renders AccessDeniedView for 403 ApiClientError', () => {
    mockUseAdminContextQuery.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new ApiClientError('Forbidden', 403, 'FORBIDDEN'),
      refetch: jest.fn(),
    });

    let tree: renderer.ReactTestRenderer | undefined;
    act(() => {
      tree = renderer.create(
        <AdminCapabilityGate requiredCapability="territory.write">
          <div>Conteúdo Protegido</div>
        </AdminCapabilityGate>
      );
    });

    const instance = tree!.root;
    const textNodes = instance.findAllByType('Text' as any);
    const content = textNodes.map((n) => n.props.children).flat().join(' ');

    expect(content).toContain('Acesso Negado (403)');
  });

  test('AdminCapabilityGate renders recoverable connection error view on 500/network error and triggers retry', () => {
    const mockRefetch = jest.fn();
    mockUseAdminContextQuery.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new ApiClientError('Internal Server Error', 500, 'INTERNAL_ERROR'),
      refetch: mockRefetch,
    });

    let tree: renderer.ReactTestRenderer | undefined;
    act(() => {
      tree = renderer.create(
        <AdminCapabilityGate requiredCapability="territory.write">
          <div>Conteúdo Protegido</div>
        </AdminCapabilityGate>
      );
    });

    const instance = tree!.root;
    const textNodes = instance.findAllByType('Text' as any);
    const content = textNodes.map((n) => n.props.children).flat().join(' ');

    expect(content).toContain('Erro de Conexão Editorial');
    expect(content).toContain('FALHA DE CONEXÃO');

    const retryButton = instance.findByProps({ accessibilityLabel: 'Tentar reconectar com o servidor editorial' });
    act(() => {
      retryButton.props.onPress();
    });

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  test('AdminCapabilityGate renders children when capability matches', () => {
    mockUseAdminContextQuery.mockReturnValue({
      data: {
        access: {
          user_id: 'user-editor',
          scopes: [
            {
              scope_type: 'global',
              roles: ['editor'],
              capabilities: ['territory.write', 'territory.read'],
            },
          ],
        },
      },
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
    });

    let tree: renderer.ReactTestRenderer | undefined;
    act(() => {
      tree = renderer.create(
        <AdminCapabilityGate requiredCapability="territory.write">
          <AccessDeniedView title="Área Autorizada" message="Bem-vindo editor!" />
        </AdminCapabilityGate>
      );
    });

    const instance = tree!.root;
    const textNodes = instance.findAllByType('Text' as any);
    const content = textNodes.map((n) => n.props.children).flat().join(' ');

    expect(content).toContain('Área Autorizada');
    expect(content).toContain('Bem-vindo editor!');
  });

  test('AdminShell renders header and dynamic nav tabs with accessibility attributes', async () => {
    mockUseAdminContextQuery.mockReturnValue({
      data: {
        access: {
          user_id: 'user-admin',
          scopes: [
            {
              scope_type: 'global',
              roles: ['admin'],
              capabilities: [
                'territory.read',
                'territory.write',
                'actor.write',
                'content.publish',
                'content.archive',
              ],
            },
          ],
        },
      },
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(
        <AdminShell isAuthenticated={true} onGoHome={jest.fn()} onLogout={jest.fn()} />
      );
    });

    const instance = tree!.root;
    const textNodes = instance.findAllByType('Text' as any);
    const content = textNodes.map((n) => n.props.children).flat().join(' ');

    expect(content).toContain('ECOconexão Editorial');
    expect(content).toContain('ADMIN');
    expect(content).toContain('Território & Rotas');
    expect(content).toContain('Atores');
    expect(content).toContain('Fila de Revisão');
    expect(content).toContain('Auditoria');

    const territoryTab = instance.findByProps({ accessibilityLabel: 'Acessar gestão de território e rotas' });
    expect(territoryTab.props.accessibilityRole).toBe('tab');
    expect(territoryTab.props.accessibilityState).toEqual({ selected: true });

    const actorsTab = instance.findByProps({ accessibilityLabel: 'Acessar gestão de atores e estabelecimentos' });
    expect(actorsTab.props.accessibilityRole).toBe('tab');
    expect(actorsTab.props.accessibilityState).toEqual({ selected: false });

    const reviewTab = instance.findByProps({ accessibilityLabel: 'Acessar fila de revisão e publicação' });
    expect(reviewTab.props.accessibilityRole).toBe('tab');
    expect(reviewTab.props.accessibilityState).toEqual({ selected: false });

    const auditTab = instance.findByProps({ accessibilityLabel: 'Acessar auditoria e logs do sistema' });
    expect(auditTab.props.accessibilityRole).toBe('tab');
    expect(auditTab.props.accessibilityState).toEqual({ selected: false });
  });
});


