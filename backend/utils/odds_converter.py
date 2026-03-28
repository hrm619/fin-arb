"""Conversions between probability %, American odds, and decimal odds."""


def pct_to_american(pct: float) -> int:
    """Convert probability percentage (0-100) to American odds."""
    if pct <= 0 or pct >= 100:
        raise ValueError(f"Probability must be between 0 and 100 exclusive, got {pct}")
    if pct >= 50:
        return round(-pct / (100 - pct) * 100)
    return round((100 - pct) / pct * 100)


def pct_to_decimal(pct: float) -> float:
    """Convert probability percentage (0-100) to decimal odds."""
    if pct <= 0 or pct >= 100:
        raise ValueError(f"Probability must be between 0 and 100 exclusive, got {pct}")
    return round(100 / pct, 4)


def american_to_pct(american_odds: int) -> float:
    """Convert American odds to implied probability percentage (0-100)."""
    if american_odds == 0:
        raise ValueError("American odds cannot be zero")
    if american_odds < 0:
        return round(abs(american_odds) / (abs(american_odds) + 100) * 100, 4)
    return round(100 / (american_odds + 100) * 100, 4)


def american_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal odds."""
    if american_odds == 0:
        raise ValueError("American odds cannot be zero")
    if american_odds < 0:
        return round(1 + 100 / abs(american_odds), 4)
    return round(1 + american_odds / 100, 4)


def decimal_to_pct(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability percentage (0-100)."""
    if decimal_odds <= 1:
        raise ValueError(f"Decimal odds must be greater than 1, got {decimal_odds}")
    return round(100 / decimal_odds, 4)


def decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds to American odds."""
    if decimal_odds <= 1:
        raise ValueError(f"Decimal odds must be greater than 1, got {decimal_odds}")
    if decimal_odds >= 2:
        return round((decimal_odds - 1) * 100)
    return round(-100 / (decimal_odds - 1))


def remove_vig(implied_prob_a: float, implied_prob_b: float) -> tuple[float, float]:
    """Remove vig from a two-outcome market, returning fair probabilities."""
    total = implied_prob_a + implied_prob_b
    if total <= 0:
        raise ValueError("Sum of implied probabilities must be positive")
    return (
        round(implied_prob_a / total * 100, 4),
        round(implied_prob_b / total * 100, 4),
    )
