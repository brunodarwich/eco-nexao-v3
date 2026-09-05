import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { TouchableOpacity, Text, AccessibilityInfo } from 'react-native';
import { DynamicLocationConsentModal } from './DynamicLocationConsentModal';
import * as LocationConsent from '../../auth/locationConsent';

jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

describe('DynamicLocationConsentModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    jest.spyOn(AccessibilityInfo, 'announceForAccessibility');
    jest.spyOn(LocationConsent, 'saveLocationConsent').mockResolvedValue(true);
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
  });

  it('renders with both checkboxes unchecked by default and continue button disabled', () => {
    let root: renderer.ReactTestRenderer;
    act(() => {
      root = renderer.create(
        <DynamicLocationConsentModal
          visible={true}
          onConsentSuccess={jest.fn()}
          onCancelFixedOrigin={jest.fn()}
        />
      );
    });

    const checkboxes = root!.root.findAllByType(TouchableOpacity).filter(
      (b) => b.props.accessibilityRole === 'checkbox'
    );
    expect(checkboxes.length).toBe(2);

    // Both checkboxes must be unchecked
    expect(checkboxes[0].props.accessibilityState.checked).toBe(false);
    expect(checkboxes[1].props.accessibilityState.checked).toBe(false);

    // Continue button must be disabled
    const continueBtn = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Concordar e continuar'
    );
    expect(continueBtn).toBeDefined();
    expect(continueBtn?.props.disabled).toBe(true);
  });

  it('blocks continuation if only adult is checked', () => {
    let root: renderer.ReactTestRenderer;
    act(() => {
      root = renderer.create(
        <DynamicLocationConsentModal
          visible={true}
          onConsentSuccess={jest.fn()}
          onCancelFixedOrigin={jest.fn()}
        />
      );
    });

    const adultCheckbox = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Declaro que tenho 18 anos ou mais.'
    );
    act(() => {
      adultCheckbox?.props.onPress();
    });

    const continueBtn = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Concordar e continuar'
    );
    expect(continueBtn?.props.disabled).toBe(true);
  });

  it('blocks continuation if only LGPD consent is checked', () => {
    let root: renderer.ReactTestRenderer;
    act(() => {
      root = renderer.create(
        <DynamicLocationConsentModal
          visible={true}
          onConsentSuccess={jest.fn()}
          onCancelFixedOrigin={jest.fn()}
        />
      );
    });

    const lgpdCheckbox = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Li e concordo com o tratamento temporário da minha localização para calcular este trajeto.'
    );
    act(() => {
      lgpdCheckbox?.props.onPress();
    });

    const continueBtn = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Concordar e continuar'
    );
    expect(continueBtn?.props.disabled).toBe(true);
  });

  it('enables continuation when both are checked and calls saveLocationConsent', async () => {
    const onConsentSuccess = jest.fn();
    let root: renderer.ReactTestRenderer;
    act(() => {
      root = renderer.create(
        <DynamicLocationConsentModal
          visible={true}
          onConsentSuccess={onConsentSuccess}
          onCancelFixedOrigin={jest.fn()}
        />
      );
    });

    const adultCheckbox = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Declaro que tenho 18 anos ou mais.'
    );
    const lgpdCheckbox = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Li e concordo com o tratamento temporário da minha localização para calcular este trajeto.'
    );

    act(() => {
      adultCheckbox?.props.onPress();
      lgpdCheckbox?.props.onPress();
    });

    const continueBtn = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Concordar e continuar'
    );
    expect(continueBtn?.props.disabled).toBeFalsy();

    await act(async () => {
      await continueBtn?.props.onPress();
    });

    expect(LocationConsent.saveLocationConsent).toHaveBeenCalledWith(true, true);
    expect(onConsentSuccess).toHaveBeenCalled();
  });

  it('allows cancelling and returning to fixed origins', () => {
    const onCancelFixedOrigin = jest.fn();
    let root: renderer.ReactTestRenderer;
    act(() => {
      root = renderer.create(
        <DynamicLocationConsentModal
          visible={true}
          onConsentSuccess={jest.fn()}
          onCancelFixedOrigin={onCancelFixedOrigin}
        />
      );
    });

    const cancelBtn = root!.root.findAllByType(TouchableOpacity).find(
      (b) => b.props.accessibilityLabel === 'Cancelar e usar origem fixa'
    );
    expect(cancelBtn).toBeDefined();

    act(() => {
      cancelBtn?.props.onPress();
    });

    expect(onCancelFixedOrigin).toHaveBeenCalled();
  });
});
