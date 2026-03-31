"""Business logic for signal extraction and management."""

import json
import logging

import anthropic
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models.signal import Signal
from backend.schemas.signal import SignalData
from backend.services.transcript_service import get_transcript

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a sports betting research analyst. Extract structured signals from the \
following transcript that are relevant to predicting the outcome of a sporting event.

For each signal, return a JSON array of objects with these fields:
- "signal_type": one of "injury", "scheme", "motivation", "sentiment", "line_commentary"
- "content": a concise summary of the signal (1-2 sentences)
- "relevance_score": float 0.0-1.0 indicating how relevant this is to predicting the outcome
- "direction": +1 if the signal favors the home team, -1 if it favors the away team, null if neutral or unclear
- "timestamp_ref": approximate position in transcript if discernible, else null

Return ONLY a JSON array, no other text.

Transcript:
{transcript_text}
"""


def extract_signals(db: Session, transcript_id: int) -> list[Signal]:
    """Extract signals from a transcript using Claude API."""
    transcript = get_transcript(db, transcript_id)
    settings = get_settings()

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.llm_model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT.format(
                    transcript_text=transcript.raw_text[:50000]
                ),
            }
        ],
    )

    raw_response = message.content[0].text
    signal_datas = parse_llm_response(raw_response)
    ranked = rank_signals(signal_datas)

    models: list[Signal] = []
    for sd in ranked:
        signal = Signal(
            transcript_id=transcript_id,
            event_id=transcript.event_id,
            signal_type=sd.signal_type,
            content=sd.content,
            relevance_score=sd.relevance_score,
            timestamp_ref=sd.timestamp_ref,
            direction=sd.direction,
        )
        db.add(signal)
        models.append(signal)

    db.commit()
    for m in models:
        db.refresh(m)
    return models


def parse_llm_response(raw_response: str) -> list[SignalData]:
    """Parse structured JSON from Claude's response."""
    text = raw_response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response as JSON: %s", text[:200])
        return []

    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        if not isinstance(item, dict) or not item.get("content"):
            continue
        direction = item.get("direction")
        if direction is not None:
            direction = int(direction) if direction in (1, -1, 1.0, -1.0) else None
        results.append(SignalData(
            signal_type=item.get("signal_type", "unknown"),
            content=item.get("content", ""),
            relevance_score=float(item.get("relevance_score", 0.0)),
            timestamp_ref=item.get("timestamp_ref"),
            direction=direction,
        ))
    return results


def rank_signals(signals: list[SignalData]) -> list[SignalData]:
    """Sort signals by relevance_score descending."""
    return sorted(signals, key=lambda s: s.relevance_score, reverse=True)


def set_direction(db: Session, signal_id: int, direction: int) -> Signal:
    """Set the direction on a signal (+1 favors home, -1 favors away)."""
    if direction not in (1, -1):
        raise ValueError("Direction must be +1 or -1")
    signal = db.get(Signal, signal_id)
    if not signal:
        raise ValueError(f"Signal {signal_id} not found")
    signal.direction = direction
    db.commit()
    db.refresh(signal)
    return signal


def flag_signal(db: Session, signal_id: int, flag: str) -> Signal:
    """Set the user_flag on a signal."""
    signal = db.get(Signal, signal_id)
    if not signal:
        raise ValueError(f"Signal {signal_id} not found")
    signal.user_flag = flag
    db.commit()
    db.refresh(signal)
    return signal


def list_signals(db: Session, event_id: int) -> list[Signal]:
    """Return all signals for an event, ranked by relevance."""
    return list(
        db.query(Signal)
        .filter(Signal.event_id == event_id)
        .order_by(Signal.relevance_score.desc())
        .all()
    )
