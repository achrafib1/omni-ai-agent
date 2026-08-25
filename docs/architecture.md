# Architecture

## System boundaries

Omni AI Agent separates messaging platforms from conversational reasoning.
Channel-specific payloads terminate at the gateway, while the agent consumes a
shared domain message and state contract.

The runtime is divided into three processes:

1. The FastAPI gateway receives platform and local-development traffic.
2. The FastMCP HTTP service exposes prompts and callable tools.
3. The Discord listener maintains a Discord Gateway connection and forwards
   accepted messages to FastAPI.

PostgreSQL and external AI/observability providers are shared dependencies.

## Message flow

### Platform ingress

Discord messages enter through the standalone listener, which accepts direct
messages and bot mentions and forwards a normalized Discord-shaped payload to
`POST /api/v1/discord/webhook`.

WhatsApp events arrive at `POST /api/v1/whatsapp/webhook`. The WhatsApp adapter
ignores delivery-status events, parses text, image, and audio messages, and can
download referenced media from Meta's Graph API.

The WebSocket routes accept a smaller project-defined JSON structure for local
streaming tests. They are not platform webhooks.

### Gateway orchestration

Each adapter produces an `OmniMessage` containing platform identity, session
identity, message type, text content, and optional media bytes. `MessageBus`
then:

1. Looks up or creates the internal user record.
2. Builds the initial LangGraph state.
3. Uses the conversation session as the LangGraph checkpoint thread.
4. Attaches an Opik callback.
5. Executes the graph to completion or streams custom graph output.
6. Returns the completed text through the originating channel adapter.

HTTP webhook work is scheduled through FastAPI background tasks so the webhook
handler can acknowledge receipt before model processing completes.

## LangGraph workflow

The graph executes these stages:

```text
START
  -> memory extraction
  -> routing
  -> system context injection
  -> semantic memory injection
  -> conversation | image | audio
  -> optional summarization
  -> END
```

- Memory extraction asks Gemini to identify a durable personal fact and sends
  qualifying facts to the MCP memory tool.
- Routing uses structured model output to select conversation, image, or audio.
- Context injection requests the MCP system-activity tool.
- Memory injection performs user-scoped pgvector retrieval through MCP.
- Conversation generation streams Gemini output and records the final AI
  message in graph state.
- Summarization activates after more than 20 stored messages and retains the
  five most recent messages.
- Image and audio nodes currently return placeholder text.

The graph is compiled with `AsyncPostgresSaver`. Its `thread_id` is derived
from the channel session, providing short-term conversation persistence across
requests.

## Long-term memory

User records map a platform identity to an internal UUID. Extracted facts are
embedded with the configured Gemini embedding model and stored in the
`agent_memories` table as 768-dimensional vectors.

Retrieval filters by internal user UUID, orders candidates by cosine distance,
and returns up to three memories. This application-level filtering is important
for isolation, but it is not a substitute for database authorization policies.

## MCP integration

The FastMCP service listens on port 8001 and exposes:

- `store_user_memory`
- `retrieve_user_memories`
- `get_current_system_activity`
- `get_routing_system_prompt`
- `get_omni_character_card`

The LangGraph process creates a network client for
`http://localhost:8001/mcp`. Prompt functions attempt to use Opik-managed
prompts and fall back to repository-defined prompt strings if retrieval is not
available.

## Persistence

SQLAlchemy provides asynchronous application sessions. Alembic manages the
`users` and `agent_memories` tables in the configured schema, and a subsequent
migration changes memory vectors from 384 to 768 dimensions.

The scripts in `scripts/db/` enable required PostgreSQL extensions and prepare
the schema search path. They require database-level privileges and should be
reviewed for the target environment before execution.

## Observability

Opik instrumentation appears in three places:

- LangGraph runs receive an `OpikTracer` callback.
- MCP tools use the `track` decorator.
- Prompt functions can retrieve versioned prompts from Opik.

Tracing can include user messages, generated responses, memories, and tool
arguments. Operators should configure retention and access controls appropriate
for that data.
