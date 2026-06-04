.PHONY: install format lint test run-gateway run-mcp pre-commit-install

# Install all dependencies using uv
install:
	uv sync

# Install the pre-commit git hooks
pre-commit-install:
	uv run pre-commit install

# Automatically format the entire codebase
format:
	uvx ruff format src/
	uvx ruff check src/ --fix

# Check for linting errors without modifying files
lint:
	uvx ruff check src/

# Run the API Gateway locally
run-gateway:
	uv run uvicorn src.app.gateway.api:app --reload --host 0.0.0.0 --port 8000

# Run the FastMCP Tools server locally
run-mcp:
	uv run fastmcp run src.app.mcp_server.server:mcp