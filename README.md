# Ticketing LLM

FastAPI service that triages support tickets with an LLM (Anthropic or OpenAI) using
structured output validated by Pydantic, and stores every analysis in PostgreSQL.

## Run with Docker

```bash
cp .env.example .env        # set LLM_PROVIDER and the matching API key
docker compose up --build
```

Migrations run automatically on startup (`alembic upgrade head`). API docs: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/tickets/analyze` | Analyze a description, persist it, return the analysis (201) |
| GET | `/tickets?category=&severity=&limit=&offset=` | List analyzed tickets |
| GET | `/tickets/{id}` | Get one ticket |
| GET | `/health` | DB connectivity check |

```bash
curl -X POST http://localhost:8000/tickets/analyze \
  -H "Content-Type: application/json" \
  -d '{"description": "Database connection timeout on the checkout service"}'
```

```json
{
  "category": "database",
  "severity": "high",
  "summary": "...",
  "recommended_actions": ["..."],
  "id": "6f1c..."
}
```

`category` is one of `database, network, authentication, performance, application,
infrastructure, security, other`; `severity` is one of `low, medium, high, critical`.
If the LLM call fails the API returns 502.

## LLM providers

Switch with `LLM_PROVIDER=anthropic|openai`. Both providers implement `LLMProvider`
([app/llm/base.py](app/llm/base.py)) and receive the same Pydantic model
(`TicketAnalysis`) as their structured output format:

- Anthropic: `client.beta.messages.parse(output_format=TicketAnalysis, ...)` with
  server-side refusal fallbacks enabled. Default model `claude-opus-5-5`, effort `low`.
- OpenAI: `client.responses.parse(text_format=TicketAnalysis, ...)`. Model from `OPENAI_MODEL`.

## Development

Common tasks are in the Makefile (`make help` lists them all):

```bash
make install           # uv sync
make up / make down    # full stack in Docker
make run               # API locally with reload, Postgres in Docker
make test              # fake LLM + in-memory SQLite, no API keys needed
make check             # lint + format check + tests
make migration m="add priority"   # autogenerate a migration
```
