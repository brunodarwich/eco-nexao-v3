/**
 * Typed HTTP API Client for ECOnexão backend integration (ECO-0701).
 */

import {
  ActorCategory,
  ActorDetail,
  ActorSummary,
  ActorCategoryListEnvelope,
  ActorDetailEnvelope,
  ActorListEnvelope,
  AvatarUploadResponseEnvelope,
  BootstrapData,
  BootstrapResponseEnvelope,
  GetRouteActorsQuery,
  GetRouteMapQuery,
  ListRoutesQuery,
  Region,
  RegionListEnvelope,
  RouteAlert,
  RouteDetail,
  RouteGeometry,
  RouteMapPayload,
  RouteOrigin,
  RouteSummary,
  RouteAlertListEnvelope,
  RouteDetailEnvelope,
  RouteGeometryEnvelope,
  RouteListEnvelope,
  RouteMapPayloadEnvelope,
  RouteOriginListEnvelope,
  RoutePreviewEnvelope,
  RoutePreviewRequest,
  TripCreate,
  TripEnvelope,
  TripListEnvelope,
  UserPreferencesEnvelope,
  UserPreferencesUpdate,
  UserProfileEnvelope,
  UserProfileUpdate,
  SupportContentEnvelope,
  StandardSuccessResponse,
  AdminContextEnvelope,
  AdminRegionCreateSchema,
  AdminRegionEnvelope,
  AdminRegionListEnvelope,
  AdminRegionUpdateSchema,
  AdminRouteCreateSchema,
  AdminRouteEnvelope,
  AdminRouteListEnvelope,
  AdminRouteUpdateSchema,
  AdminActorCreateSchema,
  AdminActorEnvelope,
  AdminActorListEnvelope,
  AdminActorUpdateSchema,
  StatusTransitionRequest,
  StatusTransitionEnvelope,
  PublishGuardResultEnvelope,
  ReconciliationCandidateListEnvelope,
  ReconciliationDecisionRequest,
  ReconciliationDecisionEnvelope,
  ReconciliationCompensationRequest,
  EditorialAlertListEnvelope,
  EditorialAlertEnvelope,
  EditorialAlertCreateRequest,
  EditorialAlertUpdateRequest,
  AlertResolveRequest,
} from "./types";
import { onlineManager } from '@tanstack/react-query';
import { Platform } from 'react-native';

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly requestId?: string;
  public readonly details?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    code: string = "API_ERROR",
    requestId?: string,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

export class ApiClient {
  private baseUrl: string;
  private getAccessToken: () => string | null | Promise<string | null> = () => null;
  private refreshAccessToken: (() => Promise<string | null>) | null = null;
  private onAuthFailure: (() => void | Promise<void>) | null = null;
  private refreshFlight: Promise<string | null> | null = null;

  constructor(baseUrl?: string) {
    const configuredUrl = baseUrl || process.env.EXPO_PUBLIC_API_URL;
    if (!configuredUrl) throw new Error('EXPO_PUBLIC_API_URL não está configurada.');
    const parsedUrl = new URL(configuredUrl);
    const isLocal = parsedUrl.hostname === 'localhost' || parsedUrl.hostname === '127.0.0.1';
    if (parsedUrl.protocol !== 'https:' && !isLocal) {
      throw new Error('EXPO_PUBLIC_API_URL deve usar HTTPS fora do ambiente local.');
    }
    this.baseUrl = configuredUrl;
  }

  public configureAuth(
    getAccessToken: () => string | null | Promise<string | null>,
    refreshAccessToken: () => Promise<string | null>,
    onAuthFailure?: () => void | Promise<void>
  ): void {
    this.getAccessToken = getAccessToken;
    this.refreshAccessToken = refreshAccessToken;
    this.onAuthFailure = onAuthFailure ?? null;
  }

