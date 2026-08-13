import { apiClient } from '../api/client';

describe('ApiClient favorite actor methods', () => {
  afterEach(() => jest.restoreAllMocks());

  it('addFavoriteActor realiza PUT para /me/favorite-actors/{actor_id}', async () => {
    const mockSuccess = { success: true };
    const spy = jest.spyOn(apiClient, 'addFavoriteActor').mockResolvedValue(mockSuccess);

    const res = await apiClient.addFavoriteActor('actor-123');

    expect(spy).toHaveBeenCalledWith('actor-123');
    expect(res).toEqual({ success: true });
  });

  it('removeFavoriteActor realiza DELETE para /me/favorite-actors/{actor_id}', async () => {
    const mockSuccess = { success: true };
    const spy = jest.spyOn(apiClient, 'removeFavoriteActor').mockResolvedValue(mockSuccess);

    const res = await apiClient.removeFavoriteActor('actor-123');

    expect(spy).toHaveBeenCalledWith('actor-123');
    expect(res).toEqual({ success: true });
  });

  it('getMyFavoriteActors realiza GET para /me/favorite-actors', async () => {
    const mockList = { data: [] };
    const spy = jest.spyOn(apiClient, 'getMyFavoriteActors').mockResolvedValue(mockList as any);

    const res = await apiClient.getMyFavoriteActors();

    expect(spy).toHaveBeenCalled();
    expect(res).toEqual(mockList);
  });
});
