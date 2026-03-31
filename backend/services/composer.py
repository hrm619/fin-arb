"""Estimate composer — anchor + structural + signals + confidence."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models.suggested_estimate import SuggestedEstimate
from backend.schemas.composer import (
    StructuralAdjustmentDetail,
    SuggestedEstimateResponse,
)
from backend.schemas.structural_priors import ApplicableEdge
from backend.services.confidence_scorer import compute_confidence
from backend.services.line_service import get_lines
from backend.services.market_anchor import get_market_anchor
from backend.services.signal_aggregator import aggregate_signals
from backend.services.signal_service import list_signals
from backend.services.structural_priors import get_applicable_edges

logger = logging.getLogger(__name__)

QUALITY_WEIGHTS = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}


def compose_estimate(
    db: Session, event_id: int, season: int = 2024,
) -> SuggestedEstimateResponse:
    """Generate a suggested estimate with full decomposition."""
    from backend.services.event_service import get_event

    event = get_event(db, event_id)
    settings = get_settings()

    # 1. Market anchor
    anchor = get_market_anchor(db, event_id, outcome_name=event.home_team)
    if anchor is None:
        raise ValueError(f"No market lines found for event {event_id}")

    # 2. Structural adjustments
    edges = get_applicable_edges(
        event.home_team, event.away_team, season=season,
    )
    structural_details = _build_structural_details(edges, settings)
    total_structural = sum(d.adjustment for d in structural_details)

    # 3. Signal adjustments
    signals = list_signals(db, event_id)
    signal_agg = aggregate_signals(signals)

    # 4. Suggested probability
    suggested = _clamp(
        anchor.vig_free_prob_pct + total_structural + signal_agg.total_adjustment
    )

    # 5. Composite confidence
    lines = get_lines(db, event_id)
    confidence = compute_confidence(edges, signals, suggested, lines)

    # 6. Persist
    model = _persist(
        db, event_id, anchor, total_structural,
        signal_agg.total_adjustment, suggested, confidence,
        structural_details, signal_agg,
    )

    return SuggestedEstimateResponse(
        id=model.id,
        event_id=event_id,
        anchor_prob_pct=anchor.vig_free_prob_pct,
        anchor_source=anchor.source,
        structural_adjustments=structural_details,
        total_structural_adjustment=round(total_structural, 4),
        signal_aggregation=signal_agg if signal_agg.signal_count > 0 else None,
        total_signal_adjustment=signal_agg.total_adjustment,
        suggested_prob_pct=suggested,
        composite_confidence=confidence,
        confidence_tier=confidence.tier,
    )


def get_suggested_estimate(
    db: Session, event_id: int,
) -> SuggestedEstimate | None:
    """Retrieve a previously generated suggested estimate."""
    return (
        db.query(SuggestedEstimate)
        .filter(SuggestedEstimate.event_id == event_id)
        .first()
    )


def compute_structural_adjustment(edges: list[ApplicableEdge]) -> float:
    """Sum structural adjustments from applicable edges."""
    settings = get_settings()
    discount = settings.market_efficiency_discount
    total = 0.0
    for edge in edges:
        weight = _quality_weight(edge.quality_grade)
        total += edge.edge_magnitude * weight * (1 - discount) * 100
    return round(total, 4)


def _build_structural_details(
    edges: list[ApplicableEdge], settings,
) -> list[StructuralAdjustmentDetail]:
    discount = settings.market_efficiency_discount
    details = []
    for edge in edges:
        weight = _quality_weight(edge.quality_grade)
        adj = round(edge.edge_magnitude * weight * (1 - discount) * 100, 4)
        details.append(StructuralAdjustmentDetail(
            edge_id=edge.edge_id,
            metric=edge.metric,
            applies_to_team=edge.applies_to_team,
            edge_magnitude=edge.edge_magnitude,
            quality_grade=edge.quality_grade,
            quality_weight=weight,
            market_efficiency_discount=discount,
            adjustment=adj,
        ))
    return details


def _quality_weight(grade: str | None) -> float:
    return QUALITY_WEIGHTS.get(grade or "", 0.3)


def _clamp(value: float, low: float = 1.0, high: float = 99.0) -> float:
    return round(max(low, min(high, value)), 2)


def _persist(
    db, event_id, anchor, structural_adj, signal_adj,
    suggested, confidence, structural_details, signal_agg,
) -> SuggestedEstimate:
    """Save or update the suggested estimate in the DB."""
    existing = get_suggested_estimate(db, event_id)
    decomposition = {
        "anchor": {"source": anchor.source, "prob_pct": anchor.vig_free_prob_pct},
        "structural": [d.model_dump() for d in structural_details],
        "signals": signal_agg.model_dump(),
        "confidence": confidence.model_dump(),
    }

    if existing:
        existing.anchor_prob_pct = anchor.vig_free_prob_pct
        existing.anchor_source = anchor.source
        existing.structural_adjustment = structural_adj
        existing.signal_adjustment = signal_agg.total_adjustment
        existing.suggested_prob_pct = suggested
        existing.composite_confidence = confidence.composite_score
        existing.confidence_tier = confidence.tier
        existing.decomposition_json = decomposition
        db.commit()
        db.refresh(existing)
        return existing

    model = SuggestedEstimate(
        event_id=event_id,
        anchor_prob_pct=anchor.vig_free_prob_pct,
        anchor_source=anchor.source,
        structural_adjustment=structural_adj,
        signal_adjustment=signal_agg.total_adjustment,
        suggested_prob_pct=suggested,
        composite_confidence=confidence.composite_score,
        confidence_tier=confidence.tier,
        decomposition_json=decomposition,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
