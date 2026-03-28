# Claude Code — Build Prompt: Arbitrage Research & Edge Detection Tool v1

## Your Role

You are a senior software engineer building a local arbitrage research and edge detection tool from a technical specification. Your job is to implement the system exactly as specified, following atomic function design principles throughout.

---

## Primary Documents

Before writing any code, read and internalize both of these documents in full:

1. `technical-spec.md` — the complete technical specification
2. `phase1-prd.md` — the product requirements document (for intent and context)

If any implementation decision is unclear, resolve it by asking: *what does the spec say, and what does the PRD say about intent?* Do not invent behavior not specified in either document.

---

## Atomic Function Principles — Non-Negotiable

These rules apply to every function you write, without exception:

**1. One function, one responsibility.**
A function does exactly one logical thing. If you find yourself writing "and" in a function's description, split it.

```python
# WRONG — two responsibilities
def fetch_and_store_lines(event_id):
    lines = call_odds_api(event_id)
    db.save(lines)

# RIGHT — two functions
def fetch_lines_from_api(event_id) -> list[RawLine]: ...
def store_lines(event_id, lines) -> list[MarketLine]: ...
```

**2. Functions accept typed inputs and return typed outputs.**
Use Pydantic models or Python dataclasses for all non-primitive inputs and outputs. Never pass raw dicts between functions.

**3. Functions do not mutate state they do not own.**
A function that computes a value returns it. A function that writes to the database is a separate function.

**4. Integration functions only talk to external APIs.**
They normalize the response into an internal schema and return it. They do not call other services, write to the database, or contain business logic.

**5. Service functions only contain business logic.**
They call integration functions, call utility functions, and call the database layer. They do not contain HTTP client code.

**6. Utility functions are pure.**
Utility functions (odds conversion, Kelly, edge calculation) take inputs and return outputs. They have no side effects, no database calls, no API calls. They are deterministic. Every utility function gets a unit test before anything else is built.

**7. Routers are thin.**
FastAPI route handlers validate input, call exactly one service function, and return the result. No business logic in routers.

```python
# RIGHT — thin router
@router.get("/slates/{slate_id}/edge")
async def get_edge(slate_id: int, db: Session = Depends(get_db)):
    return edge_service.rank_slate(slate_id, db)
```

**8. Functions fail loudly with specific exceptions.**
Do not swallow errors. Raise specific, descriptive exceptions. The caller decides how to handle them.

```python
# WRONG
def get_estimate(event_id):
    try:
        return db.query(Estimate).filter_by(event_id=event_id).first()
    except:
        return None

# RIGHT
def get_estimate(event_id, db) -> Estimate:
    estimate = db.query(Estimate).filter_by(event_id=event_id).first()
    if not estimate:
        raise EstimateNotFoundError(f"No estimate found for event {event_id}")
    return estimate
```

---

## Implementation Order

Build in exactly this sequence. Do not jump ahead. Each step must be working and tested before proceeding:

### Step 1 — Project Scaffolding
- Initialize project structure exactly as defined in section 3 of the spec
- Set up FastAPI app, SQLAlchemy engine, Alembic migrations
- Create `.env.example` from section 9 of the spec
- Verify the app starts with `uvicorn main:app --reload`

### Step 2 — Database Models + Migrations
- Implement all SQLAlchemy models from section 4 of the spec
- Create the initial Alembic migration
- Verify all tables are created correctly on `alembic upgrade head`

### Step 3 — Utility Functions (build and test before anything else)
- `utils/odds_converter.py` — all conversion functions from spec section 8.1
- `utils/kelly.py` — all Kelly functions from spec section 8.2
- `utils/edge_calculator.py` — all edge functions from spec section 8.3
- Write unit tests for every utility function before moving to step 4
- These are pure functions — test with known inputs and expected outputs

### Step 4 — Slate + Event Layer
- Pydantic schemas for Slate and Event
- `slate_service.py` and `event_service.py` — all functions from spec section 6.1 and 6.2
- Routers: `/slates` and `/events` endpoints from spec section 5.1 and 5.2
- Verify via FastAPI docs (`/docs`) that CRUD operations work correctly

### Step 5 — Odds API Integration + Line Service
- `integrations/odds_api.py` — all functions from spec section 7.1
- `line_service.py` — `fetch_odds_api_lines`, `store_lines`, `get_lines`, `get_best_line`
- Router: `POST /events/{id}/lines/fetch` and `GET /events/{id}/lines`
- Verify you can fetch and display lines for a real event

### Step 6 — Estimate Service
- Pydantic schemas for UserEstimate
- `estimate_service.py` — all functions from spec section 6.5
- Enforce lock behavior: once `locked_at` is set, the estimate cannot be modified
- Auto-compute american_odds and decimal_odds on submission using odds_converter
- Router: estimate endpoints from spec section 5.5

### Step 7 — Edge Service + Edge Routes
- `edge_service.py` — all functions from spec section 6.7
- Router: `/slates/{id}/edge`, `/slates/{id}/shortlist`
- Verify end-to-end: add event → fetch lines → submit estimate → get ranked edge

### Step 8 — Transcript Ingestion
- `integrations/whisper.py` — transcription functions from spec section 7.6
- `transcript_service.py` — all functions from spec section 6.3
- Support both raw text paste and URL-triggered transcription
- Router: transcript endpoints from spec section 5.3

### Step 9 — Signal Extraction (Claude API)
- `signal_service.py` — all functions from spec section 6.4
- Use the extraction prompt provided separately (do not write your own — await the prompt)
- `parse_llm_response` must handle malformed or partial LLM responses gracefully
- Router: signal endpoints from spec section 5.4

### Step 10 — Kalshi + Polymarket Integrations
- `integrations/kalshi.py` — all functions from spec section 7.2
- `integrations/polymarket.py` — all functions from spec section 7.3
- Extend `line_service.fetch_lines` to orchestrate all three sources
- Add `detect_arb_opportunities` to line_service
- Router: arb endpoints from spec sections 5.6 and 5.7

### Step 11 — Tracking Service
- `tracking_service.py` — all functions from spec section 6.8
- Router: tracking endpoints from spec section 5.8
- Verify CSV export produces correct column headers and data

### Step 12 — ESPN + Weather Integrations
- `integrations/espn.py` — injury and form data from spec section 7.4
- `integrations/weather.py` — forecast functions from spec section 7.5
- Wire into `event_service.get_event_research`

### Step 13 — Frontend
- Scaffold React + Vite app
- Implement four pages from spec section 11 in order:
  1. Slate View
  2. Event Research View
  3. Edge Dashboard
  4. Tracking Dashboard
- Use TanStack Query for all API calls
- Use Zustand for local UI state only

---

## Code Quality Rules

- All backend functions have type annotations
- All public functions have a one-line docstring stating what they do (not how)
- No function exceeds 30 lines — if it does, split it
- No hardcoded values — all thresholds, model names, and config come from environment variables or config.py
- All external API calls are wrapped in try/except with specific error handling
- Log errors with context, not just the exception message

---

## What To Do When Stuck

1. Re-read the relevant section of the spec
2. Check if the PRD clarifies intent
3. If still unclear, implement the most conservative interpretation and add a `# TODO: clarify` comment
4. Do not invent features or behavior not in the spec

---

## Definition of Done — Per Step

A step is done when:
- All functions listed in the spec for that step are implemented
- All utility functions have passing unit tests
- The relevant API endpoints return correct responses via `/docs`
- No hardcoded secrets or values exist
- The code passes a basic linting check (flake8 or ruff)
