from fastapi import APIRouter

from app.api.endpoints import wallets
from app.api.endpoints import homepage

api_router = APIRouter()
api_router.include_router(wallets.router)
api_router.include_router(homepage.router)
