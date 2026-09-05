import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { TouchableOpacity, Text, Modal, Alert, AccessibilityInfo } from 'react-native';
import * as Linking from 'expo-linking';
import * as Location from 'expo-location';
import { OriginSelector, MY_LOCATION_ORIGIN_ID } from './OriginSelector';
import * as LocationConsent from '../../auth/locationConsent';

jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

jest.mock('../../auth/locationConsent', () => ({
  hasValidLocationConsent: jest.fn(),
  saveLocationConsent: jest.fn(),
  revokeLocationConsent: jest.fn(),
  CURRENT_LOCATION_POLICY_VERSION: '2026-09-04',
}));

jest.mock('expo-linking', () => ({
  openSettings: jest.fn(),
}));

const mockOrigins = [
  {
    id: 'origin-porto',
    route_id: 'route-1',
    code: 'porto',
    name: 'Porto Fluvial',
    description: 'Ponto de partida no porto',
    distance_m: 12000,
    duration_s: 900,
    actor_count: 5,
  },
  {
    id: 'origin-aeroporto',
    route_id: 'route-1',
    code: 'aeroporto',
    name: 'Aeroporto',
    description: 'Ponto de partida no aeroporto',
    distance_m: 35000,
    duration_s: 2400,
    actor_count: 8,
  },
  {
    id: 'origin-rodoviaria',
    route_id: 'route-1',
    code: 'rodoviaria',
    name: 'Rodoviária',
    description: 'Ponto de partida na rodoviária',
    distance_m: 28000,
    duration_s: 1800,
    actor_count: 6,
  },
];

