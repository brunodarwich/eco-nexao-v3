import React from 'react';
import renderer, { act } from 'react-test-renderer';

import AdminIndexScreen from '../../../app/admin';
import { ApiClientError } from '../../api/client';
import { useAdminContextQuery } from '../../hooks/queries';
import { useAuth } from '../../hooks/useAuth';

const mockReplace = jest.fn();

jest.mock('expo-router', () => ({
  router: { replace: (...args: unknown[]) => mockReplace(...args) },
}));

jest.mock('../../api/client', () => ({
  apiClient: {
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

jest.mock('../../hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('../../hooks/queries', () => ({ useAdminContextQuery: jest.fn() }));

const mockUseAuth = useAuth as jest.Mock;
const mockUseAdminContextQuery = useAdminContextQuery as jest.Mock;

describe('ECO-1801 — rota editorial', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({ status: 'authenticated', signOut: jest.fn() });
  });

  test('bloqueia na UI quando a autoridade backend nega o contexto editorial (403)', async () => {
    mockUseAdminContextQuery.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new ApiClientError('Acesso proibido', 403, 'FORBIDDEN'),
      refetch: jest.fn(),
    });

    let tree: renderer.ReactTestRenderer | undefined;
    await act(async () => {
      tree = renderer.create(<AdminIndexScreen />);
    });

    const content = tree!.root
      .findAllByType('Text' as never)
      .flatMap((node) => node.props.children)
      .join(' ');
    expect(content).toContain('Acesso Negado (403)');
  });

  test('renderiza o shell na rota e encerra a sessão editorial', async () => {
    const signOut = jest.fn().mockResolvedValue(undefined);
    mockUseAuth.mockReturnValue({ status: 'authenticated', signOut });
    mockUseAdminContextQuery.mockReturnValue({
      data: {
        access: {
          user_id: 'publisher-1',
          scopes: [
            {
              scope_type: 'global',
              roles: ['publisher'],
              capabilities: ['content.publish', 'content.archive'],
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
      tree = renderer.create(<AdminIndexScreen />);
    });

    const logout = tree!.root.findByProps({ accessibilityLabel: 'Encerrar sessão editorial' });
    await act(async () => {
      logout.props.onPress();
      await signOut.mock.results[0].value;
    });

    expect(signOut).toHaveBeenCalledTimes(1);
    expect(mockReplace).toHaveBeenCalledWith('/(tabs)');
  });
});

