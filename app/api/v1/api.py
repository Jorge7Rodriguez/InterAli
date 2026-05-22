from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.claims import router as claims_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.food_listings import router as food_listings_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(food_listings_router)
api_router.include_router(claims_router)
