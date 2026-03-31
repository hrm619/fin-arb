# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial arbitrage research and edge detection platform. Compares user probability estimates against market odds (Kalshi, Polymarket, sportsbooks) to find betting edges and cross-market arbitrage opportunities. Includes transcript ingestion, LLM signal extraction, Kelly criterion sizing, and performance tracking.

## Tech Stack

- **Backend**: FastAPI (Python 3.13+), SQLAlchemy + SQLite, Alembic migrations
- **Frontend**: React 19 + Vite 8, Tailwind CSS + shadcn/ui, Zustand (persisted), TanStack Query v5
- **External APIs**: The Odds API (sportsbook lines), Kalshi (RSA-PSS auth), Polymarket (Gamma API), ESPN, Weather, OpenAI Whisper, Anthropic Claude
- **Package manager**: uv (backend), npm (frontend)
- **Testing**: pytest + pytest-asyncio (294 tests)

## Common Commands

```bash
# Backend
uv sync                          # Install dependencies
uv run pytest                    # Run all tests (228 passing)
uv run pytest tests/test_foo.py  # Run single test file
uv run pytest -k "test_name"    # Run single test by name
uv run alembic upgrade head      # Apply database migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run uvicorn backend.main:app --reload  # Run FastAPI dev server (port 8000)

# Frontend
cd frontend && npm install       # Install dependencies
npm run dev                      # Run Vite dev server (port 5173, proxies /api to :8000)
npx vite build                   # Production build
```

## Architecture

```
backend/
  main.py, config.py, database.py
  models/        # SQLAlchemy ORM (8 tables: slates, events, transcripts, signals, user_estimates, market_lines, outcomes, suggested_estimates)
  schemas/       # Pydantic request/response models (including structural_priors, market_anchor, signal_aggregator, confidence_scorer, composer)
  routers/       # Thin FastAPI routes: slates, events, lines, estimates, edge, signals, transcripts, tracking, sports, composer
  services/      # Business logic: slate, event, line, estimate, edge, signal, transcript, tracking, sports + estimate engine (structural_priors, stats_provider, market_anchor, signal_aggregator, confidence_scorer, composer)
  integrations/  # External API wrappers: odds_api, kalshi (RSA-PSS), polymarket (Gamma API), espn, weather
  utils/         # Pure functions: odds_converter, kelly, edge_calculator
  migrations/    # Alembic migration scripts
frontend/
  src/pages/           # 4 pages: SlateView, EventResearch, EdgeDashboard, TrackingDashboard
  src/components/ui/   # shadcn/ui primitives (button, card, table, checkbox, select, dialog, badge, input, label, separator, skeleton)
  src/components/slate/    # GameBrowser, SelectedGamesPanel, ShortlistPanel, CreateSlateForm, AddEventForm, EventRow
  src/components/research/ # LinesPanel, EstimatePanel, TranscriptPanel, SignalsPanel, StructuralPriorsPanel, SuggestedEstimatePanel
  src/store/           # Zustand (persisted currentSlateId + selectedGames for cross-league selection)
  src/api/             # REST client + TanStack Query hooks (35+ hooks)
  src/lib/             # Tailwind merge utility (cn)
```

## Key Data Flow

1. **Sports browsing**: `GET /api/v1/sports` → `GET /api/v1/sports/{key}/events` (Odds API, cached with TTL)
2. **Slate building**: Browse leagues → checkbox-select games → batch save (`POST /slates/{id}/events/batch`)
3. **Line fetching**: Uses stored `external_event_id` from Odds API (falls back to fuzzy team match for legacy events)
4. **Estimate engine**: Market anchor (sharpest line, vig-free) → structural adjustments (from Contract 2 edge registry) → signal adjustments (directed, type-capped) → suggested estimate with composite confidence
5. **Edge detection**: User estimate vs best market line → raw edge → composite confidence weighting → Kelly sizing
6. **Arb detection**: Pairs opposite outcomes across different bookmakers
7. **Signal extraction**: Transcripts → Claude API → structured signals with direction (injury, scheme, sentiment, line_commentary, motivation)

## API Endpoints

### Core CRUD
- `GET/POST /api/v1/slates` — Slate management
- `GET/POST /api/v1/slates/{id}/events` — Events on a slate
- `POST /api/v1/slates/{id}/events/batch` — Batch event creation (from game browser)
- `POST /api/v1/events/{id}/estimate` — Submit probability estimate (locks on first submit, 409 on retry)
- `POST /api/v1/events/{id}/outcome` — Grade an event result

