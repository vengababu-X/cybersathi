"""v1 API router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, community, detection, knowledge, meta

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(detection.router)
api_router.include_router(knowledge.router)
api_router.include_router(community.router)
api_router.include_router(meta.router)
