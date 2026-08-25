# Omni AI Agent

Omni AI Agent is an omnichannel conversational assistant that routes Discord
and WhatsApp messages through a shared LangGraph workflow. It combines
provider-neutral channel adapters, persistent conversation checkpoints,
semantic user memory, MCP-hosted tools and prompts, and optional Opik tracing.

## Current status

The repository contains a working application structure for text conversations,
with Discord and WhatsApp ingress, PostgreSQL persistence, an HTTP FastMCP
service, and WebSocket token streaming. Running the complete system requires
configured external services and credentials.

## Core capabilities

- Normalize Discord and WhatsApp events into one message contract.
- Resolve channel identities to internal user records.
- Orchestrate extraction, routing, context, retrieval, generation, and
  summarization with LangGraph.
- Persist conversation checkpoints in PostgreSQL.
- Store and retrieve user-scoped semantic memories with pgvector and Gemini
  embeddings.
- Expose memory, context, and prompt operations through FastMCP over HTTP.
- Stream generated text over local WebSocket endpoints.
- Trace graph and tool execution with Opik instrumentation.

## Architecture

```text
Discord Gateway / WhatsApp Cloud API / local WebSocket client
                            |
                    FastAPI gateway
                            |
                  channel adapter layer
                            |
                       MessageBus
                    /       |       \
             PostgreSQL  LangGraph  Opik
                            |
                   FastMCP HTTP service
                    /       |       \
                 prompts  context  pgvector memory
                            |
                      Gemini models
```

Incoming platform payloads are parsed into `OmniMessage`, associated with an
internal user, and submitted to a persistent LangGraph thread. The graph
extracts durable facts, chooses a response path, loads contextual tools and
memories over MCP, generates a response, and summarizes long conversations.
The message bus either sends the completed response through the source channel
adapter or forwards generated tokens to a WebSocket client.

More detail is available in [Architecture](docs/architecture.md).

## Technology stack

- Python 3.12 and `uv`
- FastAPI and Uvicorn
- LangGraph and LangChain
- FastMCP
- Gemini and Groq model integrations
- PostgreSQL, SQLAlchemy, Alembic, and pgvector
- Opik tracing
- HTTPX for asynchronous platform API calls

## Repository structure

```text
alembic/                    Database migrations
scripts/db/                 PostgreSQL extension and schema setup
src/app/agent/              LangGraph state, nodes, edges, and MCP client
src/app/gateway/            API routes, channel adapters, and message bus
src/app/mcp_server/         MCP tools, prompts, and HTTP server
src/shared/domain/          Shared schemas and database models
src/shared/infrastructure/  Database and observability infrastructure
main.py                     FastAPI application entry point
dev_launcher.py             Local multi-service launcher
test_client.html            Local HTTP/WebSocket test dashboard
```

## Requirements

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/)
- PostgreSQL with the `vector` and `uuid-ossp` extensions
- Credentials for the configured model and platform integrations
- An Opik workspace when tracing is enabled

The Discord listener imports `discord.py`, but that package is not currently
declared directly in `pyproject.toml`. The listener should be considered
unavailable from a clean dependency installation until the manifest is updated.

## Local development

Install the locked dependencies:

```bash
uv sync
```

Prepare PostgreSQL by applying the scripts in `scripts/db/` with an authorized
database account, then apply the Alembic migrations:

```bash
uv run alembic upgrade head
```

Start the MCP service in one terminal:

```bash
uv run python -m src.app.mcp_server.server
```

Start the API gateway in another terminal:

```bash
uv run python -m main
```

The API is then available at `http://localhost:8000`. The MCP client currently
expects the MCP endpoint at `http://localhost:8001/mcp`.

`dev_launcher.py` starts the MCP server, API gateway, and Discord listener
together, but it also requires the Discord listener dependency noted above.

## Configuration

Settings are loaded from local environment variables by Pydantic Settings.
Never commit real credentials. Use values such as `replace-me-locally` only in
private local configuration.

See [Configuration](docs/configuration.md) for the supported setting names and
which application component consumes each one.

## API and channels

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Application health response |
| `POST /api/v1/discord/webhook` | Accept a normalized Discord message payload |
| `WS /api/v1/discord/stream` | Stream a locally simulated Discord conversation |
| `GET /api/v1/whatsapp/webhook` | Complete WhatsApp webhook verification |
| `POST /api/v1/whatsapp/webhook` | Accept WhatsApp Cloud API events |
| `WS /api/v1/whatsapp/stream` | Run a local WhatsApp-context simulation |

Discord uses a separate Gateway listener to receive organic messages and
forward them to the FastAPI webhook. WhatsApp uses Meta's Cloud API webhooks.
The WebSocket routes are local testing interfaces, not native platform
transport mechanisms.

## Quality checks

The repository configures Ruff and pre-commit:

```bash
uv run ruff check .
uv run ruff format --check .
```

There is currently no committed automated test suite or configured static type
check command. The existing source also has unresolved Ruff findings; consult
[Implementation status](docs/implementation-status.md) before treating a clean
quality run as established.

## Security and privacy

- Keep provider tokens, database URLs, and observability credentials out of
  version control.
- Treat message content, external platform identifiers, semantic memories, and
  traces as potentially sensitive user data.
- Restrict database roles and use encrypted connections outside local
  development.
- Validate webhook authenticity before exposing the gateway publicly.
- Replace the current permissive development CORS policy before deployment.
- Add authentication and authorization before exposing HTTP or WebSocket
  interfaces to untrusted networks.

## Roadmap

- Add webhook signature validation and endpoint authentication.
- Declare and verify the Discord listener dependency.
- Add deterministic tests with fake model, MCP, database, and channel providers.
- Add deployment configuration and operational health checks.
- Add further channel adapters through the shared adapter interface.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development expectations and the
recommended validation workflow.
