"""Select the sharpest available market line and extract vig-free probability."""

import logging

from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models.market_line import MarketLine
from backend.schemas.market_anchor import MarketAnchor
from backend.services.line_service import get_lines
from backend.utils.odds_converter import remove_vig

logger = logging.getLogger(__name__)


def get_market_anchor(
    db: Session, event_id: int, outcome_name: str,
) -> MarketAnchor | None:
    """Select the sharpest line and return vig-free implied probability."""
    lines = get_lines(db, event_id)
    if not lines:
        return None

    sharpest = _select_sharpest_line(lines, outcome_name)
    if sharpest is None:
        return None

    vig_free = _extract_vig_free_prob(sharpest, lines)
    settings = get_settings()
    sharp_list = [s.strip().lower() for s in settings.sharp_sources.split(",")]
    is_sharp = sharpest.source.lower() in sharp_list

    return MarketAnchor(
        source=sharpest.source,
        raw_implied_prob_pct=sharpest.implied_prob_pct,
        vig_free_prob_pct=vig_free,
        outcome_name=outcome_name,
        is_sharp_source=is_sharp,
    )


def _select_sharpest_line(
    lines: list[MarketLine], outcome_name: str,
) -> MarketLine | None:
    """Pick the sharpest line matching the outcome name.

    Priority: sharp sources (pinnacle, circa) > lowest implied prob.
    """
    settings = get_settings()
    sharp_list = [s.strip().lower() for s in settings.sharp_sources.split(",")]

    matching = [
        l for l in lines
        if l.outcome_name and outcome_name.lower() in l.outcome_name.lower()
    ]
    if not matching:
        return None

    # Prefer sharp sources
    for source in sharp_list:
        sharp_matches = [l for l in matching if l.source.lower() == source]
        if sharp_matches:
            return min(sharp_matches, key=lambda l: l.implied_prob_pct)

    # Fallback: lowest implied prob (best value)
    return min(matching, key=lambda l: l.implied_prob_pct)


def _extract_vig_free_prob(
    line: MarketLine, all_lines: list[MarketLine],
) -> float:
    """Remove vig by finding the complementary line from the same source."""
    complement = _find_complement(line, all_lines)
    if complement is None:
        return line.implied_prob_pct

    fair_a, _ = remove_vig(line.implied_prob_pct, complement.implied_prob_pct)
    return fair_a


def _find_complement(
    line: MarketLine, all_lines: list[MarketLine],
) -> MarketLine | None:
    """Find the opposite-outcome line from the same source."""
    candidates = [
        l for l in all_lines
        if l.source == line.source
        and l.outcome_name != line.outcome_name
        and l.outcome_name is not None
        and l.market_key == line.market_key
    ]
    if not candidates:
        return None
    return candidates[0]
