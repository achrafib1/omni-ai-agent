"""
Core Logging Module for Omni-AI-Agent.

This module provides an enterprise-grade, highly elegant logging setup 
utilizing the 'rich' library. It ensures consistent, color-coded, and 
highly informative logs across the Gateway, LangGraph Agent, and MCP Server.
"""

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Define an elegant custom theme for our terminal output
_custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "danger": "bold red",
        "success": "bold green",
    }
)

# Shared rich console instance
console = Console(theme=_custom_theme)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a rich-enabled standard Python logger.

    This function configures the logger to output beautifully formatted
    tracebacks, precise timestamps, and caller file locations, which is
    critical for debugging complex asynchronous LLM agent flows.

    Args:
        name (str): The name of the logger (typically __name__ from the caller).
        level (int): The logging level threshold. Defaults to logging.INFO.

    Returns:
        logging.Logger: A configured standard library Logger instance.
    
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Omni-Agent successfully initialized.")
    """
    logger = logging.getLogger(name)

    # Prevent adding multiple handlers if the logger is already initialized
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(level)

    # Configure the RichHandler for beautiful terminal output
    # rich_tracebacks=True provides highly detailed error tracebacks without clutter
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )

    # Define the log message format. 
    # We omit the time and path here because RichHandler displays them natively in columns.
    formatter = logging.Formatter("%(message)s")
    rich_handler.setFormatter(formatter)

    logger.addHandler(rich_handler)
    
    # Prevent log messages from propagating to the root logger to avoid duplicates
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves the configured logger. 
    
    If it is not configured yet, it applies the default setup.

    Args:
        name (Optional[str]): The module name. Defaults to 'omni_agent'.

    Returns:
        logging.Logger: The configured logger.
    """
    logger_name = name or "omni_agent"
    return logging.getLogger(logger_name) if logging.getLogger(logger_name).hasHandlers() else setup_logger(logger_name)