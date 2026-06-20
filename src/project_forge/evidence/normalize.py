"""Deterministic normalization, URL canonicalization, and deduplication."""

import hashlib
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import EvidenceRecord, Freshness, SourceQuality


TRACKING_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "source",
}
QUALITY_ALIASES = {
    "official": SourceQuality.PRIMARY,
    "official-docs": SourceQuality.PRIMARY,
    "primary": SourceQuality.PRIMARY,
    "repository-metadata": SourceQuality.REPOSITORY_METADATA,
    "registry-metadata": SourceQuality.REGISTRY_METADATA,
    "secondary": SourceQuality.SECONDARY,
    "unverified": SourceQuality.UNVERIFIED,
}
QUALITY_RANK = {quality: index for index, quality in enumerate(reversed(list(SourceQuality)))}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonicalize_url(value: str) -> str:
    """Return a stable URL while preserving non-tracking semantic query keys."""
    if not value:
        return ""
    parsed = urlsplit(str(value).strip())
    if not parsed.scheme or not parsed.netloc:
        return str(value).strip()
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    port = parsed.port
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        host = f"{host}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = urlencode(
        sorted(
            (key, val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in TRACKING_KEYS
        )
    )
    return urlunsplit((scheme, host, path, query, ""))


def parse_day(value: Any) -> Optional[date]:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def freshness_for(observed_at: str, as_of: Optional[str] = None) -> Freshness:
    observed = parse_day(observed_at)
    current = parse_day(as_of) if as_of else date.today()
    if not observed or not current:
        return Freshness.UNKNOWN
    age = max(0, (current - observed).days)
    if age <= 90:
        return Freshness.CURRENT
    if age <= 365:
        return Freshness.AGING
    return Freshness.STALE


def infer_quality(row: Dict[str, Any]) -> SourceQuality:
    raw = str(row.get("source_quality", "")).lower()
    if raw in QUALITY_ALIASES:
        return QUALITY_ALIASES[raw]
    source = str(row.get("source", "")).lower()
    if source in {"github"}:
        return SourceQuality.REPOSITORY_METADATA
    if source in {"npm", "pypi", "osv"}:
        return SourceQuality.REGISTRY_METADATA
    if source in {"official-docs", "vendor-docs"}:
        return SourceQuality.PRIMARY
    return SourceQuality.UNVERIFIED if is_provisional(row) else SourceQuality.SECONDARY


def is_provisional(row: Dict[str, Any]) -> bool:
    if "provisional" in row:
        return bool(row["provisional"])
    return row.get("source") == "host-web-tool" or row.get("kind") == "manual-search-required"


def stable_fingerprint(source: str, canonical_url: str, title: str, summary: str) -> str:
    identity = canonical_url or f"{source}\0{title.strip().lower()}\0{summary.strip().lower()}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def normalize_record(
    row: Dict[str, Any],
    *,
    index: int = 1,
    observed_at: Optional[str] = None,
    as_of: Optional[str] = None,
) -> EvidenceRecord:
    source = str(row.get("source") or "unknown")
    title = str(row.get("title") or row.get("name") or row.get("full_name") or "Untitled evidence")
    url = str(row.get("url") or row.get("html_url") or row.get("link") or "")
    summary = str(row.get("summary") or row.get("description") or title)
    canonical = canonicalize_url(url)
    fingerprint = str(row.get("fingerprint") or stable_fingerprint(source, canonical, title, summary))
    seen_at = str(row.get("observed_at") or observed_at or utc_now())
    stars = row.get("stars", row.get("stargazers_count", 1))
    try:
        score = int(stars)
    except (TypeError, ValueError):
        score = 1
    known = {
        "evidence_id", "source", "title", "name", "full_name", "url", "html_url", "link",
        "summary", "description", "observed_at", "canonical_url", "fingerprint",
        "source_quality", "freshness", "provisional", "relevance", "score", "evidence_for",
    }
    attributes = {key: value for key, value in row.items() if key not in known}
    return EvidenceRecord(
        evidence_id=str(row.get("evidence_id") or f"E-{fingerprint[:12]}"),
        source=source,
        title=title,
        url=url,
        summary=summary,
        observed_at=seen_at,
        canonical_url=canonical,
        fingerprint=fingerprint,
        source_quality=infer_quality(row),
        freshness=freshness_for(seen_at, as_of),
        provisional=is_provisional(row),
        relevance=str(row.get("relevance") or _relevance(row)),
        score=score,
        attributes=attributes,
        evidence_for=[str(value) for value in row.get("evidence_for", [])],
    )


def _relevance(row: Dict[str, Any]) -> str:
    if row.get("query"):
        return f"Research result for query: {row['query']}"
    return "Supports project research decision."


def normalize_records(rows: Iterable[Dict[str, Any]], *, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
    """Normalize and merge duplicates, retaining the strongest record."""
    by_fingerprint: Dict[str, EvidenceRecord] = {}
    for index, row in enumerate(rows, start=1):
        record = normalize_record(row, index=index, as_of=as_of)
        previous = by_fingerprint.get(record.fingerprint)
        if previous is None or _record_rank(record) > _record_rank(previous):
            if previous and not record.evidence_for:
                record.evidence_for = previous.evidence_for
            by_fingerprint[record.fingerprint] = record
    return [record.to_dict() for record in by_fingerprint.values()]


def _record_rank(record: EvidenceRecord) -> tuple:
    return (
        not record.provisional,
        QUALITY_RANK.get(record.source_quality, 0),
        parse_day(record.observed_at) or date.min,
        record.score,
    )
