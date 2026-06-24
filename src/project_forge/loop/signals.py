"""Signal validation, deduplication, and owner classification."""

from typing import Dict, List, Optional

from .models import (
    LoopSignal,
    OwnerClassification,
    SignalKind,
    SignalSeverity,
)


FORGE_KINDS = {
    SignalKind.CONSTRAINT_CHANGE,
    SignalKind.EVIDENCE_EXPIRY,
    SignalKind.SECURITY_ADVISORY,
    SignalKind.LICENSE_CONFLICT,
}

SUPERPOWERS_KINDS = {
    SignalKind.VERIFICATION_FAILURE,
    SignalKind.ARCHITECTURE_FEEDBACK,
    SignalKind.SUPERPOWERS_FEEDBACK,
}


def validate_signal(data: Dict) -> List[str]:
    """Validate a loop signal dict, returning a list of error messages (empty = valid)."""
    errors = []

    if not data.get("signal_id"):
        errors.append("signal_id is required")
    if not data.get("summary"):
        errors.append("summary is required")

    kind_raw = data.get("kind", "")
    try:
        SignalKind(kind_raw)
    except ValueError:
        errors.append(f"unknown signal kind: {kind_raw}")

    severity_raw = data.get("severity", "")
    try:
        SignalSeverity(severity_raw)
    except ValueError:
        errors.append(f"unknown severity: {severity_raw}")

    observed_at = data.get("observed_at", "")
    if observed_at:
        try:
            from datetime import datetime
            datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            errors.append(f"invalid observed_at timestamp: {observed_at}")

    if data.get("suggested_owner"):
        try:
            OwnerClassification(data["suggested_owner"])
        except ValueError:
            errors.append(f"unknown suggested_owner: {data['suggested_owner']}")

    return errors


def classify_owner(signal: LoopSignal) -> OwnerClassification:
    """Classify which role should handle this signal."""
    # Honor explicit suggestion when present
    if signal.suggested_owner:
        return signal.suggested_owner

    # Critical security or license → human
    if signal.severity == SignalSeverity.CRITICAL and signal.kind in {
        SignalKind.SECURITY_ADVISORY,
        SignalKind.LICENSE_CONFLICT,
    }:
        return OwnerClassification.HUMAN

    # Forge-owned kinds
    if signal.kind in FORGE_KINDS:
        return OwnerClassification.FORGE

    # Superpowers-owned kinds
    if signal.kind in SUPERPOWERS_KINDS:
        return OwnerClassification.SUPERPOWERS

    # Manual signals → Forge by default
    if signal.kind == SignalKind.MANUAL:
        return OwnerClassification.FORGE

    return OwnerClassification.SUPERPOWERS


def compute_fingerprint(signal: LoopSignal) -> str:
    """Compute a content-based dedup fingerprint."""
    return signal.fingerprint


def is_duplicate(signal: LoopSignal, known_fingerprints: List[str]) -> bool:
    """Check if a signal with the same fingerprint has already been processed."""
    return signal.fingerprint in known_fingerprints


def deduplicate_signals(
    signals: List[LoopSignal], known_fingerprints: List[str]
) -> List[LoopSignal]:
    """Return only signals whose fingerprints are not already known."""
    seen = set(known_fingerprints)
    result = []
    for s in signals:
        if s.fingerprint not in seen:
            seen.add(s.fingerprint)
            result.append(s)
    return result
