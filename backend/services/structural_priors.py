"""Load edge registry and match applicable edges to games."""

import json
import logging
from functools import lru_cache
from pathlib import Path

from backend.config import get_settings
from backend.schemas.structural_priors import ApplicableEdge
from backend.services.stats_provider import (
    get_latest_week,
    get_team_metrics,
    normalize_team_name,
)

logger = logging.getLogger(__name__)


def load_edge_registry(registry_path: str | None = None) -> dict:
    """Load the Contract 2 edge registry JSON file."""
    if registry_path is None:
        settings = get_settings()
        registry_path = settings.edge_registry_path
        if not registry_path:
            registry_path = str(
                Path(settings.contracts_dir) / "edges" / "nfl_edges.json"
            )

    path = Path(registry_path)
    if not path.exists():
        logger.warning("Edge registry not found at %s", registry_path)
        return {"edges": []}

    with open(path) as f:
        return json.load(f)


def get_applicable_edges(
    home_team: str,
    away_team: str,
    season: int,
    week: int | None = None,
    registry: dict | None = None,
) -> list[ApplicableEdge]:
    """Find all edges that apply to a given matchup."""
    if registry is None:
        registry = load_edge_registry()

    edges = registry.get("edges", [])
    if not edges:
        return []

    applicable: list[ApplicableEdge] = []
    teams = [
        (normalize_team_name(home_team), home_team, "home"),
        (normalize_team_name(away_team), away_team, "away"),
    ]

    for abbr, display_name, role in teams:
        if week is None:
            week = get_latest_week(abbr, season) or 1
        metrics = get_team_metrics(abbr, season, week)
        if not metrics:
            continue

        for edge in edges:
            match = _check_edge_applies(edge, metrics)
            if match:
                applicable.append(ApplicableEdge(
                    edge_id=edge["edge_id"],
                    hypothesis_name=edge["hypothesis_name"],
                    metric=edge["metric"],
                    bucket_label=edge["bucket_label"],
                    edge_magnitude=edge["measurement"]["edge_magnitude"],
                    quality_grade=edge.get("quality", {}).get("grade"),
                    quality_composite=edge.get("quality", {}).get("composite_score"),
                    applies_to_team=display_name,
                    metric_value=match,
                ))

    return applicable


def _check_edge_applies(
    edge: dict, metrics: dict[str, float | None],
) -> float | None:
    """Check if a team's metrics place them in this edge's bucket.

    Returns the metric value if the edge applies, None otherwise.
    """
    metric_name = edge.get("metric", "")
    metric_value = metrics.get(metric_name)
    if metric_value is None:
        return None

    applicability = edge.get("applicability", {})
    cls_type = applicability.get("classification_type", "quartile")
    direction = applicability.get("metric_direction", "unknown")
    bucket = edge.get("bucket_label", "")

    return _matches_bucket(metric_value, bucket, cls_type, direction)


def _matches_bucket(
    value: float,
    bucket_label: str,
    classification_type: str,
    metric_direction: str,
) -> float | None:
    """Determine if a metric value places a team in the given bucket.

    For quartile: uses a simplified heuristic based on bucket label.
    Returns the value if matched, None otherwise.

    Note: Precise bucket matching would require league-wide distributions.
    This simplified version checks direction consistency.
    """
    if classification_type == "binary":
        if bucket_label == "above" and metric_direction == "higher_is_better":
            return value
        if bucket_label == "below" and metric_direction == "lower_is_better":
            return value
        return None

    if classification_type == "quartile":
        # For quartiles, we can only do approximate matching without
        # league-wide data. We include the edge and let the quality
        # score weight its influence appropriately.
        if bucket_label in ("Q1", "Q2") and metric_direction == "higher_is_better":
            return value
        if bucket_label in ("Q3", "Q4") and metric_direction == "lower_is_better":
            return value
        return None

    # For percentile/custom, include if direction matches
    if "top" in bucket_label.lower() and metric_direction == "higher_is_better":
        return value
    if "bottom" in bucket_label.lower() and metric_direction == "lower_is_better":
        return value

    return None
