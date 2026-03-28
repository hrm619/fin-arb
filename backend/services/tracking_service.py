"""Business logic for outcome grading and performance tracking."""

import csv
import io
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.models.event import Event
from backend.models.outcome import Outcome
from backend.schemas.outcome import EdgeBreakdown, OutcomeCreate, TrackingSummary
from backend.services.estimate_service import get_estimate
from backend.services.event_service import get_event
from backend.services.line_service import get_best_line
from backend.utils.edge_calculator import raw_edge


def grade_event(db: Session, event_id: int, data: OutcomeCreate) -> Outcome:
    """Grade an event with a result."""
    get_event(db, event_id)
    existing = db.query(Outcome).filter(Outcome.event_id == event_id).first()
    if existing:
        raise ValueError(f"Event {event_id} already graded")

    outcome = Outcome(
        event_id=event_id,
        result=data.result,
        actual_score=data.actual_score,
        graded_at=datetime.now(tz=UTC),
        graded_by="user",
        notes=data.notes,
    )
    db.add(outcome)

    event = get_event(db, event_id)
    event.status = "graded"
    db.commit()
    db.refresh(outcome)
    return outcome


def get_outcome(db: Session, event_id: int) -> Outcome:
    """Get the outcome for an event or raise."""
    outcome = db.query(Outcome).filter(Outcome.event_id == event_id).first()
    if not outcome:
        raise ValueError(f"No outcome for event {event_id}")
    return outcome


def compute_hit_rate(db: Session, sport: str | None = None) -> float:
    """Compute win rate across graded events, optionally filtered by sport."""
    query = db.query(Outcome).join(Event)
    if sport:
        query = query.filter(Event.sport == sport)
    outcomes = query.all()
    if not outcomes:
        return 0.0
    wins = sum(1 for o in outcomes if o.result == "win")
    non_push = [o for o in outcomes if o.result != "push"]
    if not non_push:
        return 0.0
    return round(wins / len(non_push), 4)


def compute_roi(db: Session, sport: str | None = None) -> float:
    """Compute simple ROI: (wins - losses) / total non-push bets."""
    query = db.query(Outcome).join(Event)
    if sport:
        query = query.filter(Event.sport == sport)
    outcomes = query.all()
    non_push = [o for o in outcomes if o.result != "push"]
    if not non_push:
        return 0.0
    wins = sum(1 for o in non_push if o.result == "win")
    losses = len(non_push) - wins
    return round((wins - losses) / len(non_push), 4)


def get_summary(db: Session) -> TrackingSummary:
    """Aggregate performance metrics."""
    outcomes = db.query(Outcome).all()
    wins = sum(1 for o in outcomes if o.result == "win")
    losses = sum(1 for o in outcomes if o.result == "loss")
    pushes = sum(1 for o in outcomes if o.result == "push")
    return TrackingSummary(
        total_graded=len(outcomes),
        wins=wins,
        losses=losses,
        pushes=pushes,
        hit_rate=compute_hit_rate(db),
        roi=compute_roi(db),
    )


def compute_edge_by_dimension(
    db: Session, dimension: str
) -> list[EdgeBreakdown]:
    """Break down hit rate and average edge by sport, market_type, or confidence_tier."""
    outcomes = db.query(Outcome).join(Event).all()
    groups: dict[str, list[tuple[Outcome, Event]]] = {}

    for outcome in outcomes:
        event = outcome.event
        key = getattr(event, dimension, "unknown") or "unknown"
        groups.setdefault(key, []).append((outcome, event))

    breakdowns: list[EdgeBreakdown] = []
    for group_name, items in groups.items():
        non_push = [(o, e) for o, e in items if o.result != "push"]
        if not non_push:
            continue
        wins = sum(1 for o, _ in non_push if o.result == "win")
        hit_rate = wins / len(non_push)

        edges: list[float] = []
        for _, event in non_push:
            try:
                estimate = get_estimate(db, event.id)
                best_line = get_best_line(db, event.id)
                if best_line:
                    edges.append(raw_edge(estimate.probability_pct, best_line.implied_prob_pct))
            except ValueError:
                continue

        breakdowns.append(
            EdgeBreakdown(
                dimension=dimension,
                group=group_name,
                count=len(non_push),
                hit_rate=round(hit_rate, 4),
                avg_edge=round(sum(edges) / len(edges), 6) if edges else 0.0,
            )
        )

    return sorted(breakdowns, key=lambda b: b.hit_rate, reverse=True)


def export_to_csv(db: Session) -> str:
    """Export all graded events to a CSV string."""
    outcomes = db.query(Outcome).join(Event).order_by(Event.event_date).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "event_id", "home_team", "away_team", "sport", "league",
        "market_type", "event_date", "result", "actual_score",
        "graded_at", "notes",
    ])
    for outcome in outcomes:
        event = outcome.event
        writer.writerow([
            event.id, event.home_team, event.away_team, event.sport,
            event.league, event.market_type, event.event_date.isoformat(),
            outcome.result, outcome.actual_score or "",
            outcome.graded_at.isoformat(), outcome.notes or "",
        ])
    return output.getvalue()
