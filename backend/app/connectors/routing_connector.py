"""Abstract routing connector protocol and dataclasses for routing preview (ECO-2309)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class RouteCalculationResult:
    provider: str
    distance_m: int
    duration_s: int
    geojson: dict[str, Any]
    encoded_polyline: str | None = None
    bounds: dict[str, float] | None = None


class RoutingConnectorError(Exception):
    """Base exception for routing connector errors."""

    def __init__(self, message: str, code: str = "ROUTING_ERROR") -> None:
        super().__init__(message)
        self.code = code


class RoutingProviderUnavailableError(RoutingConnectorError):
    """Raised when routing provider is unavailable or times out."""

    def __init__(self, message: str = "Provedor de roteamento indisponível.") -> None:
        super().__init__(message, code="ROUTING_PROVIDER_UNAVAILABLE")


class RoutingTimeoutError(RoutingConnectorError):
    """Raised when the routing provider exceeds the request deadline."""

    def __init__(self, message: str = "O provedor de roteamento excedeu o tempo limite.") -> None:
        super().__init__(message, code="ROUTING_TIMEOUT")


class RoutingQuotaExceededError(RoutingConnectorError):
    """Raised before a provider call would exceed the approved monthly ceiling."""

    def __init__(self, message: str = "Limite mensal de roteamento atingido.") -> None:
        super().__init__(message, code="ROUTING_MONTHLY_QUOTA_EXCEEDED")


class RoutingNoRouteFoundError(RoutingConnectorError):
    """Raised when no route could be found between points."""

    def __init__(
        self, message: str = "Nenhuma rota encontrada para as coordenadas fornecidas."
    ) -> None:
        super().__init__(message, code="NO_ROUTE_FOUND")


class RoutingConnector(ABC):
    """Abstract base class / protocol for routing calculation connectors."""

    @abstractmethod
    async def calculate_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        travel_mode: str = "DRIVE",
    ) -> RouteCalculationResult:
        """Calculate route between origin and destination coordinates."""
        ...
