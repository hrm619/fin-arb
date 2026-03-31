"""Composite confidence scoring — replaces manual confidence_tier."""

from backend.models.market_line import MarketLine
from backend.models.signal import Signal
from backend.schemas.confidence_scorer import CompositeConfidence
from backend.schemas.structural_priors import ApplicableEdge

WEIGHTS = {"structural": 0.5, "signal_coherence": 0.3, "line_confirmation": 0.2}
MAX_QUALITY_SCORE = 3.0


def compute_confidence(
    edges: list[ApplicableEdge],
    signals: list[Signal],
    suggested_prob: float,
    market_lines: list[MarketLine],
) -> CompositeConfidence:
    """Compute composite confidence from structural, signal, and line data."""
    ss = structural_strength(edges)
    sc = signal_coherence(signals)
    lc = line_confirmation(suggested_prob, market_lines)

    score = round(
        WEIGHTS["structural"] * ss
        + WEIGHTS["signal_coherence"] * sc
        + WEIGHTS["line_confirmation"] * lc,
        4,
    )

    return CompositeConfidence(
        structural_strength=ss,
        signal_coherence=sc,
        line_confirmation=lc,
        composite_score=score,
        tier=confidence_tier(score),
        weights_used=WEIGHTS,
    )


def structural_strength(edges: list[ApplicableEdge]) -> float:
    """Weighted average of quality scores, normalized to 0-1."""
    if not edges:
        return 0.0
    composites = [e.quality_composite for e in edges if e.quality_composite]
    if not composites:
        return 0.0
    avg = sum(composites) / len(composites)
    return round(min(avg / MAX_QUALITY_SCORE, 1.0), 4)


def signal_coherence(signals: list[Signal]) -> float:
    """Measure agreement among directed signals. 0.5 if no signals."""
    directed = [
        s for s in signals
        if s.direction is not None
        and s.relevance_score is not None
        and s.user_flag != "dismissed"
    ]
    if not directed:
        return 0.5

    weighted_sum = sum(s.direction * s.relevance_score for s in directed)
    total_relevance = sum(s.relevance_score for s in directed)
    if total_relevance == 0:
        return 0.5

    return round(abs(weighted_sum / total_relevance), 4)


def line_confirmation(
    suggested_prob: float, market_lines: list[MarketLine],
) -> float:
    """Measure whether line movement agrees with the suggested estimate.

    Returns 1.0 if line moved toward estimate, 0.0 neutral, -0.5 if against.
    """
    if len(market_lines) < 2:
        return 0.0

    # Sort by fetch time: earliest first
    sorted_lines = sorted(market_lines, key=lambda l: l.fetched_at)
    earliest_prob = sorted_lines[0].implied_prob_pct
    latest_prob = sorted_lines[-1].implied_prob_pct

    movement = latest_prob - earliest_prob
    if abs(movement) < 0.5:
        return 0.0

    # Positive movement = market probability increased
    # If suggested_prob > earliest_prob, we want movement to be positive
    estimate_direction = 1.0 if suggested_prob > earliest_prob else -1.0
    movement_direction = 1.0 if movement > 0 else -1.0

    if estimate_direction == movement_direction:
        return round(min(abs(movement) / 5.0, 1.0), 4)
    return round(max(-abs(movement) / 10.0, -0.5), 4)


def confidence_tier(score: float) -> str:
    """Map composite score to tier label."""
    if score >= 0.70:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"
