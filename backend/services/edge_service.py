"""Business logic for edge ranking, shortlisting, and slate-level arb."""

from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.schemas.edge import RankedEvent
from backend.schemas.market_line import ArbOpportunity
from backend.services.composer import get_suggested_estimate
from backend.services.event_service import list_events
from backend.services.estimate_service import get_estimate
from backend.services.line_service import detect_arb_opportunities, get_best_line
from backend.utils.edge_calculator import raw_edge, is_meaningful_edge
from backend.utils.kelly import fractional_kelly, kelly_stake


def compute_edge(user_prob_pct: float, market_prob_pct: float) -> float:
    """Return the raw edge between user and market probability."""
    return raw_edge(user_prob_pct, market_prob_pct)


def compute_kelly(edge: float, decimal_odds: float, bankroll: float) -> float:
    """Return the fractional Kelly stake amount."""
    frac = fractional_kelly(edge, decimal_odds)
    return kelly_stake(bankroll, frac)


def confidence_weight(tier: str | None, composite_score: float | None = None) -> float:
    """Map confidence tier or composite score to a numeric weight.

    If composite_score is provided, use it directly (0-1 range).
    Otherwise fall back to manual tier mapping.
    """
    if composite_score is not None:
        return max(0.1, min(1.0, composite_score))
    weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
    return weights.get(tier or "", 0.5)


def weighted_score(edge: float, tier: str | None) -> float:
    """Return edge multiplied by confidence weight."""
    return round(edge * confidence_weight(tier), 6)


def rank_slate(db: Session, slate_id: int) -> list[RankedEvent]:
    """Rank all events on a slate by weighted edge score descending."""
    settings = get_settings()
    events = list_events(db, slate_id)
    ranked: list[RankedEvent] = []

    for event in events:
        try:
            estimate = get_estimate(db, event.id)
        except ValueError:
            continue
        best_line = get_best_line(db, event.id, outcome_name=event.home_team)
        if best_line is None:
            continue

        edge = raw_edge(estimate.probability_pct, best_line.implied_prob_pct)
        if not is_meaningful_edge(edge, settings.edge_threshold_pct / 100):
            continue

        # Use composite confidence if a suggested estimate exists
        suggested = get_suggested_estimate(db, event.id)
        comp_score = suggested.composite_confidence if suggested else None
        tier = suggested.confidence_tier if suggested else event.confidence_tier
        weight = confidence_weight(tier, composite_score=comp_score)

        score = round(edge * weight, 6)
        decimal_odds = best_line.decimal_odds or 2.0
        frac = fractional_kelly(edge, decimal_odds)
        stake = kelly_stake(settings.kelly_bankroll, frac)

        ranked.append(
            RankedEvent(
                event_id=event.id,
                home_team=event.home_team,
                away_team=event.away_team,
                sport=event.sport,
                market_type=event.market_type,
                user_prob_pct=estimate.probability_pct,
                best_market_prob_pct=best_line.implied_prob_pct,
                best_market_source=best_line.source,
                raw_edge=edge,
                confidence_tier=tier,
                confidence_weight=weight,
                weighted_score=score,
                kelly_fraction=frac,
                kelly_stake=stake,
                composite_confidence=comp_score,
            )
        )

    return sorted(ranked, key=lambda r: r.weighted_score, reverse=True)


def get_shortlist(db: Session, slate_id: int, n: int | None = None) -> list[RankedEvent]:
    """Return the top N events by weighted score."""
    size = n or get_settings().shortlist_size
    return rank_slate(db, slate_id)[:size]


def get_arb_opportunities(db: Session, slate_id: int) -> list[ArbOpportunity]:
    """Scan all events on a slate for cross-market arb opportunities."""
    events = list_events(db, slate_id)
    all_arbs: list[ArbOpportunity] = []
    for event in events:
        all_arbs.extend(detect_arb_opportunities(db, event.id))
    return sorted(all_arbs, key=lambda a: a.arb_edge_pct, reverse=True)
