import type { DimensionValue, ImageSourcePropType } from 'react-native';

import type { MapBounds, MapPin, RouteGeometry } from '../../api/types';

export type FlexiblePinItem =
  | MapPin
  | {
      id: string;
      name: string;
      segment?: string;
      category_slug?: string;
      actor_id?: string;
      latitude?: number;
      longitude?: number;
      coordinate?: { latitude?: number; longitude?: number };
    };

export interface MapCoordinate {
  latitude: number;
  longitude: number;
}

export interface MapAdapterProps {
  /** @deprecated Real adapters use map tiles rather than a raster source. */
  mapImageSource?: ImageSourcePropType;
  actors?: FlexiblePinItem[];
  pins?: FlexiblePinItem[];
  geometry?: RouteGeometry | null;
  bounds?: MapBounds | null;
  selectedActorId?: string;
  onSelectActor: (actorId: string) => void;
  height?: DimensionValue;
}
