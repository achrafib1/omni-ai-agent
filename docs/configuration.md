# Configuration

Omni AI Agent loads settings from environment variables using Pydantic
Settings. Keep all real values in private local or deployment configuration;
never commit tokens, connection strings, or provider credentials.

Examples below describe value shapes only. `replace-me-locally` and
`example-not-a-real-key` are intentionally invalid placeholders.

## Core runtime

| Setting | Purpose | Example |
| --- | --- | --- |
| `APP_NAME` | Public application name | `Omni-AI-Agent` |
| `ENABLE_DEBUG_LOGS` | Enable verbose application and SQL logging | `false` |
| `CORS_ORIGINS` | Comma-separated allowed browser origins | `http://localhost:8000` |
| `DB_SCHEMA` | PostgreSQL schema for application tables | `omni` |
| `POSTGRES_CONNECTION_STRING` | PostgreSQL connection URL | `postgresql://replace-me-locally` |

The FastAPI entry point currently installs a permissive `*` CORS policy for the
local HTML dashboard instead of applying `CORS_ORIGINS`. Change that policy
before exposing the application publicly.

## Model providers

| Setting | Current use |
| --- | --- |
| `GEMINI_API_KEY` | Conversation, routing, extraction, summarization, and embeddings |
| `GROQ_API_KEY` | Groq factory exists, but active graph nodes currently use Gemini |
| `TOGETHER_API_KEY` | Declared but not connected to the current workflow |
| `ELEVENLABS_API_KEY` | Declared for planned audio work |
| `ELEVENLABS_VOICE_ID` | Declared for planned audio work |

Example private value:

```text
GEMINI_API_KEY=example-not-a-real-key
```

## Discord

| Setting | Purpose |
| --- | --- |
| `DISCORD_BOT_TOKEN` | Authenticate the Gateway listener and outbound REST calls |

The Discord application must enable message-content intent for the listener to
read messages. The listener responds only to direct messages and messages that
mention the bot.

## WhatsApp

| Setting | Purpose |
| --- | --- |
| `WHATSAPP_PHONE_NUMBER_ID` | Select the Cloud API sender number |
| `WHATSAPP_TOKEN` | Authenticate Graph API media and message requests |
| `WHATSAPP_VERIFY_TOKEN` | Validate the webhook subscription challenge |

The current webhook verifies the subscription token but does not validate the
signature of incoming POST requests.

## Opik

| Setting | Purpose |
| --- | --- |
| `OPIK_API_KEY` | Authenticate tracing and prompt access |
| `OPIK_WORKSPACE` | Select the Opik workspace |
| `OPIK_PROJECT_NAME` | Group traces under a project name |

Prompt retrieval falls back to local strings when the Opik prompt client is not
available. Graph callback and tool tracing still need valid provider setup for
remote observability.

## Supabase settings

`SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are declared in the settings model,
but current persistence uses the PostgreSQL connection string directly through
SQLAlchemy and LangGraph. They are not required by the traced execution path.

## Database preparation

The database requires `vector` and `uuid-ossp`. Review and apply
`scripts/db/001_enable_extensions.sql` and
`scripts/db/002_configure_search_path.sql` with an appropriately privileged
account. The second script targets the PostgreSQL `postgres` role and may need
adaptation for managed or shared environments.

Apply migrations only after the schema and extensions are ready:

```bash
uv run alembic upgrade head
```
