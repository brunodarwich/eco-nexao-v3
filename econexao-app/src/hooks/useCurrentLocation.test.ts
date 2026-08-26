import React from 'react';
import renderer, { act } from 'react-test-renderer';
import * as Location from 'expo-location';
import { useCurrentLocation, UseCurrentLocationReturn, LocationResult } from './useCurrentLocation';

interface ConsumerProps {
  onState: (api: UseCurrentLocationReturn) => void;
}

const TestHookConsumer = ({ onState }: ConsumerProps): React.ReactElement | null => {
  const hookApi = useCurrentLocation();
  onState(hookApi);
  return null;
};

describe('useCurrentLocation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Location.hasServicesEnabledAsync as jest.Mock).mockResolvedValue(true);
    (Location.getForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: Location.PermissionStatus.UNDETERMINED,
      canAskAgain: true,
    });
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: Location.PermissionStatus.GRANTED,
      canAskAgain: true,
    });
    (Location.getCurrentPositionAsync as jest.Mock).mockResolvedValue({
      coords: {
        latitude: -2.4431,
        longitude: -54.7083,
        accuracy: 15,
      },
    });
  });

  it('starts in idle status and does not request location on mount', () => {
    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    expect(latestApi).toBeDefined();
    expect(latestApi.status).toBe('idle');
    expect(latestApi.coords).toBeNull();
    expect(latestApi.errorMessage).toBeNull();
    expect(latestApi.canAskAgain).toBe(true);
    expect(Location.getForegroundPermissionsAsync).not.toHaveBeenCalled();
    expect(Location.requestForegroundPermissionsAsync).not.toHaveBeenCalled();
    expect(Location.getCurrentPositionAsync).not.toHaveBeenCalled();
  });

  it('successfully obtains coordinates when permissions are granted and accuracy is good', async () => {
    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(Location.hasServicesEnabledAsync).toHaveBeenCalledTimes(1);
    expect(Location.getForegroundPermissionsAsync).toHaveBeenCalledTimes(1);
    expect(Location.requestForegroundPermissionsAsync).toHaveBeenCalledTimes(1);
    expect(Location.getCurrentPositionAsync).toHaveBeenCalledTimes(1);

    expect(result).toEqual({
      success: true,
      status: 'ready',
      coords: {
        latitude: -2.4431,
        longitude: -54.7083,
        accuracy: 15,
      },
      errorMessage: null,
      canAskAgain: true,
    });
    expect(latestApi.status).toBe('ready');
    expect(latestApi.coords).toEqual({
      latitude: -2.4431,
      longitude: -54.7083,
      accuracy: 15,
    });
    expect(latestApi.errorMessage).toBeNull();
  });

  it('reuses existing granted permission without requesting again', async () => {
    (Location.getForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: Location.PermissionStatus.GRANTED,
      canAskAgain: true,
    });

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(Location.getForegroundPermissionsAsync).toHaveBeenCalledTimes(1);
    expect(Location.requestForegroundPermissionsAsync).not.toHaveBeenCalled();
    expect(result.success).toBe(true);
    expect(result.status).toBe('ready');
  });

  it('returns services_disabled status when device location services are off', async () => {
    (Location.hasServicesEnabledAsync as jest.Mock).mockResolvedValue(false);

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(result.success).toBe(false);
    expect(result.status).toBe('services_disabled');
    expect(result.coords).toBeNull();
    expect(result.errorMessage).toContain('desativados');
    expect(latestApi.status).toBe('services_disabled');
    expect(Location.requestForegroundPermissionsAsync).not.toHaveBeenCalled();
  });

  it('returns denied status when user rejects location permission but can ask again', async () => {
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: Location.PermissionStatus.DENIED,
      canAskAgain: true,
    });

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(result.success).toBe(false);
    expect(result.status).toBe('denied');
    expect(result.coords).toBeNull();
    expect(result.canAskAgain).toBe(true);
    expect(result.errorMessage).toContain('negada');
    expect(latestApi.status).toBe('denied');
    expect(Location.getCurrentPositionAsync).not.toHaveBeenCalled();
  });

  it('returns permanently_denied when permission is blocked (canAskAgain is false)', async () => {
    (Location.getForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: Location.PermissionStatus.DENIED,
      canAskAgain: false,
    });

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(result.success).toBe(false);
    expect(result.status).toBe('permanently_denied');
    expect(result.canAskAgain).toBe(false);
    expect(result.errorMessage).toContain('configurações');
    expect(latestApi.status).toBe('permanently_denied');
    expect(Location.requestForegroundPermissionsAsync).not.toHaveBeenCalled();
  });

  it('returns inaccurate status when accuracy threshold is exceeded (> 1000m)', async () => {
    (Location.getCurrentPositionAsync as jest.Mock).mockResolvedValue({
      coords: {
        latitude: -2.4431,
        longitude: -54.7083,
        accuracy: 1500,
      },
    });

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(result.success).toBe(true);
    expect(result.status).toBe('inaccurate');
    expect(result.coords).toEqual({
      latitude: -2.4431,
      longitude: -54.7083,
      accuracy: 1500,
    });
    expect(result.errorMessage).toContain('precisão');
    expect(latestApi.status).toBe('inaccurate');
  });

  it('returns timeout status when location fetch times out', async () => {
    (Location.getCurrentPositionAsync as jest.Mock).mockImplementation(
      () =>
        new Promise((_, reject) => {
          setTimeout(() => {
            reject(new Error('LOCATION_TIMEOUT'));
          }, 10);
        })
    );

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(result.success).toBe(false);
    expect(result.status).toBe('timeout');
    expect(result.coords).toBeNull();
    expect(result.errorMessage).toContain('Tempo limite');
    expect(latestApi.status).toBe('timeout');
  });

  it('returns generic error status on unexpected rejection', async () => {
    (Location.getCurrentPositionAsync as jest.Mock).mockRejectedValue(new Error('GPS unavailable'));

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let result!: LocationResult;
    await act(async () => {
      result = await latestApi.requestLocation();
    });

    expect(result.success).toBe(false);
    expect(result.status).toBe('error');
    expect(result.coords).toBeNull();
    expect(result.errorMessage).toBe('GPS unavailable');
    expect(latestApi.status).toBe('error');
  });

  it('guards against concurrent requests while already requesting', async () => {
    (Location.getCurrentPositionAsync as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              coords: {
                latitude: -2.4431,
                longitude: -54.7083,
                accuracy: 10,
              },
            });
          }, 50);
        })
    );

    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    let res1!: LocationResult;
    let res2!: LocationResult;

    await act(async () => {
      const p1 = latestApi.requestLocation();
      const p2 = latestApi.requestLocation();
      [res1, res2] = await Promise.all([p1, p2]);
    });

    expect(res1.success).toBe(true);
    expect(res2.success).toBe(false);
    expect(res2.errorMessage).toContain('já está em andamento');
  });

  it('resets location state to idle on resetLocation', async () => {
    let latestApi!: UseCurrentLocationReturn;
    act(() => {
      renderer.create(
        React.createElement(TestHookConsumer, {
          onState: (api: UseCurrentLocationReturn) => {
            latestApi = api;
          },
        })
      );
    });

    await act(async () => {
      await latestApi.requestLocation();
    });
    expect(latestApi.status).toBe('ready');

    act(() => {
      latestApi.resetLocation();
    });

    expect(latestApi.status).toBe('idle');
    expect(latestApi.coords).toBeNull();
    expect(latestApi.errorMessage).toBeNull();
  });
});
