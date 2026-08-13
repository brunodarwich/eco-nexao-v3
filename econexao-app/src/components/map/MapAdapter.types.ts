import type { DimensionValue, ImageSourcePropType } from 'react-native';

import type { MapBounds, RouteGeometry } from '../../api/types';
import type { FlexiblePinItem } from './MapPin';

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
