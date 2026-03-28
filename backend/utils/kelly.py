"""Kelly criterion calculations for optimal bet sizing."""


def kelly_fraction(edge: float, decimal_odds: float) -> float:
    """Return the full Kelly fraction (0-1) given edge and decimal odds."""
    if decimal_odds <= 1:
        raise ValueError(f"Decimal odds must be greater than 1, got {decimal_odds}")
    b = decimal_odds - 1
    p = (edge + 1 / decimal_odds)
    q = 1 - p
    fraction = (b * p - q) / b
    return round(max(fraction, 0.0), 6)


def fractional_kelly(edge: float, decimal_odds: float, fraction: float = 0.25) -> float:
    """Return a fractional Kelly fraction (default quarter-Kelly)."""
    return round(kelly_fraction(edge, decimal_odds) * fraction, 6)


def kelly_stake(bankroll: float, kelly_frac: float) -> float:
    """Return the dollar amount to stake given bankroll and Kelly fraction."""
    if bankroll < 0:
        raise ValueError(f"Bankroll cannot be negative, got {bankroll}")
    return round(bankroll * kelly_frac, 2)
