# src/app/mcp_server/server.py
"""
FastMCP Server Entrypoint for Omni-AI-Agent.
"""

import sys
from fastmcp import FastMCP

from shared.infrastructure.observability.logger import get_logger

# Import the prompt synchronizers
from app.mcp_server.prompts.prompt_sync import (
    get_routing_system_prompt, 
    get_omni_character_card
)

# Import our specialized tools
from app.mcp_server.tools.memory_rag import store_user_memory, retrieve_user_memories
from app.mcp_server.tools.system_tools import get_current_system_activity

logger = get_logger("mcp_server")

# ============================================================================
# FASTMCP SERVER INITIALIZATION
# ============================================================================
mcp = FastMCP(
    name="OmniAgent-MCP-Engine"
)

def register_prompts(mcp_instance: FastMCP) -> None:
    """Registers dynamic prompts into the MCP Server."""
    
    # FIX: Pass the function directly into the prompt method.
    # FastMCP infers the name from the function name.
    mcp_instance.prompt(get_routing_system_prompt)
    mcp_instance.prompt(get_omni_character_card)
    
    logger.info("[info]MCP Prompts successfully registered.[/info]")

def register_tools(mcp_instance: FastMCP) -> None:
    """Registers Python functions as LLM-callable MCP tools."""
    
    # FIX: Pass the function directly into the tool method.
    # FastMCP parses parameters, type hints, and docstrings automatically.
    mcp_instance.tool(get_current_system_activity)
    mcp_instance.tool(store_user_memory)
    mcp_instance.tool(retrieve_user_memories)
    
    logger.info("[info]MCP Tools successfully registered.[/info]")

# ============================================================================
# SERVER BOOTSTRAP
# ============================================================================
try:
    logger.info("Initializing OmniAgent FastMCP Components...")
    register_prompts(mcp)
    register_tools(mcp)
    logger.info("[success]FastMCP Engine successfully bootstrapped and ready.[/success]")
except Exception as e:
    logger.error(f"[danger]Critical failure during MCP component registration:[/danger] {e}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting FastMCP Server on standard I/O...")
    mcp.run()