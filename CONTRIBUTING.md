# Contributing

Contributions should preserve the separation between channel integrations,
agent orchestration, MCP tools, and shared infrastructure.

## Development setup

Install Python 3.12 or newer and `uv`, then install the locked dependencies:

```bash
uv sync
```

Use private local configuration for provider and database credentials. Never
include credentials, tokens, message data, traces, local databases, or logs in
a commit.

## Making changes

- Keep platform-specific parsing and delivery inside channel adapters.
- Pass normalized `OmniMessage` objects into the shared workflow.
- Keep model/provider construction behind the agent's provider boundary.
- Expose remote agent tools through the MCP service rather than importing tool
  implementations into graph nodes.
- Add a migration when changing persisted schema or vector dimensions.
- Mark placeholder and planned behavior explicitly in code and documentation.
- Add deterministic tests with fake external providers when changing behavior.

## Validation

Run the configured non-mutating checks before submitting a change:

```bash
uv run ruff check .
uv run ruff format --check .
```

The repository does not currently contain an automated test suite. When tests
are added, document and run the exact command configured by the project.

Database and provider integration checks must use isolated test resources and
synthetic data. Do not run destructive migrations against shared environments.

## Commit hygiene

- Keep commits focused on one coherent change.
- Keep tests with the behavior they verify.
- Use explicit staging paths and inspect the staged diff before committing.
- Do not commit environment files, caches, generated media, build output, local
  databases, logs, or editor settings.
- Explain why the change is needed and identify any remaining limitation.

## Documentation

Update the README or focused documents when changing configuration, entry
points, API routes, workflow behavior, dependencies, or implementation status.
Document only behavior supported by the repository and completed verification.
