# src/app/gateway/listeners/discord_listener.py
"""
Discord Ingress Listener Service for Omni-AI-Agent.

This acts as a standalone microservice. It connects to the Discord Gateway 
via WebSockets to listen for organic human chat messages in real-time. 

When a message is detected, it triggers the "Typing..." indicator in Discord,
and forwards the payload to our central FastAPI gateway for cognitive processing.
This perfectly decouples Discord's persistent socket requirements from our REST API.
"""

import asyncio
import sys
from typing import Dict, Any
import discord
import httpx

from src.shared.config import settings
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger("discord_listener")

# The internal URL of our centralized FastAPI Gateway
FASTAPI_WEBHOOK_URL = "http://localhost:8000/api/v1/discord/webhook"


class OmniDiscordClient(discord.Client):
    """
    Custom Discord Client that listens to channel messages and forwards
    them to our internal Omni-AI-Agent Gateway.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Reuse a single HTTP client for efficient connection pooling
        self.http_client = httpx.AsyncClient(timeout=15.0)

    async def on_ready(self) -> None:
        """Fired when the bot successfully connects to the Discord Gateway."""
        logger.info(f"[success]Discord Listener online and logged in as {self.user}[/success]")

    async def on_message(self, message: discord.Message) -> None:
        """
        Fired whenever a new message is posted in any channel the bot can see.
        """

        logger.debug(f"[Gateway Event] Message received from '{message.author.name}': {message.content}")
        
        # 1. Prevent infinite feedback loops (don't reply to ourselves or other bots)
        if message.author.bot:
            return

        # Maintain standard channel hygiene: Only respond to DMs or direct mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.user in message.mentions if self.user else False

        if is_dm or is_mentioned:
            # Strip out the mention tag if present to keep agent prompts clean
            clean_content = message.content
            if is_mentioned and self.user is not None:
                clean_content = clean_content.replace(f"<@{self.user.id}>", "").strip()
                clean_content = clean_content.replace(f"<@!{self.user.id}>", "").strip()

            logger.info(f"Detected message from {message.author.name} in channel {message.channel.id}")

            try:
                # 2. Trigger a 10-second non-blocking "Typing..." indicator in Discord
                await message.channel.typing()
                logger.debug("Successfully triggered Discord typing indicator.")
                
                # 3. Construct the exact JSON payload our FastAPI DiscordAdapter expects
                payload: Dict[str, Any] = {
                    "channel_id": str(message.channel.id),
                    "author": {
                        "id": str(message.author.id),
                        "bot": message.author.bot
                    },
                    "content": clean_content.strip()
                }

                # 4. Forward the payload to our FastAPI Gateway
                logger.debug(f"Forwarding payload to API Gateway: {FASTAPI_WEBHOOK_URL}")
                response = await self.http_client.post(
                    FASTAPI_WEBHOOK_URL, 
                    json=payload
                )
                response.raise_for_status()
                logger.info(f"[success]Payload accepted by FastAPI REST API (HTTP {response.status_code})[/success]")
                
            except httpx.HTTPStatusError as e:
                logger.error(f"[danger]API Gateway rejected payload:[/danger] HTTP {e.response.status_code}")
            except Exception as e:
                logger.error(f"[danger]Failed to reach API Gateway:[/danger] {e}", exc_info=True)

    async def close(self) -> None:
        """Safely tears down connection pools on exit."""
        logger.info("Closing HTTP connection pools...")
        await self.http_client.aclose()
        await super().close()


async def main() -> None:
    """Bootstraps the Discord Ingress Listener."""
    logger.info("Initializing Discord Ingress Listener...")
    
    # Securely retrieve the token
    token = getattr(settings, "DISCORD_BOT_TOKEN", None)
    if not token:
        logger.error("[danger]DISCORD_BOT_TOKEN not found in environment settings.[/danger]")
        sys.exit(1)
        
    token_value = token.get_secret_value() if hasattr(token, "get_secret_value") else str(token)

    # We MUST enable the message_content intent to read what users type
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    client = OmniDiscordClient(intents=intents)
    
    try:
        # Start the listener loop
        await client.start(token_value)
    except KeyboardInterrupt:
        logger.info("Discord Listener shutting down gracefully...")
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[success]Listener cleanly terminated.[/success]")
        sys.exit(0)