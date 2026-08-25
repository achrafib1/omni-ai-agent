# src/app/gateway/api.py
"""
Top-level API router aggregator for Omni-AI-Agent.

This module aggregates all versioned API routers. For now, it only includes
the v1 router, but it is structurally designed to seamlessly accommodate future 
API versions (e.g., v2, v3) without requiring modifications to the main FastAPI 
application lifecycle or entrypoint.
"""

from fastapi import APIRouter

# Import the v1 router aggregator
from src.app.gateway.v1.api import api_v1_router

from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# Create the main API router that will be included in the FastAPI app instance.
api_router = APIRouter()

# Include the v1 router under the "/v1" prefix.
logger.debug("Registering API v1 routes to the top-level router.")
api_router.include_router(api_v1_router, prefix="/v1")

# Future versions can easily be added here:
# from app.gateway.v2.api import api_v2_router
# api_router.include_router(api_v2_router, prefix="/v2")