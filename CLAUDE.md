# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial arbitrage research and edge detection platform. Compares user probability estimates against market odds (Kalshi, Polymarket, sportsbooks) to find betting edges and cross-market arbitrage opportunities. Includes transcript ingestion, LLM signal extraction, Kelly criterion sizing, and performance tracking.

## Tech Stack

- **Backend**: FastAPI (Python 3.13+), SQLAlchemy + SQLite, Alembic migrations
- **Frontend**: React 18 + Vite, Zustand state, TanStack Query
- **External APIs**: The Odds API, Kalshi, Polymarket, ESPN, Weather, OpenAI Whisper, Anthropic Claude
- **Package manager**: uv (not pip)
- **Testing**: pytest + pytest-asyncio

## Common Commands

```bash
uv sync                          # Install dependencies
uv run fin-arb                   # Run CLI entrypoint
uv run pytest                    # Run all tests
uv run pytest tests/test_foo.py  # Run single test file
uv run pytest -k "test_name"    # Run single test by name
uv run alembic upgrade head      # Apply database migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run uvicorn backend.main:app --reload  # Run FastAPI dev server
```

## Architecture

Target structure (see `technical-spec.md` for full detail):

```
backend/
  main.py, config.py, database.py
  models/        # SQLAlchemy ORM (7 tables: slates, events, transcripts, signals, user_estimates, market_lines, outcomes)
  schemas/       # Pydantic request/response models
  routers/       # Thin FastAPI routes (validation + one service call)
  services/      # Business logic (8 modules, ~53 functions)
  integrations/  # External API wrappers (odds, kalshi, polymarket, espn, weather, whisper)
  utils/         # Pure functions: odds conversion, Kelly criterion, edge calculation
frontend/
  src/pages/     # 4 pages: Slate, Event Research, Edge Dashboard, Tracking
  src/components/
  src/store/     # Zustand
  src/api/       # TanStack Query hooks
```

**Data flow**: Transcripts → Signal extraction (Claude) → User probability estimates → Market lines (multi-source) → Edge computation → Kelly sizing → Performance tracking

## Implementation Rules (from claude-code-prompt.md)

- **One function = one responsibility.** No function exceeds 30 lines.
- **Typed everything**: all functions have type annotations; use Pydantic/dataclasses for inputs/outputs.
- **Layer separation**: integration functions only talk to APIs (no business logic); service functions contain business logic (no HTTP clients); utility functions are pure (no side effects).
- **Routers are thin**: validation + one service call only.
- **Fail loudly** with specific exceptions. All external API calls wrapped in try/except with logging.
- **No hardcoded values** — use environment variables via config.
- **Utilities are tested first** before building services that depend on them.

## Implementation Sequence

Build in this order (each phase complete before next):
1. Database models + Alembic migrations
2. Utility functions (odds converter, Kelly, edge calculator) — **test first**
3. Slate + Event services/routes
4. Odds API integration + Line service
5. Estimate service
6. Edge service + routes
7. Transcript ingestion
8. Signal extraction (Claude API)
9. Kalshi + Polymarket integrations
10. Tracking service
11. ESPN + Weather integrations
12. Frontend (React)

## Environment Variables

Required keys (stored in `.env`, never committed): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ODDS_API_KEY`, `KALSHI_API_KEY`, `KALSHI_BASE_URL`, `POLYMARKET_BASE_URL`, `WEATHER_API_KEY`, `DATABASE_URL`, `KELLY_BANKROLL`, `ARB_THRESHOLD_PCT`, `EDGE_THRESHOLD_PCT`, `LLM_MODEL`, `SHORTLIST_SIZE`
