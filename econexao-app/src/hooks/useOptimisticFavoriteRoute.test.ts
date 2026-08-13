import { apiClient } from '../api/client';

describe('ApiClient favorite route methods', () => {
  afterEach(() => jest.restoreAllMocks());

  it('addFavoriteRoute realiza PUT para /me/favorite-routes/{route_id}', async () => {
    const mockSuccess = { success: true };
    const spy = jest.spyOn(apiClient, 'addFavoriteRoute').mockResolvedValue(mockSuccess);

    const res = await apiClient.addFavoriteRoute('route-123');

    expect(spy).toHaveBeenCalledWith('route-123');
    expect(res).toEqual({ success: true });
  });

  it('removeFavoriteRoute realiza DELETE para /me/favorite-routes/{route_id}', async () => {
    const mockSuccess = { success: true };
    const spy = jest.spyOn(apiClient, 'removeFavoriteRoute').mockResolvedValue(mockSuccess);

    const res = await apiClient.removeFavoriteRoute('route-123');

    expect(spy).toHaveBeenCalledWith('route-123');
    expect(res).toEqual({ success: true });
  });

  it('updateMyPreferences realiza PATCH para /me/preferences', async () => {
    const mockPrefResponse = {
      data: {
        id: 'pref-1',
        user_id: 'user-1',
        active_region_id: 'region-abc',
        high_contrast: false,
        screen_reader_mode: false,
        text_scale: 1,
        locale: 'pt-BR',
      },
    };
    const spy = jest.spyOn(apiClient, 'updateMyPreferences').mockResolvedValue(mockPrefResponse as any);

    const res = await apiClient.updateMyPreferences({ active_region_id: 'region-abc' });

    expect(spy).toHaveBeenCalledWith({ active_region_id: 'region-abc' });
    expect(res).toEqual(mockPrefResponse);
  });
});
