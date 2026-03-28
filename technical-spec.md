# Technical Specification: Arbitrage Research & Edge Detection Tool — v1

**Derived from:** PRD v1.0  
**Stack:** Python backend, React frontend, SQLite, local deployment  
**Architecture:** REST API backend + single-page frontend application

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend (SPA)                │
│         Weekly Slate View / Research View /          │
│         Edge Dashboard / Tracking Dashboard          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (localhost)
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend (Python)                │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Slate      │  │  Data        │  │  Edge      │  │
│  │  Service    │  │  Service     │  │  Service   │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Transcript │  │  Signal      │  │  Tracking  │  │
│  │  Service    │  │  Service     │  │  Service   │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  SQLite Database                     │
│  slates / events / transcripts / signals /           │
│  user_estimates / market_lines / outcomes            │
└─────────────────────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   External APIs   Claude API   Whisper API
   (Odds/Kalshi/   (Signal      (Transcription
   Polymarket/     Extraction)  fallback)
   Weather/ESPN)
```

---

## 2. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend framework | FastAPI (Python 3.11+) | Async support, auto docs, clean routing |
| Frontend framework | React 18 + Vite | Fast dev cycle, component model |
| Database | SQLite via SQLAlchemy | Local, zero-config, sufficient for v1 |
| Migrations | Alembic | Schema versioning from day one |
| HTTP client | httpx (async) | Native async, clean API |
| Transcription | Whisper API (openai-python) | Reliable, fast, affordable |
| LLM | Anthropic Python SDK | Signal extraction layer |
| Env management | python-dotenv | API key isolation |
| Testing | pytest + pytest-asyncio | Atomic function testing |
| Frontend state | Zustand | Lightweight, no boilerplate |
| Frontend HTTP | TanStack Query | Caching, loading states, refetch |

---

## 3. Project Structure

```
arb-tool/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Environment config loader
│   ├── database.py              # SQLAlchemy engine + session
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── slate.py
│   │   ├── event.py
│   │   ├── transcript.py
│   │   ├── signal.py
│   │   ├── estimate.py
│   │   ├── market_line.py
│   │   └── outcome.py
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── slate.py
│   │   ├── event.py
│   │   ├── transcript.py
│   │   ├── signal.py
│   │   ├── estimate.py
│   │   ├── market_line.py
│   │   └── outcome.py
│   ├── routers/                 # FastAPI route handlers (thin layer only)
│   │   ├── slates.py
│   │   ├── events.py
│   │   ├── transcripts.py
│   │   ├── signals.py
│   │   ├── estimates.py
│   │   ├── lines.py
│   │   ├── edge.py
│   │   └── tracking.py
│   ├── services/                # All business logic lives here
│   │   ├── slate_service.py
│   │   ├── event_service.py
│   │   ├── transcript_service.py
│   │   ├── signal_service.py
│   │   ├── estimate_service.py
│   │   ├── line_service.py
│   │   ├── edge_service.py
│   │   └── tracking_service.py
│   ├── integrations/            # One file per external API
│   │   ├── odds_api.py
│   │   ├── kalshi.py
│   │   ├── polymarket.py
│   │   ├── espn.py
│   │   ├── weather.py
│   │   └── whisper.py
│   ├── utils/
│   │   ├── odds_converter.py    # % ↔ American ↔ decimal
│   │   ├── kelly.py             # Kelly criterion calculator
│   │   └── edge_calculator.py  # Edge and arb detection math
│   ├── migrations/              # Alembic migrations
│   └── tests/
│       ├── test_services/
│       ├── test_integrations/
│       └── test_utils/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── SlateView.jsx
│   │   │   ├── EventResearch.jsx
│   │   │   ├── EdgeDashboard.jsx
│   │   │   └── TrackingDashboard.jsx
│   │   ├── components/
│   │   │   ├── slate/
│   │   │   ├── research/
│   │   │   ├── edge/
│   │   │   └── tracking/
│   │   ├── store/               # Zustand stores
│   │   ├── api/                 # TanStack Query hooks
│   │   └── utils/
│   └── vite.config.js
├── .env.example
├── docker-compose.yml           # Optional local orchestration
└── README.md
```

---

## 4. Database Schema

### 4.1 `slates`
```sql
id              INTEGER PRIMARY KEY
name            TEXT NOT NULL          -- e.g. "NFL Week 14"
week_start      DATE NOT NULL
week_end        DATE NOT NULL
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### 4.2 `events`
```sql
id              INTEGER PRIMARY KEY
slate_id        INTEGER FK → slates.id
home_team       TEXT NOT NULL
away_team       TEXT NOT NULL
sport           TEXT NOT NULL          -- nfl, nba, mlb, nhl, etc.
league          TEXT NOT NULL
event_date      TIMESTAMP NOT NULL
market_type     TEXT NOT NULL          -- moneyline, spread, over_under, binary
spread_value    REAL                   -- nullable, for spread markets
total_value     REAL                   -- nullable, for over/under markets
confidence_tier TEXT                   -- high, medium, low, null
status          TEXT DEFAULT 'open'    -- open, graded, pushed
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### 4.3 `transcripts`
```sql
id              INTEGER PRIMARY KEY
event_id        INTEGER FK → events.id
source_url      TEXT                   -- YouTube URL
source_type     TEXT DEFAULT 'youtube'
raw_text        TEXT NOT NULL
duration_secs   INTEGER
processed_at    TIMESTAMP
created_at      TIMESTAMP
```

### 4.4 `signals`
```sql
id              INTEGER PRIMARY KEY
transcript_id   INTEGER FK → transcripts.id
event_id        INTEGER FK → events.id
signal_type     TEXT NOT NULL          -- injury, scheme, motivation, sentiment, line_commentary
content         TEXT NOT NULL          -- extracted signal text
relevance_score REAL                   -- 0.0–1.0, LLM-assigned
timestamp_ref   TEXT                   -- approximate position in transcript
user_flag       TEXT                   -- used_in_pricing, dismissed, null
created_at      TIMESTAMP
```

### 4.5 `user_estimates`
```sql
id              INTEGER PRIMARY KEY
event_id        INTEGER FK → events.id
probability_pct REAL NOT NULL          -- 0.0–100.0
american_odds   INTEGER                -- computed on save
decimal_odds    REAL                   -- computed on save
note            TEXT
locked_at       TIMESTAMP NOT NULL     -- set on first submission, immutable after
created_at      TIMESTAMP
```

### 4.6 `market_lines`
```sql
id              INTEGER PRIMARY KEY
event_id        INTEGER FK → events.id
source          TEXT NOT NULL          -- kalshi, polymarket, draftkings, fanduel, etc.
market_key      TEXT                   -- external market identifier
implied_prob_pct REAL NOT NULL         -- 0.0–100.0
american_odds   INTEGER
decimal_odds    REAL
fetched_at      TIMESTAMP NOT NULL
raw_response    JSON                   -- full API response for audit
```

### 4.7 `outcomes`
```sql
id              INTEGER PRIMARY KEY
event_id        INTEGER FK → events.id
result          TEXT NOT NULL          -- win, loss, push
actual_score    TEXT                   -- optional, e.g. "24-17"
graded_at       TIMESTAMP NOT NULL
graded_by       TEXT DEFAULT 'user'
notes           TEXT
```

---

## 5. API Endpoints

All endpoints prefixed with `/api/v1`.

### 5.1 Slates
```
GET    /slates                    → list all slates
POST   /slates                    → create slate
GET    /slates/{id}               → get slate with events
PUT    /slates/{id}               → update slate metadata
DELETE /slates/{id}               → delete slate
```

### 5.2 Events
```
GET    /slates/{slate_id}/events          → list events on slate
POST   /slates/{slate_id}/events          → add event to slate
GET    /events/{id}                       → get full event detail
PUT    /events/{id}                       → update event (confidence tier, etc.)
DELETE /events/{id}                       → remove from slate
GET    /events/{id}/research              → aggregate all research for event
```

### 5.3 Transcripts
```
POST   /events/{event_id}/transcripts     → ingest transcript (URL or raw text)
GET    /events/{event_id}/transcripts     → list transcripts for event
GET    /transcripts/{id}                  → get full transcript text
DELETE /transcripts/{id}                  → remove transcript
```

### 5.4 Signals
```
POST   /transcripts/{transcript_id}/extract   → trigger LLM signal extraction
GET    /events/{event_id}/signals             → list all signals for event
PATCH  /signals/{id}/flag                     → set user_flag (used/dismissed)
```

### 5.5 User Estimates
```
POST   /events/{event_id}/estimate        → submit probability estimate (locks on submit)
GET    /events/{event_id}/estimate        → get current estimate
```

### 5.6 Market Lines
```
POST   /events/{event_id}/lines/fetch     → trigger on-demand line fetch
GET    /events/{event_id}/lines           → get all lines for event
GET    /events/{event_id}/lines/arb       → get cross-market arb opportunities
```

### 5.7 Edge
```
GET    /slates/{slate_id}/edge            → ranked edge table for full slate
GET    /slates/{slate_id}/shortlist       → top 6 by edge × confidence
GET    /slates/{slate_id}/arb             → opinion-free cross-market arb opportunities
```

### 5.8 Tracking
```
POST   /events/{event_id}/outcome         → grade event result
GET    /tracking/summary                  → aggregate performance metrics
GET    /tracking/export                   → CSV export of all graded events
```

---

## 6. Service Layer — Atomic Function Definitions

Each service contains small, single-responsibility functions. No function should do more than one logical thing.

### 6.1 `slate_service.py`
```python
create_slate(name, week_start, week_end) → Slate
get_slate(slate_id) → Slate
list_slates() → list[Slate]
update_slate(slate_id, fields) → Slate
delete_slate(slate_id) → bool
```

### 6.2 `event_service.py`
```python
create_event(slate_id, event_data) → Event
get_event(event_id) → Event
list_events(slate_id) → list[Event]
update_event(event_id, fields) → Event
delete_event(event_id) → bool
set_confidence_tier(event_id, tier) → Event
get_event_research(event_id) → EventResearch  # aggregates all data
```

### 6.3 `transcript_service.py`
```python
ingest_from_url(event_id, youtube_url) → Transcript
ingest_from_text(event_id, raw_text, source_url) → Transcript
transcribe_audio(audio_file_path) → str              # Whisper fallback
get_transcript(transcript_id) → Transcript
list_transcripts(event_id) → list[Transcript]
delete_transcript(transcript_id) → bool
```

### 6.4 `signal_service.py`
```python
extract_signals(transcript_id) → list[Signal]        # triggers Claude API
parse_llm_response(raw_response) → list[SignalData]  # parses structured JSON from Claude
rank_signals(signals) → list[Signal]                 # sort by relevance_score desc
flag_signal(signal_id, flag) → Signal
list_signals(event_id) → list[Signal]
```

### 6.5 `estimate_service.py`
```python
submit_estimate(event_id, probability_pct, note) → Estimate
get_estimate(event_id) → Estimate
lock_estimate(estimate_id) → Estimate                # sets locked_at, prevents further edits
is_locked(estimate_id) → bool
```

### 6.6 `line_service.py`
```python
fetch_lines(event_id) → list[MarketLine]             # orchestrates all source fetches
fetch_odds_api_lines(event) → list[MarketLine]
fetch_kalshi_lines(event) → list[MarketLine]
fetch_polymarket_lines(event) → list[MarketLine]
store_lines(event_id, lines) → list[MarketLine]
get_lines(event_id) → list[MarketLine]
get_best_line(event_id, source) → MarketLine
detect_arb_opportunities(event_id) → list[ArbOpportunity]
```

### 6.7 `edge_service.py`
```python
compute_edge(user_prob_pct, market_prob_pct) → float
compute_kelly(edge, odds, bankroll) → float
rank_slate(slate_id) → list[RankedEvent]
get_shortlist(slate_id, n=6) → list[RankedEvent]
get_arb_opportunities(slate_id) → list[ArbOpportunity]
confidence_weight(tier) → float                      # high=1.0, medium=0.7, low=0.4
weighted_score(edge, confidence_tier) → float
```

### 6.8 `tracking_service.py`
```python
grade_event(event_id, result, actual_score, notes) → Outcome
get_outcome(event_id) → Outcome
compute_hit_rate(filters) → float
compute_roi(filters) → float
compute_edge_by_dimension(dimension) → dict          # sport, bet_type, confidence_tier
export_to_csv() → str                                # returns CSV string
```

---

## 7. Integration Layer — Atomic Function Definitions

Each integration file wraps a single external API. All functions are async.

### 7.1 `odds_api.py`
```python
get_sports() → list[Sport]
get_events(sport_key, date) → list[OddsEvent]
get_odds(event_id, markets, bookmakers) → list[OddsLine]
get_historical_odds(event_id) → list[OddsLine]
normalize_to_market_line(raw_odds, event_id) → MarketLine
```

### 7.2 `kalshi.py`
```python
search_markets(query) → list[KalshiMarket]
get_market(market_id) → KalshiMarket
get_orderbook(market_id) → KalshiOrderbook
extract_implied_prob(orderbook) → float
normalize_to_market_line(market, event_id) → MarketLine
```

### 7.3 `polymarket.py`
```python
search_markets(query) → list[PolyMarket]
get_market(condition_id) → PolyMarket
get_clob_data(condition_id) → CLOBData
extract_implied_prob(clob_data) → float
normalize_to_market_line(market, event_id) → MarketLine
```

### 7.4 `espn.py`
```python
get_injuries(sport, team) → list[InjuryReport]
get_team_form(sport, team, last_n=10) → list[GameResult]
get_head_to_head(sport, home_team, away_team) → list[GameResult]
normalize_injury(raw) → InjuryReport
```

### 7.5 `weather.py`
```python
get_forecast(lat, lon, event_datetime) → WeatherForecast
is_outdoor_sport(sport) → bool
format_weather_summary(forecast) → str
```

### 7.6 `whisper.py`
```python
transcribe_file(file_path) → str
transcribe_url(audio_url) → str
chunk_audio(file_path, chunk_secs=600) → list[str]   # for long files
merge_transcripts(chunks) → str
```

---

## 8. Utility Functions

### 8.1 `odds_converter.py`
```python
pct_to_american(pct) → int
pct_to_decimal(pct) → float
american_to_pct(american_odds) → float
american_to_decimal(american_odds) → float
decimal_to_pct(decimal_odds) → float
decimal_to_american(decimal_odds) → int
remove_vig(implied_prob_a, implied_prob_b) → tuple[float, float]
```

### 8.2 `kelly.py`
```python
kelly_fraction(edge, decimal_odds) → float
fractional_kelly(edge, decimal_odds, fraction=0.25) → float
kelly_stake(bankroll, kelly_fraction) → float
```

### 8.3 `edge_calculator.py`
```python
raw_edge(user_prob, market_prob) → float
is_meaningful_edge(edge, threshold=0.03) → bool
is_arb_opportunity(prob_a, prob_b, threshold=0.03) → bool
combined_implied_prob(lines) → float                  # sum of all sides
vig_percentage(combined_prob) → float
```

---

## 9. Environment Variables

```bash
# .env.example

