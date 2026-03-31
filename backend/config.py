"""Application configuration loaded from environment variables."""

from dataclasses import dataclass, field
from functools import lru_cache
from os import environ
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    database_url: str = field(
        default_factory=lambda: environ.get("DATABASE_URL", "sqlite:///./arb_tool.db")
    )
    anthropic_api_key: str = field(
        default_factory=lambda: environ.get("ANTHROPIC_API_KEY", "")
    )
    openai_api_key: str = field(
        default_factory=lambda: environ.get("OPENAI_API_KEY", "")
    )
    odds_api_key: str = field(
        default_factory=lambda: environ.get("ODDS_API_KEY", "")
    )
    kalshi_api_key: str = field(
        default_factory=lambda: environ.get("KALSHI_API_KEY", "")
    )
    kalshi_rsa_key_path: str = field(
        default_factory=lambda: environ.get("KALSHI_RSA_KEY_PATH", "")
    )
    kalshi_base_url: str = field(
        default_factory=lambda: environ.get(
            "KALSHI_BASE_URL", "https://trading-api.kalshi.com/trade-api/v2"
        )
    )
    polymarket_base_url: str = field(
        default_factory=lambda: environ.get(
            "POLYMARKET_BASE_URL", "https://clob.polymarket.com"
        )
    )
    weather_api_key: str = field(
        default_factory=lambda: environ.get("WEATHER_API_KEY", "")
    )
    kelly_bankroll: float = field(
        default_factory=lambda: float(environ.get("KELLY_BANKROLL", "1000.00"))
    )
    arb_threshold_pct: float = field(
        default_factory=lambda: float(environ.get("ARB_THRESHOLD_PCT", "3.0"))
    )
    edge_threshold_pct: float = field(
        default_factory=lambda: float(environ.get("EDGE_THRESHOLD_PCT", "3.0"))
    )
    llm_model: str = field(
        default_factory=lambda: environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
    )
    shortlist_size: int = field(
        default_factory=lambda: int(environ.get("SHORTLIST_SIZE", "6"))
    )
    contracts_dir: str = field(
        default_factory=lambda: environ.get(
            "CONTRACTS_DIR", str(Path.home() / ".fin-arb" / "contracts")
        )
    )
    edge_registry_path: str = field(
        default_factory=lambda: environ.get("EDGE_REGISTRY_PATH", "")
    )
    factor_research_db_path: str = field(
        default_factory=lambda: environ.get(
            "FACTOR_RESEARCH_DB_PATH",
            str(Path(__file__).resolve().parent.parent.parent
                / "factor-research" / "factor_research.db"),
        )
    )
    sharp_sources: str = field(
        default_factory=lambda: environ.get("SHARP_SOURCES", "pinnacle,circa")
    )
    market_efficiency_discount: float = field(
        default_factory=lambda: float(
            environ.get("MARKET_EFFICIENCY_DISCOUNT", "0.5")
        )
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
