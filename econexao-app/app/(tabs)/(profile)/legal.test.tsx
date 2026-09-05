import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { TouchableOpacity, Text, Modal, AccessibilityInfo } from 'react-native';
import LegalAndPrivacyScreen from './legal';
import * as LocationConsent from '../../../src/auth/locationConsent';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

jest.mock('../../../src/hooks/useApp', () => ({
  useApp: () => ({
    state: { activeRegionId: 'pindobal' },
    activeRegion: { id: 'pindobal', name: 'Pindobal' },
    openRegionSelector: jest.fn(),
  }),
}));

jest.mock('../../../src/hooks/queries', () => ({
  useRegionsQuery: () => ({
    data: [{ id: 'pindobal', name: 'Pindobal' }],
    isPending: false,
    isError: false,
  }),
}));

const mockBack = jest.fn();
jest.mock('expo-router', () => ({
  useRouter: () => ({
    back: mockBack,
    push: jest.fn(),
  }),
}));

jest.mock('expo-linking', () => ({
  openURL: jest.fn(),
  createURL: jest.fn((path: string) => `mocked://${path}`),
}));

describe('LegalAndPrivacyScreen Component (ECO-2314 LGPD Revocation Flow)', () => {
  let queryClient: QueryClient;

  const renderComponent = async () => {
    let root: renderer.ReactTestRenderer;
    await act(async () => {
      root = renderer.create(
        <QueryClientProvider client={queryClient}>
          <LegalAndPrivacyScreen />
        </QueryClientProvider>
      );
    });
    return root!;
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: Infinity },
        mutations: { retry: false, gcTime: Infinity },
      },
    });
    jest.clearAllMocks();
    jest.useFakeTimers();
    jest.spyOn(AccessibilityInfo, 'announceForAccessibility');
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
    queryClient.clear();
  });

  it('renders inactive status when no consent exists in storage and hides revoke button', async () => {
    jest.spyOn(LocationConsent, 'hasValidLocationConsent').mockResolvedValue(false);

    const root = await renderComponent();

    const texts = root!.root.findAllByType(Text).map((t) => t.props.children);
    const hasInactiveText = texts.some(
      (txt) => typeof txt === 'string' && txt.includes('Nenhum consentimento de localização ativo')
    );
    expect(hasInactiveText).toBe(true);

    const revokeButtons = root!.root.findAllByType(TouchableOpacity).filter(
      (b) => b.props.accessibilityLabel === 'Revogar consentimento de localização dinâmica'
    );
    expect(revokeButtons.length).toBe(0);
  });

  it('renders active status when consent exists in storage and displays revoke button', async () => {
    jest.spyOn(LocationConsent, 'hasValidLocationConsent').mockResolvedValue(true);

    const root = await renderComponent();

    const texts = root.root.findAllByType(Text).map((t) => t.props.children);
    const hasActiveText = texts.some(
      (txt) => typeof txt === 'string' && txt.includes('Consentimento de localização ativo')
    );
    expect(hasActiveText).toBe(true);

    const revokeButtons = root.root.findAllByType(TouchableOpacity).filter(
      (b) => b.props.accessibilityLabel === 'Revogar consentimento de localização dinâmica'
    );
    expect(revokeButtons.length).toBe(1);
  });

  const getRevokeModal = (root: renderer.ReactTestRenderer) => {
    const modals = root.root.findAllByType(Modal);
    return modals.find((m) => m.props.accessibilityLabel === 'Confirmar revogação de consentimento de localização') || modals[modals.length - 1];
  };

  it('opens accessible confirmation modal when clicking revoke button', async () => {
    jest.spyOn(LocationConsent, 'hasValidLocationConsent').mockResolvedValue(true);

    const root = await renderComponent();

    // Modal initially closed
    let modal = getRevokeModal(root);
    expect(modal.props.visible).toBe(false);

    const revokeBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Revogar consentimento de localização dinâmica'
    );

    act(() => {
      revokeBtn?.props.onPress();
    });

    modal = getRevokeModal(root);
    expect(modal.props.visible).toBe(true);

    const dialogCard = root.root.findByProps({
      accessibilityLabel: 'Modal de confirmação de revogação de consentimento',
    });
    expect(dialogCard).toBeDefined();
  });

  it('cancelling revocation closes modal, preserves active consent, and announces cancellation', async () => {
    jest.spyOn(LocationConsent, 'hasValidLocationConsent').mockResolvedValue(true);
    const revokeSpy = jest.spyOn(LocationConsent, 'revokeLocationConsent');

    const root = await renderComponent();

    const revokeBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Revogar consentimento de localização dinâmica'
    );
    act(() => {
      revokeBtn?.props.onPress();
    });

    const modalCancelBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Cancelar revogação'
    );
    expect(modalCancelBtn).toBeDefined();

    act(() => {
      modalCancelBtn?.props.onPress();
    });

    const modal = getRevokeModal(root);
    expect(modal.props.visible).toBe(false);
    expect(revokeSpy).not.toHaveBeenCalled();

    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(
      expect.stringContaining('Revogação cancelada. Consentimento mantido.')
    );

    // Consent status should remain active
    const texts = root.root.findAllByType(Text).map((t) => t.props.children);
    expect(texts.some((txt) => typeof txt === 'string' && txt.includes('Consentimento de localização ativo'))).toBe(true);
  });

  it('successful confirmation removes consent from storage, updates UI to inactive, and announces success', async () => {
    jest.spyOn(LocationConsent, 'hasValidLocationConsent').mockResolvedValue(true);
    const revokeSpy = jest.spyOn(LocationConsent, 'revokeLocationConsent').mockResolvedValue(true);

    const root = await renderComponent();

    const revokeBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Revogar consentimento de localização dinâmica'
    );
    act(() => {
      revokeBtn?.props.onPress();
    });

    const confirmRevokeBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Confirmar revogação'
    );
    expect(confirmRevokeBtn).toBeDefined();

    await act(async () => {
      await confirmRevokeBtn?.props.onPress();
    });

    expect(revokeSpy).toHaveBeenCalledTimes(1);

    const modal = getRevokeModal(root);
    expect(modal.props.visible).toBe(false);

    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(
      expect.stringContaining('Consentimento de localização revogado com sucesso')
    );

    // Consent status should now be inactive
    const texts = root.root.findAllByType(Text).map((t) => t.props.children);
    expect(texts.some((txt) => typeof txt === 'string' && txt.includes('Nenhum consentimento de localização ativo'))).toBe(true);
  });

  it('storage failure displays accessible alert role, keeps consent active, does not announce success, and allows retry', async () => {
    jest.spyOn(LocationConsent, 'hasValidLocationConsent').mockResolvedValue(true);
    const revokeSpy = jest.spyOn(LocationConsent, 'revokeLocationConsent')
      .mockResolvedValueOnce(false)
      .mockResolvedValueOnce(true);

    const root = await renderComponent();

    // Open modal
    const revokeBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Revogar consentimento de localização dinâmica'
    );
    act(() => {
      revokeBtn?.props.onPress();
    });

    const confirmRevokeBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Confirmar revogação'
    );

    // 1st attempt fails
    await act(async () => {
      await confirmRevokeBtn?.props.onPress();
    });

    expect(revokeSpy).toHaveBeenCalledTimes(1);

    // Modal stays open
    const modal = getRevokeModal(root);
    expect(modal.props.visible).toBe(true);

    // Error alert is rendered with role="alert"
    const errorAlerts = root.root.findAllByProps({ accessibilityRole: 'alert' });
    expect(errorAlerts.length).toBeGreaterThan(0);

    // Error announcement made; success NOT announced
    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(
      expect.stringContaining('Erro ao revogar consentimento no armazenamento local')
    );
    expect(AccessibilityInfo.announceForAccessibility).not.toHaveBeenCalledWith(
      expect.stringContaining('Consentimento de localização revogado com sucesso')
    );

    // Retry button is now available
    const retryBtn = root.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Tentar novamente'
    );
    expect(retryBtn).toBeDefined();

    // 2nd attempt succeeds via retry
    await act(async () => {
      await retryBtn?.props.onPress();
    });

    expect(revokeSpy).toHaveBeenCalledTimes(2);
    const finalModal = getRevokeModal(root);
    expect(finalModal.props.visible).toBe(false);
    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(
      expect.stringContaining('Consentimento de localização revogado com sucesso')
    );

    // UI updated to inactive
    const texts = root.root.findAllByType(Text).map((t) => t.props.children);
    expect(texts.some((txt) => typeof txt === 'string' && txt.includes('Nenhum consentimento de localização ativo'))).toBe(true);
  });
});
