"""Edge and arbitrage detection math."""


def raw_edge(user_prob: float, market_prob: float) -> float:
    """Return the raw edge as a fraction (user_prob - market_prob) / 100."""
    return round((user_prob - market_prob) / 100, 6)


def is_meaningful_edge(edge: float, threshold: float = 0.03) -> bool:
    """Return True if edge exceeds the threshold."""
    return edge > threshold


def is_arb_opportunity(prob_a: float, prob_b: float, threshold: float = 0.03) -> bool:
    """Return True if two sides sum to less than (100 - threshold*100)."""
    return (prob_a + prob_b) < (100 - threshold * 100)


def combined_implied_prob(lines: list[float]) -> float:
    """Return the sum of implied probabilities across all sides."""
    return round(sum(lines), 4)


def vig_percentage(combined_prob: float) -> float:
    """Return the vig as the excess over 100%."""
    return round(combined_prob - 100, 4)
