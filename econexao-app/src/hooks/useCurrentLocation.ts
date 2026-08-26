import { useState, useCallback, useRef, useEffect } from 'react';
import * as Location from 'expo-location';

export type LocationStateStatus =
  | 'idle'
  | 'requesting'
  | 'ready'
  | 'denied'
  | 'permanently_denied'
  | 'services_disabled'
  | 'timeout'
  | 'inaccurate'
  | 'error';

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy: number | null;
}

export interface LocationResult {
  success: boolean;
  status: LocationStateStatus;
  coords: LocationCoordinates | null;
  errorMessage: string | null;
  canAskAgain?: boolean;
}

export interface UseCurrentLocationState {
  status: LocationStateStatus;
  coords: LocationCoordinates | null;
  errorMessage: string | null;
  canAskAgain: boolean;
}

export interface UseCurrentLocationReturn extends UseCurrentLocationState {
  requestLocation: () => Promise<LocationResult>;
  resetLocation: () => void;
}

const ACCURACY_THRESHOLD_METERS = 1000;
const LOCATION_TIMEOUT_MS = 10000;

export function useCurrentLocation(): UseCurrentLocationReturn {
  const [state, setState] = useState<UseCurrentLocationState>({
    status: 'idle',
    coords: null,
    errorMessage: null,
    canAskAgain: true,
  });

  const isMountedRef = useRef(true);
  const isRequestingRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const resetLocation = useCallback(() => {
    if (!isMountedRef.current) return;
    setState({
      status: 'idle',
      coords: null,
      errorMessage: null,
      canAskAgain: true,
    });
  }, []);

  const requestLocation = useCallback(async (): Promise<LocationResult> => {
    if (isRequestingRef.current) {
      return {
        success: false,
        status: state.status,
        coords: state.coords,
        errorMessage: 'Uma solicitação de localização já está em andamento.',
        canAskAgain: state.canAskAgain,
      };
    }

    isRequestingRef.current = true;
    if (isMountedRef.current) {
      setState((prev) => ({
        ...prev,
        status: 'requesting',
        errorMessage: null,
      }));
    }

    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    try {
      // 1. Check if location services are enabled on the device
      const servicesEnabled = await Location.hasServicesEnabledAsync();
      if (!servicesEnabled) {
        const result: LocationResult = {
          success: false,
          status: 'services_disabled',
          coords: null,
          errorMessage: 'Os serviços de localização estão desativados no dispositivo.',
          canAskAgain: true,
        };
        if (isMountedRef.current) {
          setState({
            status: 'services_disabled',
            coords: null,
            errorMessage: result.errorMessage,
            canAskAgain: true,
          });
        }
        return result;
      }

      // 2. Check existing foreground permissions first
      let permissionResponse = await Location.getForegroundPermissionsAsync();

      // If not granted and can ask again, request foreground permission
      if (permissionResponse.status !== Location.PermissionStatus.GRANTED && permissionResponse.canAskAgain) {
        permissionResponse = await Location.requestForegroundPermissionsAsync();
      }

      if (permissionResponse.status !== Location.PermissionStatus.GRANTED) {
        const isPermanentlyDenied = !permissionResponse.canAskAgain;
        const resultStatus: LocationStateStatus = isPermanentlyDenied ? 'permanently_denied' : 'denied';
        const errorMsg = isPermanentlyDenied
          ? 'Permissão de localização bloqueada. Por favor, habilite nas configurações do aparelho.'
          : 'Permissão de localização foi negada.';

        const result: LocationResult = {
          success: false,
          status: resultStatus,
          coords: null,
          errorMessage: errorMsg,
          canAskAgain: permissionResponse.canAskAgain,
        };

        if (isMountedRef.current) {
          setState({
            status: resultStatus,
            coords: null,
            errorMessage: errorMsg,
            canAskAgain: permissionResponse.canAskAgain,
          });
        }
        return result;
      }

      // 3. Get current position with controlled timeout
      const locationPromise = Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      const timeoutPromise = new Promise<never>((_, reject) => {
        timeoutId = setTimeout(() => {
          reject(new Error('LOCATION_TIMEOUT'));
        }, LOCATION_TIMEOUT_MS);
      });

      const location = await Promise.race([locationPromise, timeoutPromise]);
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }

      const coords: LocationCoordinates = {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        accuracy: location.coords.accuracy,
      };

      // 4. Check accuracy threshold (>1000m)
      if (location.coords.accuracy !== null && location.coords.accuracy > ACCURACY_THRESHOLD_METERS) {
        const result: LocationResult = {
          success: true,
          status: 'inaccurate',
          coords,
          errorMessage: 'A precisão da localização obtida é baixa.',
          canAskAgain: true,
        };
        if (isMountedRef.current) {
          setState({
            status: 'inaccurate',
            coords,
            errorMessage: result.errorMessage,
            canAskAgain: true,
          });
        }
        return result;
      }

      const result: LocationResult = {
        success: true,
        status: 'ready',
        coords,
        errorMessage: null,
        canAskAgain: true,
      };

      if (isMountedRef.current) {
        setState({
          status: 'ready',
          coords,
          errorMessage: null,
          canAskAgain: true,
        });
      }
      return result;
    } catch (err: unknown) {
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }

      const isTimeout = err instanceof Error && err.message === 'LOCATION_TIMEOUT';
      const status: LocationStateStatus = isTimeout ? 'timeout' : 'error';
      const errorMessage = isTimeout
        ? 'Tempo limite esgotado ao tentar obter a localização.'
        : err instanceof Error
        ? err.message
        : 'Erro ao obter localização.';

      const result: LocationResult = {
        success: false,
        status,
        coords: null,
        errorMessage,
        canAskAgain: true,
      };

      if (isMountedRef.current) {
        setState({
          status,
          coords: null,
          errorMessage,
          canAskAgain: true,
        });
      }
      return result;
    } finally {
      isRequestingRef.current = false;
    }
  }, [state.status, state.coords, state.canAskAgain]);

  return {
    ...state,
    requestLocation,
    resetLocation,
  };
}
