# fin-arb

Financial arbitrage research and edge detection platform. Compare your probability estimates against sportsbook odds, prediction markets, and cross-market lines to find betting edges and arbitrage opportunities.

## What it does

1. **Browse real games** — Pull upcoming events from The Odds API across all major sports leagues
2. **Build a slate** — Select games from multiple leagues into a weekly slate
3. **Fetch live odds** — Pull lines from 9+ sportsbooks, Kalshi, and Polymarket in one click
4. **Research events** — Ingest YouTube transcripts, extract signals with Claude, and see market consensus summaries with color-coded matchup cards
5. **Submit estimates** — Lock in your probability estimate for each event
6. **Find edges** — Auto-rank events by edge (your estimate vs market), weighted by confidence, with Kelly criterion stake sizing
7. **Detect arbitrage** — Cross-market arb detection across bookmakers
8. **Track performance** — Win rate, ROI, breakdowns by sport/market/confidence, CSV export

## Quick start

### Prerequisites

- Python 3.13+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) package manager
- API keys (see Environment Variables below)

### Setup

```bash
# Clone and install
git clone https://github.com/hrm619/fin-arb.git
cd fin-arb
uv sync
cd frontend && npm install && cd ..

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
uv run alembic upgrade head

# Run tests
uv run pytest
```

### Run

```bash
# Terminal 1: Backend
uv run uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173**

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, SQLite, Alembic |
| Frontend | React 19, Vite 8, Tailwind CSS, shadcn/ui |
| State | Zustand (persisted), TanStack Query v5 |
| APIs | The Odds API, Kalshi, Polymarket, Claude, Whisper |
| Testing | pytest (228 tests) |

## Architecture

```
backend/
  routers/       → Thin API routes (9 routers)
  services/      → Business logic (9 services)
  integrations/  → External API wrappers (Odds API, Kalshi, Polymarket, ESPN, Weather)
  models/        → SQLAlchemy ORM (7 tables)
  schemas/       → Pydantic models
  utils/         → Pure functions (odds conversion, Kelly criterion, edge calculation)

frontend/
  src/pages/          → SlateView, EventResearch, EdgeDashboard, TrackingDashboard
  src/components/ui/  → shadcn/ui primitives (11 components)
  src/components/     → Domain components (slate building, research panels)
  src/api/            → REST client + 35 React Query hooks
  src/store/          → Zustand store
```

## Key features

### Slate Builder
Browse leagues via dropdown, see real upcoming games, select with checkboxes across multiple leagues, batch-save to a slate. Games store the Odds API event ID for reliable line fetching.

### Market Lines Summary
Color-coded matchup cards showing consensus probability, best odds, best book, and spread range per outcome. Edge callout when you've submitted an estimate.

### Edge Dashboard
Events ranked by weighted edge score (raw edge x confidence tier). Kelly criterion sizing with configurable bankroll. Sortable by edge, Kelly stake, or confidence.

### Cross-Market Arbitrage
Detects arb opportunities by pairing opposite outcomes across different sportsbooks. Scans all events on a slate.

### Signal Extraction
Ingest YouTube transcripts (via Whisper) or paste text. Claude extracts structured signals: injury reports, scheme analysis, sentiment, line commentary — ranked by relevance.

## Environment variables

```bash
ANTHROPIC_API_KEY=         # Claude API
OPENAI_API_KEY=            # Whisper transcription
ODDS_API_KEY=              # The Odds API (https://the-odds-api.com)
KALSHI_API_KEY=            # Kalshi API key ID
KALSHI_RSA_KEY_PATH=       # Path to Kalshi RSA private key
KALSHI_BASE_URL=           # https://api.elections.kalshi.com/trade-api/v2
POLYMARKET_BASE_URL=       # https://clob.polymarket.com
WEATHER_API_KEY=           # OpenWeatherMap
DATABASE_URL=              # sqlite:///./arb_tool.db
KELLY_BANKROLL=            # e.g. 1000.00
ARB_THRESHOLD_PCT=         # e.g. 3.0
EDGE_THRESHOLD_PCT=        # e.g. 3.0
LLM_MODEL=                 # e.g. claude-sonnet-4-20250514
SHORTLIST_SIZE=            # e.g. 6
```

## License

Private repository.