  private generateRequestId(): string {
    return `req-${Math.random().toString(36).substring(2, 10)}-${Date.now()}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    hasRetriedAuth = false,
    requiresAuth = false
  ): Promise<T> {
    const url = `${this.baseUrl.replace(/\/$/, "")}${endpoint}`;
    const requestId = this.generateRequestId();
    const method = (options.method ?? 'GET').toUpperCase();

    if (method !== 'GET' && method !== 'HEAD' && !onlineManager.isOnline()) {
      throw new ApiClientError(
        'Esta ação precisa de conexão. Reconecte e tente novamente.',
        0,
        'OFFLINE_MUTATION_BLOCKED',
        requestId
      );
    }

    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      Accept: "application/json",
      "X-Request-ID": requestId,
      ...(options.headers as Record<string, string>),
    };

    if (requiresAuth) {
      const authToken = await this.getAccessToken();
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json().catch(() => null);
      const responseRequestId =
        (typeof data?.request_id === "string" && data.request_id) ||
        response.headers.get("X-Request-ID") ||
        requestId;

      if (requiresAuth && response.status === 401 && !hasRetriedAuth && this.refreshAccessToken) {
        if (!this.refreshFlight) {
          this.refreshFlight = this.refreshAccessToken().finally(() => {
            this.refreshFlight = null;
          });
        }
        let refreshedToken: string | null = null;
        try {
          refreshedToken = await this.refreshFlight;
        } catch {
          await this.onAuthFailure?.();
          throw new ApiClientError(
            'Sua sessão expirou e não pôde ser renovada.',
            401,
            'AUTH_REFRESH_FAILED',
            responseRequestId
          );
        }
        if (!refreshedToken) {
          await this.onAuthFailure?.();
          throw new ApiClientError(
            'Sua sessão expirou e não pôde ser renovada.',
            401,
            'AUTH_REFRESH_FAILED',
            responseRequestId
          );
        }
        return this.request<T>(endpoint, options, true, true);
      }

      if (!response.ok) {
        const errorDetail = data?.error || data?.detail?.error || data?.detail;
        const code = typeof errorDetail === "object" ? errorDetail?.code || "HTTP_ERROR" : "HTTP_ERROR";
        const message =
          typeof errorDetail === "object"
            ? errorDetail?.message || response.statusText
            : typeof errorDetail === "string"
            ? errorDetail
            : response.statusText;

        throw new ApiClientError(
          message || `Request failed with status ${response.status}`,
          response.status,
          code,
          responseRequestId,
          typeof errorDetail === "object" ? errorDetail?.details : undefined
        );
      }

      // Return unpacked data if envelope
      if (data && typeof data === "object" && "data" in data) {
        return data as T;
      }

      return data as T;
    } catch (err) {
      if (err instanceof ApiClientError) {
        throw err;
      }
      throw new ApiClientError(
        err instanceof Error ? err.message : "Network error",
        0,
        "NETWORK_ERROR",
        requestId
      );
    }
  }

  // ---------------------------------------------------------------------------
  // API Endpoints
  // ---------------------------------------------------------------------------

  public async getBootstrap(): Promise<BootstrapResponseEnvelope> {
    return this.request<BootstrapResponseEnvelope>("/bootstrap", {}, false, true);
  }

  public async getRegions(): Promise<RegionListEnvelope> {
    return this.request<RegionListEnvelope>("/regions", {}, false, false);
  }

  public async getRoutes(
    params?: ListRoutesQuery,
    options?: { signal?: AbortSignal }
  ): Promise<RouteListEnvelope> {
    const query = new URLSearchParams();
    if (params?.region_id) query.append("region_id", params.region_id);
    if (params?.q) query.append("q", params.q);
    if (params?.saved !== undefined) query.append("saved", String(params.saved));
    if (params?.verified !== undefined)
      query.append("verified", String(params.verified));
    if (params?.cursor) query.append("cursor", params.cursor);
    if (params?.limit) query.append("limit", String(params.limit));

    const queryString = query.toString() ? `?${query.toString()}` : "";
    const isSavedOnly = params?.saved === true;
    return this.request<RouteListEnvelope>(`/routes${queryString}`, { signal: options?.signal }, false, isSavedOnly);
  }

  public async getRouteDetail(routeId: string): Promise<RouteDetailEnvelope> {
    return this.request<RouteDetailEnvelope>(`/routes/${routeId}`, {}, false, false);
  }

  public async getRouteOrigins(routeId: string): Promise<RouteOriginListEnvelope> {
    return this.request<RouteOriginListEnvelope>(`/routes/${routeId}/origins`, {}, false, false);
  }

  public async getRouteGeometry(
    routeId: string,
    originId: string
  ): Promise<RouteGeometryEnvelope> {
    const query = `?origin_id=${encodeURIComponent(originId)}`;
    return this.request<RouteGeometryEnvelope>(
      `/routes/${routeId}/geometry${query}`,
      {},
      false,
      false
    );
  }

  public async getRouteAlerts(routeId: string): Promise<RouteAlertListEnvelope> {
    return this.request<RouteAlertListEnvelope>(`/routes/${routeId}/alerts`, {}, false, false);
  }

  public async getRouteActors(
    routeId: string,
    params?: GetRouteActorsQuery,
    options?: { signal?: AbortSignal }
  ): Promise<ActorListEnvelope> {
    const query = new URLSearchParams();
    if (params?.q) query.append("q", params.q);
    if (params?.category) query.append("category", params.category);
    if (params?.origin_id) query.append("origin_id", params.origin_id);
    if (params?.cursor) query.append("cursor", params.cursor);
    if (params?.limit) query.append("limit", String(params.limit));

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return this.request<ActorListEnvelope>(
      `/routes/${routeId}/actors${queryString}`,
      { signal: options?.signal },
      false,
      false
    );
  }

  public async getRouteMapPayload(
    routeId: string,
    params: GetRouteMapQuery = {},
    options?: { signal?: AbortSignal; timeoutMs?: number }
  ): Promise<RouteMapPayloadEnvelope> {
    if (!onlineManager.isOnline()) {
      throw new ApiClientError(
        'O mapa não está disponível offline. Reconecte e tente novamente.',
        0,
        'OFFLINE'
      );
    }

    const query = new URLSearchParams();
    if (params.origin_id) query.append('origin_id', params.origin_id);
    if (params.layer) query.append('layer', params.layer);
    if (params.category) query.append('category', params.category);
    const queryString = query.toString() ? `?${query.toString()}` : '';
    const controller = new AbortController();
    let didTimeout = false;
    const abortFromCaller = () => controller.abort();
    if (options?.signal?.aborted) {
      controller.abort();
    } else {
      options?.signal?.addEventListener('abort', abortFromCaller, { once: true });
    }
    const timeout = setTimeout(() => {
      didTimeout = true;
      controller.abort();
    }, options?.timeoutMs ?? 60_000);

    try {
      return await this.request<RouteMapPayloadEnvelope>(
        `/routes/${routeId}/map${queryString}`,
        { signal: controller.signal },
        false,
        false
      );
    } catch (error) {
      if (didTimeout) {
        throw new ApiClientError(
          'O carregamento do mapa excedeu o tempo limite.',
          0,
          'TIMEOUT'
        );
      }
      throw error;
    } finally {
      clearTimeout(timeout);
      options?.signal?.removeEventListener('abort', abortFromCaller);
    }
  }

  public async previewRoute(
    routeId: string,
    payload: RoutePreviewRequest,
    options?: { signal?: AbortSignal }
  ): Promise<RoutePreviewEnvelope> {
    return this.request<RoutePreviewEnvelope>(`/routes/${routeId}/preview`, {
      method: "POST",
      body: JSON.stringify(payload),
      signal: options?.signal,
    }, false, false);
  }

  public async getActorCategories(): Promise<ActorCategoryListEnvelope> {
    return this.request<ActorCategoryListEnvelope>("/actor-categories", {}, false, false);
  }

  public async getActorDetail(actorId: string): Promise<ActorDetailEnvelope> {
    return this.request<ActorDetailEnvelope>(`/actors/${actorId}`, {}, false, false);
  }

  public async updateMyPreferences(
    data: UserPreferencesUpdate
  ): Promise<UserPreferencesEnvelope> {
    return this.request<UserPreferencesEnvelope>("/me/preferences", {
      method: "PATCH",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async addFavoriteRoute(
    routeId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-routes/${routeId}`,
      { method: "PUT" },
      false,
      true
    );
  }

  public async removeFavoriteRoute(
    routeId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-routes/${routeId}`,
      { method: "DELETE" },
      false,
      true
    );
  }

  public async getMyFavoriteRoutes(): Promise<RouteListEnvelope> {
    return this.request<RouteListEnvelope>("/me/favorite-routes", {}, false, true);
  }

  public async addFavoriteActor(
    actorId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-actors/${actorId}`,
      { method: "PUT" },
      false,
      true
    );
  }

  public async removeFavoriteActor(
    actorId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-actors/${actorId}`,
      { method: "DELETE" },
      false,
      true
    );
  }

  public async getMyFavoriteActors(): Promise<ActorListEnvelope> {
    return this.request<ActorListEnvelope>("/me/favorite-actors", {}, false, true);
  }

  public async getMyProfile(): Promise<UserProfileEnvelope> {
    return this.request<UserProfileEnvelope>("/me", {}, false, true);
  }

  public async updateMyProfile(
    data: UserProfileUpdate
  ): Promise<UserProfileEnvelope> {
    return this.request<UserProfileEnvelope>("/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async uploadAvatar(file: {
    uri: string;
    name: string;
    type: string;
    file?: Blob;
  }): Promise<AvatarUploadResponseEnvelope> {
    const body = new FormData();
    if (Platform.OS === 'web') {
      let browserFile = file.file;
      if (!browserFile) {
        const localResponse = await fetch(file.uri);
        if (!localResponse.ok) {
          throw new ApiClientError(
            'Não foi possível ler o arquivo selecionado.',
            0,
            'AVATAR_FILE_READ_FAILED'
          );
        }
        browserFile = await localResponse.blob();
      }
      body.append('file', browserFile, file.name);
    } else {
      body.append(
        'file',
        { uri: file.uri, name: file.name, type: file.type } as unknown as Blob
      );
    }
    return this.request<AvatarUploadResponseEnvelope>("/me/avatar", {
      method: "POST",
      body,
    }, false, true);
  }

  public async deleteMyAccount(): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>("/me/account", { method: "DELETE" }, false, true);
  }

  public async getMyPreferences(): Promise<UserPreferencesEnvelope> {
    return this.request<UserPreferencesEnvelope>("/me/preferences", {}, false, true);
  }

  public async getMyTrips(): Promise<TripListEnvelope> {
    return this.request<TripListEnvelope>("/me/trips", {}, false, true);
  }

  public async createTrip(routeId: string): Promise<TripEnvelope> {
    return this.request<TripEnvelope>("/me/trips", {
      method: "POST",
      body: JSON.stringify({ route_id: routeId }),
    }, false, true);
  }

  public async getSupportContent(): Promise<SupportContentEnvelope> {
    return this.request<SupportContentEnvelope>("/content/support", {}, false, false);
  }

  public async getAdminContext(options?: { signal?: AbortSignal }): Promise<AdminContextEnvelope> {
    return this.request<AdminContextEnvelope>("/admin/context", { signal: options?.signal }, false, true);
  }

  // ---------------------------------------------------------------------------
  // Admin Endpoints (ECO-1802 / ECO-1803)
  // ---------------------------------------------------------------------------

  public async getAdminRegions(options?: { signal?: AbortSignal }): Promise<AdminRegionListEnvelope> {
    return this.request<AdminRegionListEnvelope>("/admin/territory/regions", { signal: options?.signal }, false, true);
  }

  public async createAdminRegion(data: AdminRegionCreateSchema): Promise<AdminRegionEnvelope> {
    return this.request<AdminRegionEnvelope>("/admin/territory/regions", {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async updateAdminRegion(regionId: string, data: AdminRegionUpdateSchema): Promise<AdminRegionEnvelope> {
    return this.request<AdminRegionEnvelope>(`/admin/territory/regions/${regionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async deleteAdminRegion(regionId: string): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(`/admin/territory/regions/${regionId}`, {
      method: "DELETE",
    }, false, true);
  }

  public async getAdminRoutes(params?: { region_id?: string }, options?: { signal?: AbortSignal }): Promise<AdminRouteListEnvelope> {
    const query = params?.region_id ? `?region_id=${encodeURIComponent(params.region_id)}` : "";
    return this.request<AdminRouteListEnvelope>(`/admin/territory/routes${query}`, { signal: options?.signal }, false, true);
  }

  public async createAdminRoute(data: AdminRouteCreateSchema): Promise<AdminRouteEnvelope> {
    return this.request<AdminRouteEnvelope>("/admin/territory/routes", {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async updateAdminRoute(routeId: string, data: AdminRouteUpdateSchema): Promise<AdminRouteEnvelope> {
    return this.request<AdminRouteEnvelope>(`/admin/territory/routes/${routeId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async deleteAdminRoute(routeId: string): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(`/admin/territory/routes/${routeId}`, {
      method: "DELETE",
    }, false, true);
  }

  public async getAdminActors(params?: { route_id?: string; q?: string }, options?: { signal?: AbortSignal }): Promise<AdminActorListEnvelope> {
    const query = new URLSearchParams();
    if (params?.route_id) query.append("route_id", params.route_id);
    if (params?.q) query.append("q", params.q);
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return this.request<AdminActorListEnvelope>(`/admin/actors${queryString}`, { signal: options?.signal }, false, true);
  }

  public async createAdminActor(data: AdminActorCreateSchema): Promise<AdminActorEnvelope> {
    return this.request<AdminActorEnvelope>("/admin/actors", {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async updateAdminActor(actorId: string, data: AdminActorUpdateSchema): Promise<AdminActorEnvelope> {
    return this.request<AdminActorEnvelope>(`/admin/actors/${actorId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async deleteAdminActor(actorId: string): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(`/admin/actors/${actorId}`, {
      method: "DELETE",
    }, false, true);
  }

  // ---------------------------------------------------------------------------
  // Workflow, Publish Guard, Reconciliation & Alerts (ECO-1804)
  // ---------------------------------------------------------------------------

  public async transitionResourceStatus(
    resourceType: string,
    resourceId: string,
    data: StatusTransitionRequest
  ): Promise<StatusTransitionEnvelope> {
    return this.request<StatusTransitionEnvelope>(`/admin/workflow/${resourceType}/${resourceId}/transition`, {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async getPublishGuardStatus(
    resourceType: string,
    resourceId: string,
    options?: { signal?: AbortSignal }
  ): Promise<PublishGuardResultEnvelope> {
    return this.request<PublishGuardResultEnvelope>(`/admin/workflow/${resourceType}/${resourceId}/publish-guard`, {
      signal: options?.signal,
    }, false, true);
  }

  public async getReconciliationCandidates(
    params?: { status?: string; limit?: number; offset?: number },
    options?: { signal?: AbortSignal }
  ): Promise<ReconciliationCandidateListEnvelope> {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.limit) query.append("limit", String(params.limit));
    if (params?.offset) query.append("offset", String(params.offset));
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return this.request<ReconciliationCandidateListEnvelope>(`/admin/reconciliation/candidates${queryString}`, {
      signal: options?.signal,
    }, false, true);
  }

  public async decideReconciliationCandidate(
    candidateId: string,
    data: ReconciliationDecisionRequest
  ): Promise<ReconciliationDecisionEnvelope> {
    return this.request<ReconciliationDecisionEnvelope>(`/admin/reconciliation/${candidateId}/decision`, {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async compensateReconciliationMerge(
    candidateId: string,
    data: ReconciliationCompensationRequest
  ): Promise<ReconciliationDecisionEnvelope> {
    return this.request<ReconciliationDecisionEnvelope>(`/admin/reconciliation/${candidateId}/compensate`, {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async getEditorialAlerts(
    params?: { route_id?: string; severity?: string; is_active?: boolean; limit?: number; offset?: number },
    options?: { signal?: AbortSignal }
  ): Promise<EditorialAlertListEnvelope> {
    const query = new URLSearchParams();
    if (params?.route_id) query.append("route_id", params.route_id);
    if (params?.severity) query.append("severity", params.severity);
    if (params?.is_active !== undefined) query.append("is_active", String(params.is_active));
    if (params?.limit) query.append("limit", String(params.limit));
    if (params?.offset) query.append("offset", String(params.offset));
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return this.request<EditorialAlertListEnvelope>(`/admin/alerts${queryString}`, {
      signal: options?.signal,
    }, false, true);
  }

  public async createEditorialAlert(data: EditorialAlertCreateRequest): Promise<EditorialAlertEnvelope> {
    return this.request<EditorialAlertEnvelope>("/admin/alerts", {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async updateEditorialAlert(
    alertId: string,
    data: EditorialAlertUpdateRequest
  ): Promise<EditorialAlertEnvelope> {
    return this.request<EditorialAlertEnvelope>(`/admin/alerts/${alertId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }, false, true);
  }

  public async resolveEditorialAlert(
    alertId: string,
    data: AlertResolveRequest
  ): Promise<EditorialAlertEnvelope> {
    return this.request<EditorialAlertEnvelope>(`/admin/alerts/${alertId}/resolve`, {
      method: "POST",
      body: JSON.stringify(data),
    }, false, true);
  }
}

export const apiClient = new ApiClient();
