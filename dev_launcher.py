# dev_launcher.py
"""
Process Orchestration Launcher for Omni-AI-Agent.

Starts the FastAPI Gateway, the FastMCP Microservice, and the Discord Listener
concurrently as isolated background processes. Aggregates logs and handles
shutdown signals cleanly.
"""

import asyncio
import sys


async def run_process(command: list[str], prefix: str) -> None:
    """Spawns an isolated process and pipes its output with a prefix."""
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    try:
        # Read the subprocess output stream continuously
        while True:
            line = await process.stdout.readline() if process.stdout else b""
            if not line:
                break
            # Print with prefix so you can distinguish log origins
            print(f"[{prefix}] {line.decode('utf-8', errors='ignore').strip()}")
    except asyncio.CancelledError:
        process.terminate()
        await process.wait()


async def main() -> None:
    print("====================================================================")
    print("Starting Omni-AI-Agent Local Development Services...")
    print("Press CTRL+C to terminate all services safely.")
    print("====================================================================")

    # Define the execution commands for your three services
    mcp_command = ["uv", "run", "python", "-m", "src.app.mcp_server.server"]
    fastapi_command = ["uv", "run", "python", "-m", "main"]
    listener_command = ["uv", "run", "python", "-m", "src.app.gateway.listeners.discord_listener"]

    # Schedule tasks
    mcp_task = asyncio.create_task(run_process(mcp_command, "MCP-SERVER"))

    # Delay startup of API and Listener slightly to give the MCP service a head start
    await asyncio.sleep(2)
    api_task = asyncio.create_task(run_process(fastapi_command, "API-GATEWAY"))

    await asyncio.sleep(1)
    listener_task = asyncio.create_task(run_process(listener_command, "DISCORD-IN"))

    try:
        await asyncio.gather(mcp_task, api_task, listener_task)
    except KeyboardInterrupt:
        print("\nStopping all background services cleanly...")
    finally:
        mcp_task.cancel()
        api_task.cancel()
        listener_task.cancel()
        # Allow cancellation cleanups to finalize
        await asyncio.gather(mcp_task, api_task, listener_task, return_exceptions=True)
        print("All background services stopped successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
