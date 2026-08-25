# src/app/mcp_server/server.py
"""
FastMCP Server Entrypoint for Omni-AI-Agent.

This module spins up an independent microservice exposing our RAG tools, 
system context, and Opik-managed prompts over the Model Context Protocol (MCP).
It uses a highly scalable, modular registration pattern.
"""

import sys
from fastmcp import FastMCP
import opik 
import os 

from src.shared.infrastructure.observability.logger import get_logger
from src.shared.config import settings  # Import  settings configuration

# Import the prompt synchronizers
from src.app.mcp_server.prompts.prompt_sync import (
    get_routing_system_prompt, 
    get_omni_character_card
)

# Import our specialized tools
from src.app.mcp_server.tools.memory_rag import store_user_memory, retrieve_user_memories
from src.app.mcp_server.tools.system_tools import get_current_system_activity

logger = get_logger("mcp_server")

# ============================================================================
# FASTMCP SERVER INITIALIZATION
# ============================================================================
mcp = FastMCP(
    name="OmniAgent-MCP-Engine"
)

def register_prompts(mcp_instance: FastMCP) -> None:
    """
    Registers dynamic prompts into the MCP Server.
    Keeps prompt registration isolated and highly maintainable.
    """
    try:
        mcp_instance.prompt(get_routing_system_prompt)
        mcp_instance.prompt(get_omni_character_card)
        logger.info("[success]MCP Prompts successfully registered.[/success]")
    except Exception as e:
        logger.error(f"[danger]Failed to register prompts:[/danger] {e}", exc_info=True)
        raise

def register_tools(mcp_instance: FastMCP) -> None:
    """
    Registers Python functions as LLM-callable MCP tools.
    FastMCP parses parameters, type hints, and docstrings automatically.
    """
    try:
        mcp_instance.tool(get_current_system_activity)
        mcp_instance.tool(store_user_memory)
        mcp_instance.tool(retrieve_user_memories)
        logger.info("[success]MCP Tools successfully registered.[/success]")
    except Exception as e:
        logger.error(f"[danger]Failed to register tools:[/danger] {e}", exc_info=True)
        raise

# ============================================================================
# SERVER BOOTSTRAP
# ============================================================================
def bootstrap_server() -> None:
    """Bootstraps the MCP server by registering all components safely."""
    try:
        logger.info("Initializing OmniAgent FastMCP Components...")
        
        os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY.get_secret_value()
        os.environ["OPIK_WORKSPACE"] = settings.OPIK_WORKSPACE
        os.environ["OPIK_PROJECT_NAME"] = settings.OPIK_PROJECT_NAME

        # # Explicitly configure Opik inside this process using your Pydantic settings
        # opik.configure(
        #     api_key=settings.OPIK_API_KEY.get_secret_value(),
        #     workspace=settings.OPIK_WORKSPACE,
        #     project_name=settings.OPIK_PROJECT_NAME
        # )
        logger.info("[success]Opik Tracing successfully configured programmatically.[/success]")

        register_prompts(mcp)
        register_tools(mcp)
        logger.info("[success]FastMCP Engine successfully bootstrapped and ready.[/success]")
    except Exception as e:
        logger.error(f"[danger]Critical failure during MCP bootstrap:[/danger] {e}", exc_info=True)
        sys.exit(1)

# Execute bootstrap immediately upon module load
bootstrap_server()

if __name__ == "__main__":
    logger.info("Starting FastMCP Microservice on HTTP Port 8001...")
    mcp.run(transport="http", port=8001)