# Anthropic
ANTHROPIC_API_KEY=

# OpenAI (Whisper)
OPENAI_API_KEY=

# The Odds API
ODDS_API_KEY=

# Kalshi
KALSHI_API_KEY=
KALSHI_BASE_URL=https://trading-api.kalshi.com/trade-api/v2

# Polymarket
POLYMARKET_BASE_URL=https://clob.polymarket.com

# OpenWeatherMap
WEATHER_API_KEY=

# App Config
DATABASE_URL=sqlite:///./arb_tool.db
KELLY_BANKROLL=1000.00
ARB_THRESHOLD_PCT=3.0
EDGE_THRESHOLD_PCT=3.0
LLM_MODEL=claude-sonnet-4-20250514
SHORTLIST_SIZE=6
```

---

## 10. Key Data Flows

### 10.1 Transcript Ingestion + Signal Extraction
```
POST /events/{id}/transcripts
  → transcript_service.ingest_from_url(event_id, url)
    → [if no pre-built transcript] whisper.transcribe_url(url)
    → store Transcript in DB

POST /transcripts/{id}/extract
  → signal_service.extract_signals(transcript_id)
    → fetch Transcript from DB
    → call Claude API with extraction prompt
    → signal_service.parse_llm_response(raw_response)
    → signal_service.rank_signals(signals)
    → store Signals in DB
