import type { ImageSourcePropType } from 'react-native';

type RouteCover = {
  id?: string | null;
  slug?: string | null;
  cover_image_url?: string | null;
};

const pindobalCoverImage = require('../../../assets/images/pindobal1.png');

export const isPindobalRoute = (route: RouteCover) =>
  route.id === 'route-pindobal' ||
  route.slug === 'rota-pindobal' ||
  route.slug === 'rota-santarem-pindobal';

/** Keeps Pindobal's editorial cover bundled with the app while other routes use API media. */
export const getRouteCoverImage = (route: RouteCover): ImageSourcePropType | undefined => {
  if (isPindobalRoute(route)) {
    return pindobalCoverImage;
  }

  return route.cover_image_url ? { uri: route.cover_image_url } : undefined;
};

export const getPindobalCoverImage = (route: RouteCover): ImageSourcePropType | undefined =>
  isPindobalRoute(route) ? pindobalCoverImage : undefined;
