# Next Steps

## Credentials Setup

- [ ] Create `.env` from template below and add real keys
- [ ] `OPENAI_API_KEY` — needed for transcript ingestion via yt_transcriber (Whisper API)
- [ ] `ANTHROPIC_API_KEY` — needed for signal extraction from transcripts
- [ ] `ODDS_API_KEY` — needed for live line fetching from The Odds API (https://the-odds-api.com)
- [ ] `KALSHI_API_KEY` — needed for Kalshi market lines
- [ ] `WEATHER_API_KEY` — needed for OpenWeatherMap forecasts (outdoor sports only)
- [ ] Verify `ffmpeg` is installed (`brew install ffmpeg`) — required by yt_transcriber for audio chunking

```bash
# .env
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
ODDS_API_KEY=
KALSHI_API_KEY=
KALSHI_BASE_URL=https://trading-api.kalshi.com/trade-api/v2
POLYMARKET_BASE_URL=https://clob.polymarket.com
WEATHER_API_KEY=
DATABASE_URL=sqlite:///./arb_tool.db
KELLY_BANKROLL=1000.00
ARB_THRESHOLD_PCT=3.0
EDGE_THRESHOLD_PCT=3.0
LLM_MODEL=claude-sonnet-4-20250514
SHORTLIST_SIZE=6
```

## End-to-End Testing Plan

### 1. Backend smoke test (no keys needed)
- [ ] Start backend: `uv run uvicorn backend.main:app --reload`
- [ ] Verify `/health` returns 200
- [ ] Verify `/docs` loads Swagger UI with all endpoints visible
- [ ] Create a slate via POST `/api/v1/slates`
- [ ] Add an event via POST `/api/v1/slates/{id}/events`
- [ ] Submit an estimate via POST `/api/v1/events/{id}/estimate`
- [ ] Confirm estimate is locked (re-submit returns 409)
- [ ] Grade the event via POST `/api/v1/events/{id}/outcome`
- [ ] Verify tracking summary updates at GET `/api/v1/tracking/summary`
- [ ] Export CSV at GET `/api/v1/tracking/export`

### 2. Frontend smoke test (no keys needed)
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Create a slate from the Slates page
- [ ] Add an event to the slate
- [ ] Click through to Event Research page
- [ ] Submit a probability estimate — confirm it locks
- [ ] Navigate to Edge Dashboard — confirm empty state message
- [ ] Navigate to Tracking Dashboard — confirm zero-state metrics

### 3. Line fetching (requires ODDS_API_KEY)
- [ ] Add ODDS_API_KEY to `.env`
- [ ] Create an event with sport=`americanfootball_nfl` (Odds API sport key)
- [ ] Click "Fetch Lines" on the Event Research page
- [ ] Verify lines appear in the market lines table
- [ ] Check arb detection at GET `/api/v1/events/{id}/lines/arb`
- [ ] With estimate + lines present, verify Edge Dashboard ranks the event

### 4. Transcript + signal pipeline (requires OPENAI_API_KEY + ANTHROPIC_API_KEY)
- [ ] Add both keys to `.env`
- [ ] On Event Research page, paste a YouTube URL and click Ingest
- [ ] Wait for transcription to complete (may take 1-2 min for long videos)
- [ ] Expand transcript to verify text quality
- [ ] Click "Extract Signals" on the transcript
- [ ] Verify signals appear ranked by relevance with type badges
- [ ] Flag a signal as "used_in_pricing" — confirm highlight updates

### 5. Kalshi + Polymarket (requires KALSHI_API_KEY)
- [ ] Add KALSHI_API_KEY to `.env`
- [ ] Create an event for a market that exists on Kalshi/Polymarket
- [ ] Fetch lines — verify kalshi/polymarket sources appear alongside sportsbook lines
- [ ] Check cross-market arb detection across different sources

### 6. Full loop end-to-end
- [ ] Create a slate with 3-5 real upcoming events
- [ ] Fetch lines for each event
- [ ] Ingest at least one transcript per event and extract signals
- [ ] Submit probability estimates for each event
- [ ] Verify Edge Dashboard shows ranked events with Kelly sizing
- [ ] Verify Shortlist panel on Slate page shows top picks
- [ ] After events conclude, grade outcomes
- [ ] Verify Tracking Dashboard shows hit rate, ROI, and breakdowns
- [ ] Export CSV and verify data integrity

## Polish & Hardening (future iteration)

- [ ] Add CORS middleware to FastAPI for production deployment
- [ ] Add error toasts/notifications in frontend
- [ ] Add loading skeletons for better UX
- [ ] Add responsive design for mobile
- [ ] Add line movement tracking (historical lines over time)
- [ ] Add event search/filter on Slate page
- [ ] Add grading UI directly in the frontend (currently API-only for grading)
- [ ] Consider adding ESPN injury/weather data panels to Event Research page
- [ ] Add integration tests that mock full HTTP round-trips (httpx respx)
- [ ] Set up CI pipeline (GitHub Actions) for running test suite
