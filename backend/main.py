"""FastAPI application entry point."""

from fastapi import FastAPI

from backend.routers import composer, edge, estimates, events, lines, signals, slates, sports, tracking, transcripts

app = FastAPI(title="Arb Tool", version="0.1.0")

app.include_router(slates.router)
app.include_router(events.router)
app.include_router(lines.router)
app.include_router(estimates.router)
app.include_router(edge.router)
app.include_router(transcripts.router)
app.include_router(signals.router)
app.include_router(tracking.router)
app.include_router(sports.router)
app.include_router(composer.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