### Market Data
- `GET /api/v1/sports` — Active sports from Odds API (1hr cache)
- `GET /api/v1/sports/{key}/events?date_from=&date_to=` — Upcoming events (5min cache)
- `POST /api/v1/events/{id}/lines/fetch` — Fetch lines from all sources (Odds API + Kalshi + Polymarket)
- `GET /api/v1/events/{id}/lines` — Stored lines
- `GET /api/v1/events/{id}/lines/arb` — Cross-market arb opportunities

### Estimate Engine
- `GET /api/v1/events/{id}/suggested-estimate` — Get/generate suggested estimate with decomposition
- `POST /api/v1/events/{id}/suggested-estimate` — Force regeneration
- `GET /api/v1/events/{id}/structural-priors` — Applicable validated factors for a matchup
- `PATCH /api/v1/signals/{id}/direction` — Set signal direction (+1 home, -1 away)

### Analysis
- `GET /api/v1/slates/{id}/edge` — Ranked events by weighted edge score (uses composite confidence when available)
- `GET /api/v1/slates/{id}/shortlist` — Top N events
- `GET /api/v1/slates/{id}/arb` — All arb opportunities across slate
- `POST /api/v1/transcripts/{id}/extract` — LLM signal extraction (now includes direction)
- `GET /api/v1/tracking/summary` — Performance metrics
- `GET /api/v1/tracking/export` — CSV export

## Implementation Rules

- **One function = one responsibility.** No function exceeds 30 lines.
- **Typed everything**: all functions have type annotations; use Pydantic/dataclasses for inputs/outputs.
- **Layer separation**: integration functions only talk to APIs (no business logic); service functions contain business logic (no HTTP clients); utility functions are pure (no side effects).
- **Routers are thin**: validation + one service call only.
- **Fail loudly** with specific exceptions. All external API calls wrapped in try/except with logging.
- **No hardcoded values** — use environment variables via config.
- **Utilities are tested first** before building services that depend on them.
- **Frontend**: shadcn/ui components with Tailwind CSS. Dark theme. Zustand for cross-component state. TanStack Query for server state with cache invalidation on mutations.

## Integration Notes

- **Kalshi**: Uses RSA-PSS signing (not bearer token). Key at `KALSHI_RSA_KEY_PATH`. API domain: `api.elections.kalshi.com`.
- **Polymarket**: Uses Gamma API (`gamma-api.polymarket.com`) for market search, CLOB API for order book data.
- **Odds API**: Must request `oddsFormat=american`. Events matched by stored `external_event_id` or fuzzy team name fallback.
- **Line fetching**: Orchestrated across all 3 sources with graceful failure per source.
- **Arb detection**: Pairs lines with different `outcome_name` from different `source` bookmakers.
- **Edge ranking**: Compares user estimate against best market line for the *home team* outcome specifically.

## Environment Variables

Required keys (stored in `.env`, never committed):

```
ANTHROPIC_API_KEY          # Claude API for signal extraction
OPENAI_API_KEY             # Whisper for transcript ingestion
ODDS_API_KEY               # The Odds API for sportsbook lines
KALSHI_API_KEY             # Kalshi API key ID
KALSHI_RSA_KEY_PATH        # Path to Kalshi RSA private key file
KALSHI_BASE_URL            # https://api.elections.kalshi.com/trade-api/v2
POLYMARKET_BASE_URL        # https://clob.polymarket.com
WEATHER_API_KEY            # OpenWeatherMap
DATABASE_URL               # sqlite:///./arb_tool.db
KELLY_BANKROLL             # Starting bankroll for Kelly sizing
ARB_THRESHOLD_PCT          # Min combined prob gap for arb detection
EDGE_THRESHOLD_PCT         # Min edge to include in rankings
LLM_MODEL                  # Claude model for signal extraction
SHORTLIST_SIZE             # Number of events in shortlist
CONTRACTS_DIR              # ~/.fin-arb/contracts (shared contract directory)
EDGE_REGISTRY_PATH         # Path to Contract 2 edge registry JSON
FACTOR_RESEARCH_DB_PATH    # Path to factor-research SQLite DB for team metrics
SHARP_SOURCES              # Comma-separated sharp bookmaker names (default: pinnacle,circa)
MARKET_EFFICIENCY_DISCOUNT # 0-1, fraction of edge assumed already priced in (default: 0.5)
```
