# src/shared/infrastructure/observability/opik_setup.py
"""
Opik Tracing and Observability Configuration.

This module initializes the Opik client using our centralized configuration.
By calling `configure_opik()`, we ensure that all LLM calls, LangGraph
state transitions, and MCP tool executions are logged to the correct
workspace and project.
"""

import opik

from shared.config import settings
from shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


def configure_opik() -> None:
    """
    Initializes the Opik tracing configuration.

    This function should be called at the entry point of the FastAPI application
    and the FastMCP server. It explicitly passes the API key, workspace, and
    project name so the SDK does not have to guess.
    """
    try:
        opik.configure(
            api_key=settings.OPIK_API_KEY.get_secret_value(),
            workspace=settings.OPIK_WORKSPACE,
            project_name=settings.OPIK_PROJECT_NAME,
        )
        logger.info(
            f"[success]Opik observability configured successfully for project: "
            f"'{settings.OPIK_PROJECT_NAME}'[/success]"
        )
    except Exception as e:
        logger.error(
            f"[danger]Failed to configure Opik observability:[/danger] {str(e)}",
            exc_info=True,
        )
        raise
