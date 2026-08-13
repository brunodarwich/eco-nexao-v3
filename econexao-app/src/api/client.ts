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
  AvatarUploadRequest,
  AvatarUploadResponseEnvelope,
  BootstrapData,
  BootstrapResponseEnvelope,
  GetRouteActorsQuery,
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
  TripCreate,
  TripEnvelope,
  TripListEnvelope,
  UserImpactEnvelope,
  UserPreferencesEnvelope,
  UserPreferencesUpdate,
  UserProfileEnvelope,
  UserProfileUpdate,
  SupportContentEnvelope,
  StandardSuccessResponse,
} from "./types";

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
    hasRetriedAuth = false
  ): Promise<T> {
    const url = `${this.baseUrl.replace(/\/$/, "")}${endpoint}`;
    const requestId = this.generateRequestId();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      "X-Request-ID": requestId,
      ...(options.headers as Record<string, string>),
    };

    const authToken = await this.getAccessToken();
    if (authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
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

      if (response.status === 401 && !hasRetriedAuth && this.refreshAccessToken) {
        if (!this.refreshFlight) {
          this.refreshFlight = this.refreshAccessToken().finally(() => {
            this.refreshFlight = null;
          });
        }
        let refreshedToken: string | null;
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
        if (refreshedToken) return this.request<T>(endpoint, options, true);
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
    return this.request<BootstrapResponseEnvelope>("/bootstrap");
  }

  public async getRegions(): Promise<RegionListEnvelope> {
    return this.request<RegionListEnvelope>("/regions");
  }

  public async getRoutes(params?: ListRoutesQuery): Promise<RouteListEnvelope> {
    const query = new URLSearchParams();
    if (params?.region_id) query.append("region_id", params.region_id);
    if (params?.q) query.append("q", params.q);
    if (params?.saved !== undefined) query.append("saved", String(params.saved));
    if (params?.verified !== undefined)
      query.append("verified", String(params.verified));
    if (params?.cursor) query.append("cursor", params.cursor);
    if (params?.limit) query.append("limit", String(params.limit));

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return this.request<RouteListEnvelope>(`/routes${queryString}`);
  }

  public async getRouteDetail(routeId: string): Promise<RouteDetailEnvelope> {
    return this.request<RouteDetailEnvelope>(`/routes/${routeId}`);
  }

  public async getRouteOrigins(routeId: string): Promise<RouteOriginListEnvelope> {
    return this.request<RouteOriginListEnvelope>(`/routes/${routeId}/origins`);
  }

  public async getRouteGeometry(
    routeId: string,
    originId: string
  ): Promise<RouteGeometryEnvelope> {
    const query = `?origin_id=${encodeURIComponent(originId)}`;
    return this.request<RouteGeometryEnvelope>(
      `/routes/${routeId}/geometry${query}`
    );
  }

  public async getRouteAlerts(routeId: string): Promise<RouteAlertListEnvelope> {
    return this.request<RouteAlertListEnvelope>(`/routes/${routeId}/alerts`);
  }

  public async getRouteActors(
    routeId: string,
    params?: GetRouteActorsQuery
  ): Promise<ActorListEnvelope> {
    const query = new URLSearchParams();
    if (params?.q) query.append("q", params.q);
    if (params?.category) query.append("category", params.category);
    if (params?.origin_id) query.append("origin_id", params.origin_id);
    if (params?.cursor) query.append("cursor", params.cursor);
    if (params?.limit) query.append("limit", String(params.limit));

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return this.request<ActorListEnvelope>(
      `/routes/${routeId}/actors${queryString}`
    );
  }

  public async getRouteMapPayload(
    routeId: string,
    originId?: string
  ): Promise<RouteMapPayloadEnvelope> {
    const query = originId ? `?origin_id=${encodeURIComponent(originId)}` : "";
    return this.request<RouteMapPayloadEnvelope>(
      `/routes/${routeId}/map${query}`
    );
  }

  public async getActorCategories(): Promise<ActorCategoryListEnvelope> {
    return this.request<ActorCategoryListEnvelope>("/actor-categories");
  }

  public async getActorDetail(actorId: string): Promise<ActorDetailEnvelope> {
    return this.request<ActorDetailEnvelope>(`/actors/${actorId}`);
  }

  public async updateMyPreferences(
    data: UserPreferencesUpdate
  ): Promise<UserPreferencesEnvelope> {
    return this.request<UserPreferencesEnvelope>("/me/preferences", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  public async addFavoriteRoute(
    routeId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-routes/${routeId}`,
      { method: "PUT" }
    );
  }

  public async removeFavoriteRoute(
    routeId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-routes/${routeId}`,
      { method: "DELETE" }
    );
  }

  public async getMyFavoriteRoutes(): Promise<RouteListEnvelope> {
    return this.request<RouteListEnvelope>("/me/favorite-routes");
  }

  public async addFavoriteActor(
    actorId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-actors/${actorId}`,
      { method: "PUT" }
    );
  }

  public async removeFavoriteActor(
    actorId: string
  ): Promise<StandardSuccessResponse> {
    return this.request<StandardSuccessResponse>(
      `/me/favorite-actors/${actorId}`,
      { method: "DELETE" }
    );
  }

  public async getMyFavoriteActors(): Promise<ActorListEnvelope> {
    return this.request<ActorListEnvelope>("/me/favorite-actors");
  }

  public async getMyProfile(): Promise<UserProfileEnvelope> {
    return this.request<UserProfileEnvelope>("/me");
  }

  public async updateMyProfile(
    data: UserProfileUpdate
  ): Promise<UserProfileEnvelope> {
    return this.request<UserProfileEnvelope>("/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  public async createAvatarUploadUrl(
    request: AvatarUploadRequest
  ): Promise<AvatarUploadResponseEnvelope> {
    return this.request<AvatarUploadResponseEnvelope>("/me/avatar-upload", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  public async getMyPreferences(): Promise<UserPreferencesEnvelope> {
    return this.request<UserPreferencesEnvelope>("/me/preferences");
  }

  public async getMyImpact(): Promise<UserImpactEnvelope> {
    return this.request<UserImpactEnvelope>("/me/impact");
  }

  public async getMyTrips(): Promise<TripListEnvelope> {
    return this.request<TripListEnvelope>("/me/trips");
  }

  public async createTrip(routeId: string): Promise<TripEnvelope> {
    return this.request<TripEnvelope>("/me/trips", {
      method: "POST",
      body: JSON.stringify({ route_id: routeId }),
    });
  }

  public async getSupportContent(): Promise<SupportContentEnvelope> {
    return this.request<SupportContentEnvelope>("/content/support");
  }
}

export const apiClient = new ApiClient();


