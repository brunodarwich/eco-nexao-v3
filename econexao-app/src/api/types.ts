/** Stable aliases over the generated OpenAPI contract. Do not define API shapes manually here. */

import type { components, operations } from './generated/openapi';

type Schemas = components['schemas'];

export type ApiErrorDetail = Schemas['ErrorDetail'];
export type ErrorResponse = Schemas['ErrorResponse'];
export type PaginationMeta = Schemas['PaginationMeta'];
export type Region = Schemas['RegionSchema'];
export type RouteSummary = Schemas['RouteSummarySchema'];
export type RouteOrigin = Schemas['RouteOriginSchema'];
export type RouteDetail = Schemas['RouteDetailSchema'];
export type RouteGeometry = Schemas['RouteGeometrySchema'];
export type RouteAlert = Schemas['RouteAlertSchema'];
export type ActorCategory = Schemas['ActorCategorySchema'];
export type ActorSummary = Schemas['ActorSummarySchema'];
export type AccessibilityFeature = Record<string, unknown>;
export type ActorDetail = Schemas['ActorDetailSchema'];
export type MapPin = Schemas['MapPinSchema'];
export type MapBounds = Record<string, number>;
export type RouteMapPayload = Schemas['RouteMapPayloadSchema'];
export type BootstrapData = Schemas['BootstrapDataSchema'];

export type RegionListEnvelope = Schemas['RegionListEnvelope'];
export type RouteListEnvelope = Schemas['RouteListEnvelope'];
export type RouteOriginListEnvelope = Schemas['RouteOriginListEnvelope'];
export type RouteDetailEnvelope = Schemas['RouteDetailEnvelope'];
export type RouteGeometryEnvelope = Schemas['RouteGeometryEnvelope'];
export type RouteAlertListEnvelope = Schemas['RouteAlertListEnvelope'];
export type ActorListEnvelope = Schemas['ActorListEnvelope'];
export type ActorCategoryListEnvelope = Schemas['ActorCategoryListEnvelope'];
export type ActorDetailEnvelope = Schemas['ActorDetailEnvelope'];
export type RouteMapPayloadEnvelope = Schemas['RouteMapPayloadEnvelope'];
export type UserPreferencesEnvelope = Schemas['UserPreferencesEnvelope'];
export type UserPreferencesUpdate = Schemas['UserPreferencesUpdate'] & {
  high_contrast?: boolean;
  reader_mode?: boolean;
};
export type UserProfileEnvelope = Schemas['UserProfileEnvelope'];
export type UserProfileSchema = Schemas['UserProfileSchema'];
export type UserProfileUpdate = Schemas['UserProfileUpdate'];

export type AvatarUploadRequest = Schemas['AvatarUploadRequest'];
export type AvatarUploadResponseEnvelope = Schemas['AvatarUploadResponseEnvelope'];
export type UserImpactEnvelope = Schemas['UserImpactEnvelope'];
export type UserImpactData = Schemas['UserImpactData'];
export type TripListEnvelope = Schemas['TripListEnvelope'];
export type TripEnvelope = Schemas['TripEnvelope'];
export type TripSchema = Schemas['TripSchema'];
export type TripCreate = Schemas['TripCreate'];
export type SupportContentEnvelope = Schemas['SupportContentEnvelope'];
export type SupportContentData = Schemas['SupportContentData'];
export type StandardSuccessResponse = Schemas['StandardSuccessResponse'];
export type BootstrapResponseEnvelope = Schemas['BootstrapResponseEnvelope'];
export type AdminAccessSchema = Schemas['AdminAccessSchema'];
export type AdminScopeAccessSchema = Schemas['AdminScopeAccessSchema'];
export type AdminContextData = Schemas['AdminContextDataSchema'];
export type AdminContextEnvelope = Schemas['AdminContextEnvelope'];
export type AdminRegionSchema = Schemas['AdminRegionSchema'];
export type AdminRegionCreateSchema = Schemas['AdminRegionCreateSchema'];
export type AdminRegionUpdateSchema = Schemas['AdminRegionUpdateSchema'];
export type AdminRegionEnvelope = Schemas['AdminRegionEnvelope'];
export type AdminRegionListEnvelope = Schemas['AdminRegionListEnvelope'];
export type AdminRouteSchema = Schemas['AdminRouteSchema'];
export type AdminRouteCreateSchema = Schemas['AdminRouteCreateSchema'];
export type AdminRouteUpdateSchema = Schemas['AdminRouteUpdateSchema'];
export type AdminRouteEnvelope = Schemas['AdminRouteEnvelope'];
export type AdminRouteListEnvelope = Schemas['AdminRouteListEnvelope'];
export type AdminActorSchema = Schemas['AdminActorSchema'];
export type AdminActorCreateSchema = Schemas['AdminActorCreateSchema'];
export type AdminActorUpdateSchema = Schemas['AdminActorUpdateSchema'];
export type AdminActorEnvelope = Schemas['AdminActorEnvelope'];
export type AdminActorListEnvelope = Schemas['AdminActorListEnvelope'];

export type StatusTransitionRequest = Schemas['StatusTransitionRequest'];
export type StatusTransitionSchema = Schemas['StatusTransitionSchema'];
export type StatusTransitionEnvelope = Schemas['StatusTransitionEnvelope'];
export type PublishGuardResultSchema = Schemas['PublishGuardResultSchema'];
export type PublishGuardResultEnvelope = Schemas['PublishGuardResultEnvelope'];
export type ReconciliationCandidateSchema = Schemas['ReconciliationCandidateSchema'];
export type ReconciliationCandidateListEnvelope = Schemas['ReconciliationCandidateListEnvelope'];
export type ReconciliationDecisionRequest = Schemas['ReconciliationDecisionRequest'];
export type ReconciliationDecisionSchema = Schemas['ReconciliationDecisionSchema'];
export type ReconciliationDecisionEnvelope = Schemas['ReconciliationDecisionEnvelope'];
export type ReconciliationCompensationRequest = Schemas['ReconciliationCompensationRequest'];
export type EditorialAlertSchema = Schemas['EditorialAlertSchema'];
export type EditorialAlertEnvelope = Schemas['EditorialAlertEnvelope'];
export type EditorialAlertListEnvelope = Schemas['EditorialAlertListEnvelope'];
export type EditorialAlertCreateRequest = Schemas['EditorialAlertCreateRequest'];
export type EditorialAlertUpdateRequest = Schemas['EditorialAlertUpdateRequest'];
export type AlertResolveRequest = Schemas['AlertResolveRequest'];

export type ListRoutesQuery = operations['list_routes_api_v1_routes_get']['parameters']['query'];
export type GetRouteActorsQuery = operations['get_route_actors_api_v1_routes__route_id__actors_get']['parameters']['query'];

/** @deprecated Use the exact generated envelope alias for each operation. */
export interface ApiResponseEnvelope<T> {
  data: T;
  meta?: PaginationMeta;
}
