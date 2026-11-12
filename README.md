# agent-runtime

A multi-tenant AI customer support platform. Businesses teach an AI agent about their
business and embed a chat widget on their website; the agent answers their customers and
hands hard conversations to human staff.

One Python codebase runs as three processes:

- **API service** (FastAPI): REST and WebSocket front door. Never waits on the AI model.
- **Agent worker**: runs the conversation loop (retrieve, call model, run tools, stream reply).
- **Ingestion worker**: extracts, chunks, and embeds uploaded documents.

Storage is Postgres 16 with pgvector, Redis (queue, locks, live events), and file storage.

## Local setup

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
cp .env.example .env   # then edit if needed
make install           # install dependencies
make up                # start Postgres (port 55432) and Redis (port 56379)
make migrate           # create the database tables
make run               # start the API on http://127.0.0.1:8000
```

Check it: `curl http://127.0.0.1:8000/health/ready` and open http://127.0.0.1:8000/docs.

Integration tests (in `tests/integration/`) use the `agent_runtime_test` database and are
skipped with a message if Postgres or Redis isn't running.

## Commands

| Command          | What it does                       |
|------------------|------------------------------------|
| `make test`      | Run all tests                      |
| `make test-unit` | Run tests that need no Docker      |
| `make migrate`   | Apply database migrations          |
| `make revision m="..."` | Generate a migration from model changes |
| `make reset-db`  | Delete local data and start fresh  |
| `make lint`      | Lint and format check (ruff)       |
| `make format`    | Auto-fix lint and format           |
| `make typecheck` | Type check (mypy)                  |
| `make check`     | Lint, type check, and test         |
| `make down`      | Stop Postgres and Redis            |
