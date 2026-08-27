import { getRouteCoverImage } from './routeCoverImage';

describe('getRouteCoverImage', () => {
  it('uses the bundled pindobal1 image for the Pindobal route', () => {
    expect(getRouteCoverImage({ slug: 'rota-pindobal', cover_image_url: 'https://example.test/old.jpg' })).toBeDefined();
    expect(getRouteCoverImage({ id: 'route-pindobal' })).toBeDefined();
  });

  it('preserves the API image source for every other route', () => {
    expect(getRouteCoverImage({ slug: 'outra-rota', cover_image_url: 'https://example.test/route.jpg' }))
      .toEqual({ uri: 'https://example.test/route.jpg' });
  });

  it('keeps the unavailable-image state for other routes without a cover', () => {
    expect(getRouteCoverImage({ slug: 'outra-rota' })).toBeUndefined();
  });
});
