# src/app/gateway/v1/api.py
"""
Top-level API v1 Router Aggregator.
Combines all individual resource routers into a single v1 instance.
"""

from fastapi import APIRouter

from src.app.gateway.v1.routers import whatsapp, discord

api_v1_router = APIRouter()

# Register the explicitly defined thin routers
api_v1_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
api_v1_router.include_router(discord.router, prefix="/discord", tags=["Discord"])