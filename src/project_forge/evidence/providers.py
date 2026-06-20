"""Injectable stdlib-only providers for architecture research metadata."""

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Protocol

from .normalize import normalize_records, utc_now


class Transport(Protocol):
    def __call__(self, request: urllib.request.Request, timeout: int) -> Mapping[str, Any]: ...


def http_json(request: urllib.request.Request, timeout: int) -> Mapping[str, Any]:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("provider response must be a JSON object")
    return payload


@dataclass
class ProviderResult:
    rows: List[Dict[str, Any]]
    provisional: bool = False
    error: str = ""


class BaseProvider:
    source = "provider"

    def __init__(self, transport: Transport = http_json, timeout: int = 20):
        self.transport = transport
        self.timeout = timeout

    def _fetch(self, request: urllib.request.Request, label: str) -> ProviderResult:
        try:
            return ProviderResult(rows=[dict(self.transport(request, self.timeout))])
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return ProviderResult(
                rows=[self._fallback(label, exc)], provisional=True, error=type(exc).__name__
            )

    def _fallback(self, label: str, exc: Exception) -> Dict[str, Any]:
        return {
            "source": self.source,
            "kind": "provider-unavailable",
            "query": label,
            "title": f"{self.source} evidence unavailable",
            "summary": f"Refresh required: {type(exc).__name__}",
            "observed_at": utc_now(),
            "provisional": True,
            "source_quality": "unverified",
        }


class GitHubProvider(BaseProvider):
    source = "github"

    def __init__(self, token: str = "", **kwargs: Any):
        super().__init__(**kwargs)
        self.token = token

    def search(self, query: str, limit: int = 20) -> ProviderResult:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": query, "per_page": max(1, min(limit, 100))}
        )
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "project-forge/0.3.0"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        raw = self._fetch(urllib.request.Request(url, headers=headers), query)
        if raw.provisional:
            raw.rows = normalize_records(raw.rows)
            return raw
        payload = raw.rows[0]
        items = payload.get("items", [])
        rows = [self._repo(item, query) for item in items[:limit] if isinstance(item, dict)]
        return ProviderResult(rows=normalize_records(rows))

    @staticmethod
    def _repo(repo: Dict[str, Any], query: str) -> Dict[str, Any]:
        return {
            "source": "github",
            "title": repo.get("full_name") or repo.get("name") or "GitHub repository",
            "full_name": repo.get("full_name") or "",
            "url": repo.get("html_url") or repo.get("url") or "",
            "summary": repo.get("description") or "",
            "stars": repo.get("stargazers_count", repo.get("stars", 0)) or 0,
            "forks": repo.get("forks_count", repo.get("forks", 0)) or 0,
            "language": repo.get("language"),
            "topics": repo.get("topics") or [],
            "updated_at": repo.get("updated_at"),
            "license": (repo.get("license") or {}).get("spdx_id") if isinstance(repo.get("license"), dict) else repo.get("license"),
            "archived": bool(repo.get("archived", False)),
            "observed_at": utc_now(),
            "provisional": False,
            "source_quality": "repository-metadata",
            "query": query,
        }


class NpmProvider(BaseProvider):
    source = "npm"

    def fetch(self, package: str) -> ProviderResult:
        url = "https://registry.npmjs.org/" + urllib.parse.quote(package, safe="@")
        raw = self._fetch(urllib.request.Request(url, headers={"Accept": "application/json"}), package)
        if raw.provisional:
            raw.rows = normalize_records(raw.rows)
            return raw
        payload = raw.rows[0]
        latest = str((payload.get("dist-tags") or {}).get("latest", ""))
        version = (payload.get("versions") or {}).get(latest, {})
        row = {
            "source": "npm", "title": package, "url": f"https://www.npmjs.com/package/{package}",
            "summary": payload.get("description") or version.get("description") or "npm package metadata",
            "version": latest, "license": version.get("license") or payload.get("license"),
            "updated_at": (payload.get("time") or {}).get("modified"), "observed_at": utc_now(),
            "provisional": False, "source_quality": "registry-metadata",
        }
        return ProviderResult(rows=normalize_records([row]))


class PyPIProvider(BaseProvider):
    source = "pypi"

    def fetch(self, package: str) -> ProviderResult:
        url = f"https://pypi.org/pypi/{urllib.parse.quote(package)}/json"
        raw = self._fetch(urllib.request.Request(url, headers={"Accept": "application/json"}), package)
        if raw.provisional:
            raw.rows = normalize_records(raw.rows)
            return raw
        info = raw.rows[0].get("info", {})
        row = {
            "source": "pypi", "title": package, "url": info.get("project_url") or f"https://pypi.org/project/{package}/",
            "summary": info.get("summary") or "PyPI package metadata", "version": info.get("version"),
            "license": info.get("license"), "observed_at": utc_now(), "provisional": False,
            "source_quality": "registry-metadata",
        }
        return ProviderResult(rows=normalize_records([row]))


class OsvProvider(BaseProvider):
    source = "osv"

    def query(self, package: str, ecosystem: str, version: str = "") -> ProviderResult:
        body: Dict[str, Any] = {"package": {"name": package, "ecosystem": ecosystem}}
        if version:
            body["version"] = version
        request = urllib.request.Request(
            "https://api.osv.dev/v1/query",
            data=json.dumps(body).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        raw = self._fetch(request, f"{ecosystem}:{package}@{version or 'latest'}")
        if raw.provisional:
            raw.rows = normalize_records(raw.rows)
            return raw
        vulnerabilities = raw.rows[0].get("vulns", []) or []
        row = {
            "source": "osv", "title": f"OSV advisories for {package}",
            "url": f"https://osv.dev/list?q={urllib.parse.quote(package)}",
            "summary": f"{len(vulnerabilities)} known advisories returned by OSV.",
            "vulnerability_count": len(vulnerabilities),
            "vulnerability_ids": [item.get("id") for item in vulnerabilities if isinstance(item, dict)],
            "observed_at": utc_now(), "provisional": False, "source_quality": "primary",
        }
        return ProviderResult(rows=normalize_records([row]))
