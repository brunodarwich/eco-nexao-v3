"""FastAPI application entry point with middleware, CORS, logging, and error handling."""

import asyncio
import sys
import uuid
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.logging import request_id_ctx_var, setup_logging

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

setup_logging(settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API de domínio do aplicativo ECOnexão para turismo sustentável e rotas ecológicas."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Any) -> Any:
    """Middleware to extract or generate X-Request-ID and propagate it."""
    incoming_id = request.headers.get("X-Request-ID")
    request_id = incoming_id if incoming_id and incoming_id.strip() else f"req_{uuid.uuid4().hex}"

    token = request_id_ctx_var.set(request_id)
    request.state.request_id = request_id

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_ctx_var.reset(token)


HTTP_STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _get_request_id(request: Request) -> str:
    req_id: str | None = getattr(request.state, "request_id", None)
    if req_id:
        return req_id
    ctx_id = request_id_ctx_var.get()
    if ctx_id:
        return ctx_id
    return f"req_{uuid.uuid4().hex}"


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Custom exception handler for Starlette/FastAPI HTTPExceptions."""
    req_id = _get_request_id(request)
    code = HTTP_STATUS_CODE_MAP.get(exc.status_code, f"HTTP_{exc.status_code}")
    details = getattr(exc, "details", None)

    content = {
        "error": {
            "code": code,
            "message": str(exc.detail),
            "details": details,
        },
        "request_id": req_id,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={**(exc.headers or {}), "X-Request-ID": req_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Custom exception handler for 422 RequestValidationError adhering to ErrorResponse schema."""
    req_id = _get_request_id(request)
    content = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Dados de requisição inválidos",
            "details": exc.errors(),
        },
        "request_id": req_id,
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=content,
        headers={"X-Request-ID": req_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom exception handler for unhandled errors to avoid leaking internal details."""
    req_id = _get_request_id(request)
    content = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Ocorreu um erro interno no servidor.",
            "details": None,
        },
        "request_id": req_id,
    }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
        headers={"X-Request-ID": req_id},
    )


# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1")
