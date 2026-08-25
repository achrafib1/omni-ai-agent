# src/main.py
"""
Master Application Entrypoint for Omni-AI-Agent.

Initializes the FastAPI gateway, manages the LangGraph database 
checkpointing lifespan, instantiates the central MessageBus, and 
serves as the target for ASGI servers.
"""

import sys
import os
from contextlib import asynccontextmanager
from typing import Any, cast

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.shared.config import settings
from src.shared.infrastructure.observability.logger import get_logger
from src.app.agent.graph import compile_workflow
from src.app.gateway.api import api_router

# Import our Message Bus
from src.app.gateway.services.message_bus import MessageBus

logger = get_logger("omni_main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the startup and shutdown of databases and LangGraph."""
    logger.info("Initializing Omni-Agent Startup Sequence...")
    
    # Force inject Opik credentials into the OS environment for the LangChain Tracer
    os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY.get_secret_value()
    os.environ["OPIK_WORKSPACE"] = settings.OPIK_WORKSPACE
    os.environ["OPIK_PROJECT_NAME"] = settings.OPIK_PROJECT_NAME

    connection_string = settings.POSTGRES_CONNECTION_STRING.get_secret_value()
    if connection_string.startswith("postgresql+asyncpg://"):
        connection_string = connection_string.replace("postgresql+asyncpg://", "postgresql://")

    logger.info("Provisioning AsyncConnectionPool for LangGraph memory...")
    
    async with AsyncConnectionPool(
        conninfo=connection_string,
        min_size=1,
        max_size=10,
        max_idle=300,
        max_lifetime=1800,
        kwargs={"autocommit": True}
    ) as pool:
        
        checkpointer = AsyncPostgresSaver(conn=cast(Any, pool))
        await checkpointer.setup()
        
        # Compile the graph using the checkpointer
        compiled_agent = compile_workflow(checkpointer=checkpointer)
        
        # Instantiate the central Message Bus with the compiled agent
        message_bus = MessageBus(agent=compiled_agent)
        
        # Store instances in App State for dependency injection in the routers
        app.state.message_bus = message_bus
        app.state.compiled_agent = compiled_agent
        
        logger.info("[success]Gateway lifespan initialization complete.[/success]")
        
        yield  
        
    logger.info("Shutdown initiated. Database pools cleanly closed.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Omni-Channel API Gateway & LangGraph Orchestrator",
    version="1.0.0",
    debug=settings.ENABLE_DEBUG_LOGS,
    lifespan=lifespan
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

#test
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins so our local HTML file works
    allow_credentials=False,   # MUST be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/", summary="Root Health Check", tags=["Health"])
async def root() -> dict[str, str]:
    return {"status": "ok", "message": f"{settings.APP_NAME} is online."}


if __name__ == "__main__":
    logger.info(f"Starting ASGI server for {settings.APP_NAME}...")
    uvicorn.run("main:app", port=8000, reload=True)