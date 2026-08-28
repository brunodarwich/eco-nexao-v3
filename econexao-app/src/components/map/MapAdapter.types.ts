import type { DimensionValue, ImageSourcePropType } from 'react-native';

import type { MapBounds, MapPin, RouteGeometry } from '../../api/types';

export type FlexiblePinItem =
  | MapPin
  | {
      id: string;
      name: string;
      segment?: string;
      category_slug?: string;
      category_label?: string;
      color?: string;
      icon?: string;
      actor_id?: string;
      latitude?: number;
      longitude?: number;
      coordinate?: { latitude?: number; longitude?: number };
    };

export interface MapCoordinate {
  latitude: number;
  longitude: number;
}

export type GeoBounds = MapBounds;
export type MapViewMode = 'route' | 'city';

export interface MapClusterItem {
  isCluster: true;
  id: string;
  count: number;
  latitude: number;
  longitude: number;
  bounds: MapBounds;
  primaryCategorySlug: string;
  primaryCategoryLabel: string;
  primaryColor: string;
  items: FlexiblePinItem[];
}

export type MapRenderableItem =
  | (FlexiblePinItem & { isCluster?: false; offsetCoordinate?: MapCoordinate })
  | MapClusterItem;

export interface MapAdapterProps {
  /** @deprecated Real adapters use map tiles rather than a raster source. */
  mapImageSource?: ImageSourcePropType;
  actors?: FlexiblePinItem[];
  pins?: FlexiblePinItem[];
  geometry?: RouteGeometry | null;
  bounds?: MapBounds | null;
  cityBounds?: MapBounds | null;
  viewMode?: MapViewMode;
  onViewModeChange?: (mode: MapViewMode) => void;
  selectedActorId?: string;
  onSelectActor: (actorId: string) => void;
  onSelectCluster?: (cluster: MapClusterItem) => void;
  height?: DimensionValue;
  showControls?: boolean;
  selectionMode?: boolean;
  selectedCoordinate?: MapCoordinate | null;
  onSelectCoordinate?: (coord: MapCoordinate) => void;
  selectionPinLabel?: string;
}
