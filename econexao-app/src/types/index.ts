import { ImageSourcePropType } from 'react-native';

export type OriginType = 'porto' | 'rodoviaria' | 'aeroporto';

export interface OriginPoint {
  id: OriginType;
  name: string;
  locationName: string;
  actorCount: number;
  description: string;
}

export type CategorySegment = 
  | 'todos'
  | 'hospedagem'
  | 'alimentacao'
  | 'transporte'
  | 'artesanato'
  | 'emergencia'
  | 'atrativos';

export interface ActorCategory {
  id: CategorySegment;
  label: string;
  icon: string;
  color: string;
}

export interface Actor {
  id: string;
  name: string;
  segment: CategorySegment;
  subCategory: string;
  group: 'Apoio Turístico e Comercial' | 'Emergência e Infraestrutura Pública' | 'Inventário SEMTUR';
  address: string;
  city: string;
  state: string;
  phone: string;
  rating: number;
  reviewCount: number;
  greenBadge: boolean;
  accessibilityFeatures: string[];
  imageUrl: ImageSourcePropType;
  coordinate: {
    xPercentage: number;
    yPercentage: number;
    latitude?: number;
    longitude?: number;
  };
  description: string;
}

export interface RouteAlert {
  id: string;
  title: string;
  message: string;
  type: 'warning' | 'info' | 'critical';
  updatedAt: string;
}

export interface Route {
  id: string;
  title: string;
  region: string;
  city: string;
  state: string;
  totalDistanceKm: number;
  actorCountTotal: number;
  origins: OriginPoint[];
  verificationDate: string;
  isVerified: boolean;
  isFavorite: boolean;
  coverImageUrl: ImageSourcePropType;
  summary: string;
  bestSeason: string;
  connectivity: string;
  roadAccess: string;
  paymentInfo: string;
  alerts: RouteAlert[];
  actors: Actor[];
}

export interface UserProfile {
  id: string;
  name: string;
  location: string;
  avatarUrl: ImageSourcePropType;
  routesCompleted: number;
  actorsVisited: number;
  consciousTravelerBadge: boolean;
  savedRouteIds: string[];
  savedActorIds: string[];
}
