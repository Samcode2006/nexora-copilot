from fastapi import APIRouter

from app.api.v1 import facts, health, profile, student_data

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(student_data.router)
api_router.include_router(facts.router)
