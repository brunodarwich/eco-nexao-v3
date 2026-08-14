"""API v1 router composition."""

from fastapi import APIRouter

from app.api.v1.actors import router as actors_router
from app.api.v1.admin import router as admin_router
from app.api.v1.admin_actors import router as admin_actors_router
from app.api.v1.admin_media import router as admin_media_router
from app.api.v1.admin_territorial import router as admin_territorial_router
from app.api.v1.admin_workflow import router as admin_workflow_router
from app.api.v1.auth import router as auth_router
from app.api.v1.content import router as content_router
from app.api.v1.health import router as health_router
from app.api.v1.me import router as me_router
from app.api.v1.regions import router as regions_router
from app.api.v1.routes import router as routes_router

api_v1_router = APIRouter()
api_v1_router.include_router(admin_router)
api_v1_router.include_router(admin_actors_router)
api_v1_router.include_router(admin_territorial_router)
api_v1_router.include_router(admin_workflow_router)
api_v1_router.include_router(admin_media_router)
api_v1_router.include_router(health_router)

api_v1_router.include_router(auth_router)
api_v1_router.include_router(regions_router)
api_v1_router.include_router(routes_router)
api_v1_router.include_router(actors_router)
api_v1_router.include_router(me_router)
api_v1_router.include_router(content_router)