```

### 10.2 Edge Computation
```
GET /slates/{id}/edge
  → edge_service.rank_slate(slate_id)
    → list all events on slate
    → for each event:
        estimate = estimate_service.get_estimate(event_id)
        lines = line_service.get_lines(event_id)
        best_line = line_service.get_best_line(event_id)
        edge = edge_calculator.raw_edge(estimate.probability_pct, best_line.implied_prob_pct)
        kelly = kelly.fractional_kelly(edge, best_line.decimal_odds)
        weight = edge_service.confidence_weight(event.confidence_tier)
        score = edge_service.weighted_score(edge, weight)
    → sort by score descending
    → return RankedEvent list
```

### 10.3 Cross-Market Arb Detection
```
GET /events/{id}/lines/arb
  → line_service.detect_arb_opportunities(event_id)
    → get all lines for event
    → for each pair of sources:
        edge_calculator.is_arb_opportunity(prob_a, prob_b)
    → return ArbOpportunity list with source pair + edge size
```

---

## 11. Frontend Pages

### 11.1 Slate View (`/`)
- List of events on current slate
- Quick-add event form
- Confidence tier badge per event
- Edge indicator per event (if estimate submitted)
- Link to per-event research view
- Shortlist panel (top 6)
- Cross-market arb alert panel

### 11.2 Event Research View (`/events/:id`)
- Event header (teams, date, market type)
- Quantitative data panel (injuries, form, H2H, weather, line movement)
- Transcript list + upload/URL input
- Signals panel (ranked, flaggable)
- Raw transcript viewer (collapsible)
- User estimate input (probability %, format toggle, note field)
- Market lines comparison table
- Edge summary (your prob vs. best market line, Kelly suggestion)

### 11.3 Edge Dashboard (`/edge`)
- Full slate ranked table
- Sortable by edge, confidence, date
- Arb opportunities section
- Export shortlist

### 11.4 Tracking Dashboard (`/tracking`)
- Graded events table
- Hit rate vs. implied probability chart
- ROI over time chart
- Edge breakdown by sport / bet type / confidence tier
- CSV export button

---

## 12. Testing Strategy

Every utility function and service function gets a unit test. Integration tests mock external APIs.

```
tests/
├── test_utils/
│   ├── test_odds_converter.py    # pct/american/decimal conversion accuracy
│   ├── test_kelly.py             # kelly fraction math
│   └── test_edge_calculator.py  # edge, arb detection thresholds
├── test_services/
│   ├── test_slate_service.py
│   ├── test_event_service.py
│   ├── test_signal_service.py    # mock Claude API response
│   ├── test_estimate_service.py  # lock behavior, format conversion
│   ├── test_line_service.py      # mock external APIs
│   ├── test_edge_service.py      # ranking, shortlist, weighted score
│   └── test_tracking_service.py  # hit rate, ROI math
└── test_integrations/
    ├── test_odds_api.py           # mock httpx responses
    ├── test_kalshi.py
    ├── test_polymarket.py
    └── test_whisper.py
```

---

## 13. Implementation Order (Recommended)

Build in this sequence to have a working slice as early as possible:

1. **Database + migrations** — all models, Alembic setup
2. **Utils** — odds_converter, kelly, edge_calculator (fully tested before anything else)
3. **Slate + Event services + routes** — core data model working
4. **Odds API integration + line_service** — can see market lines immediately
5. **Estimate service + routes** — can submit your own probability
6. **Edge service + routes** — core value prop working end-to-end
7. **Transcript ingestion + Whisper** — audio pipeline
8. **Signal extraction (Claude API)** — qualitative layer
9. **Kalshi + Polymarket integrations** — cross-market arb
10. **Tracking service + routes** — feedback loop
11. **Frontend** — React UI across all four pages
12. **ESPN + Weather integrations** — enrich quantitative layer
