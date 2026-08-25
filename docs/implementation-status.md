# Implementation status

This document records what the repository currently implements and where work
remains. A source module alone is not treated as evidence of production
deployment or live provider verification.

## Supported in code

| Capability | Status | Notes |
| --- | --- | --- |
| FastAPI health endpoint | Implemented | Returns application status at `GET /` |
| Discord payload parsing | Implemented | Text messages and bot-message filtering |
| Discord Gateway listener | Partial | Implemented but its package is not declared directly |
| Discord outbound text | Implemented | Uses Discord REST API v10 |
| WhatsApp webhook verification | Implemented | Compares Meta challenge token |
| WhatsApp inbound text | Implemented | Parses Cloud API message events |
| WhatsApp outbound text | Implemented | Uses Meta Graph API v21.0 |
| WhatsApp media download | Implemented | Downloads image/audio bytes from Meta |
| WebSocket text streaming | Implemented | Local project-defined test transport |
| LangGraph orchestration | Implemented | Persistent graph with conditional routing |
| PostgreSQL checkpoints | Implemented | Configured with `AsyncPostgresSaver` |
| User persistence | Implemented | Async SQLAlchemy lookup/create flow |
| Semantic memory | Implemented | Gemini embeddings and pgvector retrieval |
| MCP prompts and tools | Implemented | FastMCP HTTP server on port 8001 |
| Opik instrumentation | Configured | Requires external credentials and connectivity |

## Partial and placeholder behavior

- Image requests route to `image_node`, which returns a placeholder message.
- Audio requests route to `audio_node`, which returns a placeholder message.
- Downloaded WhatsApp media is not added to LangGraph state or processed by a
  multimodal model.
- The Groq model factory is present, but graph nodes currently instantiate the
  Gemini model instead.
- Opik prompts have local fallbacks, so prompt retrieval failure does not by
  itself stop the graph.
- The HTML dashboard exercises HTTP and WebSocket paths but is not an
  application frontend or an automated test.
- Telegram and CLI are domain enum values without channel adapters or routes.

## Known limitations

- There is no committed automated test suite.
- The source currently fails the configured Ruff checks.
- Several files contain trailing whitespace and inconsistent formatting.
- The Discord listener imports `discord.py` without a matching direct project
  dependency.
- The Makefile gateway target references `src.app.gateway.api:app`, while the
  FastAPI application object is defined in `main.py`.
- HTTP and WebSocket routes do not implement application authentication.
- WhatsApp POST webhook signatures are not verified.
- Discord webhook requests are not authenticated independently of the internal
  listener topology.
- Development CORS allows all origins.
- Fixed localhost service URLs limit deployment configuration.
- External provider, database, migration, and platform behavior has not been
  verified by an automated integration environment in this repository.

## Verification baseline

During the documentation review:

- Repository entry points, routers, graph wiring, adapters, MCP registration,
  models, and migrations were inspected.
- `git diff --check` reported existing whitespace errors.
- `uv run ruff check .` completed and reported 287 findings.
- No test command was documented because the repository contains no tests.
- End-to-end calls were not made to AI providers, Opik, Discord, WhatsApp, or
  PostgreSQL.

## Planned work

- Implement media-aware image and audio nodes.
- Add request authentication and webhook signature validation.
- Make internal service URLs configurable.
- Add unit, graph, API, adapter, and integration tests using fake providers.
- Resolve lint and formatting findings.
- Verify migrations against an isolated PostgreSQL/pgvector database.
- Add deployment and operational documentation after those paths exist.