describe('OriginSelector Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    jest.spyOn(Alert, 'alert');
    jest.spyOn(AccessibilityInfo, 'announceForAccessibility');
    (LocationConsent.hasValidLocationConsent as jest.Mock).mockResolvedValue(true);
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
  });

  describe('Feature Flag Fail-Closed and Dynamic Routing Control', () => {
    it('fails closed when enableDynamicRouting is undefined (omitted): hides both "Minha localização" and "Escolher no mapa" and renders only fixed origins', () => {
      const onSelectOrigin = jest.fn();
      const onStartSelectOnMap = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            onStartSelectOnMap={onStartSelectOnMap}
          />
        );
      });

      const buttons = root!.root.findAllByType(TouchableOpacity);
      // Only 3 fixed origins should be rendered (neither GPS nor Map selection pill)
      expect(buttons.length).toBe(3);

      const gpsButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Usar minha localização atual como origem'
      );
      expect(gpsButton).toBeUndefined();

      const mapButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Escolher ponto de partida no mapa'
      );
      expect(mapButton).toBeUndefined();

      const portoButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Selecionar origem Porto Fluvial'
      );
      expect(portoButton).toBeDefined();
      expect(portoButton?.props.accessibilityState).toEqual({ selected: true });

      const aeroportoButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Selecionar origem Aeroporto'
      );
      expect(aeroportoButton).toBeDefined();

      const rodoviariaButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Selecionar origem Rodoviária'
      );
      expect(rodoviariaButton).toBeDefined();
    });

    it('hides both "Minha localização" and "Escolher no mapa" when enableDynamicRouting is explicitly false', () => {
      const onSelectOrigin = jest.fn();
      const onStartSelectOnMap = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            onStartSelectOnMap={onStartSelectOnMap}
            enableDynamicRouting={false}
          />
        );
      });

      const buttons = root!.root.findAllByType(TouchableOpacity);
      expect(buttons.length).toBe(3);

      const gpsButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Usar minha localização atual como origem'
      );
      expect(gpsButton).toBeUndefined();

      const mapButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Escolher ponto de partida no mapa'
      );
      expect(mapButton).toBeUndefined();
    });

    it('renders all three fixed origins, "Minha localização" pill, and "Escolher no mapa" pill when enableDynamicRouting is true', () => {
      const onSelectOrigin = jest.fn();
      const onStartSelectOnMap = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            onStartSelectOnMap={onStartSelectOnMap}
            enableDynamicRouting={true}
          />
        );
      });

      const buttons = root!.root.findAllByType(TouchableOpacity);
      // 1 for GPS pill + 1 for map selection pill + 3 for fixed origins = 5 pills
      expect(buttons.length).toBe(5);

      const gpsButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Usar minha localização atual como origem'
      );
      expect(gpsButton).toBeDefined();

      const mapButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Escolher ponto de partida no mapa'
      );
      expect(mapButton).toBeDefined();

      const portoButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Selecionar origem Porto Fluvial'
      );
      expect(portoButton).toBeDefined();
      expect(portoButton?.props.accessibilityState).toEqual({ selected: true });
    });
  });

  describe('Fixed Origins Selection', () => {
    it('clicking a fixed origin triggers onSelectOrigin callback for all 3 fixed origins', () => {
      const onSelectOrigin = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            enableDynamicRouting={true}
          />
        );
      });

      const aeroportoButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Selecionar origem Aeroporto'
      );
      act(() => {
        aeroportoButton?.props.onPress();
      });
      expect(onSelectOrigin).toHaveBeenCalledWith('origin-aeroporto');

      const rodoviariaButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Selecionar origem Rodoviária'
      );
      act(() => {
        rodoviariaButton?.props.onPress();
      });
      expect(onSelectOrigin).toHaveBeenCalledWith('origin-rodoviaria');
    });
  });

  describe('GPS / Minha Localização Flow (when enabled)', () => {
    it('clicking "Minha localização" requests GPS and opens confirmation modal with accessible dialog properties', async () => {
      (Location.hasServicesEnabledAsync as jest.Mock).mockResolvedValue(true);
      (Location.getForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
        status: Location.PermissionStatus.GRANTED,
        canAskAgain: true,
      });
      (Location.getCurrentPositionAsync as jest.Mock).mockResolvedValue({
        coords: {
          latitude: -2.4431,
          longitude: -54.7083,
          accuracy: 10,
        },
      });

      const onSelectOrigin = jest.fn();
      const onSelectCurrentLocation = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            onSelectCurrentLocation={onSelectCurrentLocation}
            enableDynamicRouting={true}
          />
        );
      });

      const gpsButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Usar minha localização atual como origem'
      );

      await act(async () => {
        await gpsButton?.props.onPress();
      });

      // Screen reader announcement on fetch and success
      expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(
        expect.stringContaining('Obtendo sua localização')
      );
      expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(
        expect.stringContaining('Localização obtida com sucesso')
      );

      // Confirmation modal should be visible and accessible
      const modals = root!.root.findAllByType(Modal);
      const confirmModal = modals.find((m) => m.props.accessibilityLabel === 'Confirmar cálculo de trajeto') || modals[0];
      expect(confirmModal.props.visible).toBe(true);

      const dialogContainer = root!.root.findAllByProps({ accessibilityRole: 'alert' });
      expect(dialogContainer.length).toBeGreaterThan(0);

      const modalOverlay = root!.root.findAllByProps({ accessibilityViewIsModal: true });
      expect(modalOverlay.length).toBeGreaterThan(0);

      // Confirm button click
      const confirmButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Confirmar cálculo do trajeto sugerido'
      );
      expect(confirmButton).toBeDefined();

      act(() => {
        confirmButton?.props.onPress();
      });

      expect(onSelectCurrentLocation).toHaveBeenCalledWith({
        latitude: -2.4431,
        longitude: -54.7083,
        accuracy: 10,
      });
      expect(onSelectOrigin).toHaveBeenCalledWith(MY_LOCATION_ORIGIN_ID);
      expect(confirmModal.props.visible).toBe(false);
    });

    it('cancelling the confirmation modal closes dialog, clears pending coords, and announces cancellation', async () => {
      (Location.hasServicesEnabledAsync as jest.Mock).mockResolvedValue(true);
      (Location.getForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
        status: Location.PermissionStatus.GRANTED,
        canAskAgain: true,
      });
      (Location.getCurrentPositionAsync as jest.Mock).mockResolvedValue({
        coords: {
          latitude: -2.4431,
          longitude: -54.7083,
          accuracy: 10,
        },
      });

      const onSelectOrigin = jest.fn();
      const onSelectCurrentLocation = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            onSelectCurrentLocation={onSelectCurrentLocation}
            enableDynamicRouting={true}
          />
        );
      });

      const gpsButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Usar minha localização atual como origem'
      );

      await act(async () => {
        await gpsButton?.props.onPress();
      });

      const cancelButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Cancelar cálculo a partir da minha localização'
      );

      act(() => {
        cancelButton?.props.onPress();
      });

      expect(onSelectCurrentLocation).not.toHaveBeenCalled();
      const modals = root!.root.findAllByType(Modal);
      const confirmModal = modals.find((m) => m.props.accessibilityLabel === 'Confirmar cálculo de trajeto') || modals[0];
      expect(confirmModal.props.visible).toBe(false);
      expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith(
        expect.stringContaining('cancelado')
      );
    });

    it('handles permanently denied permission by presenting Settings action and screen reader message', async () => {
      (Location.hasServicesEnabledAsync as jest.Mock).mockResolvedValue(true);
      (Location.getForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
        status: Location.PermissionStatus.DENIED,
        canAskAgain: false,
      });

      const onSelectOrigin = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            enableDynamicRouting={true}
          />
        );
      });

      const gpsButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Usar minha localização atual como origem'
      );

      await act(async () => {
        await gpsButton?.props.onPress();
      });

      expect(Alert.alert).toHaveBeenCalledWith(
        'Permissão Necessária',
        expect.stringContaining('configurações do aplicativo'),
        expect.arrayContaining([
          expect.objectContaining({ text: 'Agora não' }),
          expect.objectContaining({ text: 'Abrir Configurações' }),
        ])
      );

      // Trigger settings button
      const alertCalls = (Alert.alert as jest.Mock).mock.calls;
      const settingsButton = alertCalls[0][2].find((btn: any) => btn.text === 'Abrir Configurações');
      settingsButton.onPress();
      expect(Linking.openSettings).toHaveBeenCalledTimes(1);
    });
  });

  describe('LGPD Location Consent Gate in OriginSelector', () => {
    it('intercepts GPS press and shows consent modal when consent is not present, without calling Location API', async () => {
      (LocationConsent.hasValidLocationConsent as jest.Mock).mockResolvedValue(false);
      const onSelectOrigin = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            enableDynamicRouting={true}
          />
        );
      });

      const gpsButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Usar minha localização atual como origem'
      );

      await act(async () => {
        await gpsButton?.props.onPress();
      });

      // Crucial LGPD compliance: Location API must NOT have been called before consent!
      expect(Location.requestForegroundPermissionsAsync).not.toHaveBeenCalled();
      expect(Location.getCurrentPositionAsync).not.toHaveBeenCalled();

      // Consent modal should be visible
      const consentDialog = root!.root.findByProps({
        accessibilityLabel: 'Consentimento de localização dinâmica',
      });
      expect(consentDialog).toBeDefined();
    });

    it('intercepts Choose on Map press and shows consent modal when consent is missing', async () => {
      (LocationConsent.hasValidLocationConsent as jest.Mock).mockResolvedValue(false);
      const onStartSelectOnMap = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={jest.fn()}
            onStartSelectOnMap={onStartSelectOnMap}
            enableDynamicRouting={true}
          />
        );
      });

      const mapButton = root!.root.findAllByType(TouchableOpacity).find(
        (b) => b.props.accessibilityLabel === 'Escolher ponto de partida no mapa'
      );

      await act(async () => {
        await mapButton?.props.onPress();
      });

      expect(onStartSelectOnMap).not.toHaveBeenCalled();

      const consentDialog = root!.root.findByProps({
        accessibilityLabel: 'Consentimento de localização dinâmica',
      });
      expect(consentDialog).toBeDefined();
    });
  });

  describe('Component Preparation for ECO-2311 and Lifecycle', () => {
    it('renders "Escolher no mapa" pill and triggers onStartSelectOnMap (ECO-2311)', async () => {
      (LocationConsent.hasValidLocationConsent as jest.Mock).mockResolvedValue(true);
      const onSelectOrigin = jest.fn();
      const onStartSelectOnMap = jest.fn();
      let root: renderer.ReactTestRenderer;

      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={onSelectOrigin}
            onStartSelectOnMap={onStartSelectOnMap}
            enableDynamicRouting={true}
          />
        );
      });

      const buttons = root!.root.findAllByType(TouchableOpacity);
      expect(buttons.length).toBe(5);

      const mapButton = buttons.find(
        (b) => b.props.accessibilityLabel === 'Escolher ponto de partida no mapa'
      );
      expect(mapButton).toBeDefined();

      await act(async () => {
        await mapButton?.props.onPress();
      });

      expect(onStartSelectOnMap).toHaveBeenCalled();
    });

    it('unmounts cleanly without errors or dangling timers', () => {
      let root: renderer.ReactTestRenderer;
      act(() => {
        root = renderer.create(
          <OriginSelector
            origins={mockOrigins}
            selectedOriginId="origin-porto"
            onSelectOrigin={jest.fn()}
            enableDynamicRouting={true}
          />
        );
      });

      expect(() => {
        act(() => {
          root.unmount();
        });
      }).not.toThrow();
    });
  });
});
