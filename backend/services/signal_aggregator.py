"""Aggregate directed signals with type-specific caps."""

from backend.models.signal import Signal
from backend.schemas.signal_aggregator import SignalAggregation, SignalContribution

SIGNAL_CAPS: dict[str, float] = {
    "injury": 5.0,
    "scheme": 2.0,
    "line_commentary": 3.0,
    "motivation": 1.5,
    "sentiment": 1.0,
}


def compute_signal_adjustment(
    direction: int, relevance_score: float, signal_type: str,
) -> float:
    """Compute a single signal's adjustment in percentage points."""
    cap = SIGNAL_CAPS.get(signal_type, 1.0)
    return round(direction * relevance_score * cap, 4)


def aggregate_signals(signals: list[Signal]) -> SignalAggregation:
    """Aggregate signals into a total adjustment.

    Only includes signals with direction set and not dismissed.
    """
    contributions: list[SignalContribution] = []

    for signal in signals:
        if signal.direction is None:
            continue
        if signal.user_flag == "dismissed":
            continue
        if signal.relevance_score is None:
            continue

        cap = SIGNAL_CAPS.get(signal.signal_type, 1.0)
        adjustment = compute_signal_adjustment(
            signal.direction, signal.relevance_score, signal.signal_type,
        )
        contributions.append(SignalContribution(
            signal_id=signal.id,
            signal_type=signal.signal_type,
            direction=signal.direction,
            relevance_score=signal.relevance_score,
            cap=cap,
            adjustment=adjustment,
        ))

    total = round(sum(c.adjustment for c in contributions), 4)
    return SignalAggregation(
        contributions=contributions,
        total_adjustment=total,
        signal_count=len(contributions),
    )
