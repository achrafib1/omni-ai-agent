# src/app/agent/mcp_client.py
"""
MCP Network Client Bridge for Omni-AI-Agent.

This module acts as the HTTP network client for the LangGraph agent. It connects
to the remote FastMCP microservice to dynamically execute tools and fetch prompts
via the Model Context Protocol.

Designed with dependency injection to allow for easy testing and dynamic URL routing.
"""

from typing import Dict, Any, Optional
from fastmcp import Client
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

class MCPNetworkClient:
    """
    Network-based client for interacting with a remote FastMCP server.
    Ensures complete decoupling between the LangGraph execution environment
    and the tool/prompt storage registry.
    """

    def __init__(self, server_url: str):
        """
        Initializes the client with the target MCP server URL.
        
        Args:
            server_url (str): The HTTP URL of the FastMCP SSE/HTTP endpoint.
        """
        self.server_url = server_url
        logger.debug(f"MCPNetworkClient initialized with target URL: {self.server_url}")

    async def fetch_prompt(self, prompt_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Connects to the MCP server and fetches a dynamically rendered prompt.
        
        Args:
            prompt_name (str): The registered name of the prompt.
            arguments (Dict[str, Any], optional): Key-value pairs to hydrate the prompt.
            
        Returns:
            str: The fully resolved prompt text, or an empty string on failure.
        """
        arguments = arguments or {}
        logger.debug(f"Fetching prompt '{prompt_name}' over MCP Network from {self.server_url}...")
        
        try:
            async with Client(self.server_url) as client:
                result = await client.get_prompt(prompt_name, arguments)
                
                # Extract text from the standard MCP Message block
                if result.messages and len(result.messages) > 0:
                    content = result.messages[0].content
                    return content.text if hasattr(content, "text") else str(content)
                
                logger.warning(f"Prompt '{prompt_name}' returned empty messages.")
                return ""
        except Exception as e:
            logger.error(f"[danger]MCP Network Error (Fetch Prompt '{prompt_name}'):[/danger] {e}", exc_info=True)
            return ""

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """
        Connects to the MCP server and securely executes a registered tool.
        
        Args:
            tool_name (str): The registered name of the tool to execute.
            arguments (Dict[str, Any]): The required arguments for the tool.
            
        Returns:
            str: The stringified output of the tool execution.
        """
        arguments = arguments or {}
        logger.debug(f"Executing tool '{tool_name}' over MCP Network...")
        
        try:
            async with Client(self.server_url) as client:
                result = await client.call_tool(tool_name, arguments)
                
                # FastMCP parses structured results into `.data`
                return str(result.data)
        except Exception as e:
            logger.error(f"[danger]MCP Network Error (Execute Tool '{tool_name}'):[/danger] {e}", exc_info=True)
            return "Failed to execute remote MCP tool."