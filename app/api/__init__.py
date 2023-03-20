from fastapi import APIRouter

from app.api import tokens

api_router = APIRouter()

api_router.include_router(tokens.router, tags=["tokens"])
