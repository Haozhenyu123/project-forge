"""Evidence normalization and provider interfaces."""

from .models import EvidenceRecord, Freshness, SourceQuality
from .normalize import canonicalize_url, normalize_record, normalize_records
from .providers import GitHubProvider, NpmProvider, OsvProvider, PyPIProvider

__all__ = [
    "EvidenceRecord",
    "Freshness",
    "SourceQuality",
    "canonicalize_url",
    "normalize_record",
    "normalize_records",
    "GitHubProvider",
    "NpmProvider",
    "OsvProvider",
    "PyPIProvider",
]
