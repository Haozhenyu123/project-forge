"""Architecture risk register generation.

Generates context-aware risks based on the selected stack, creative direction signals,
and evidence quality. These risks are embedded in ADRs and handoff packets so that
Superpowers can prioritize testing and mitigation.
"""

from typing import Any, Dict, List, Optional

from project_forge.models import RiskItem


STACK_RISK_TEMPLATES: Dict[str, List[dict]] = {
    "nextjs": [
        {"id": "RISK-NEXT-VERCEL", "category": "deployment", "likelihood": "low", "impact": "medium",
         "description": "Deep coupling with Vercel platform may increase migration cost if self-hosting becomes required.",
         "mitigation": "Use standard Next.js build output; avoid Vercel-specific APIs (ISR with file system, Edge Config) unless explicitly accepted.", "signal_trigger": "Self-hosting or on-premise deployment requirement emerges."},
        {"id": "RISK-NEXT-SSR", "category": "complexity", "likelihood": "medium", "impact": "medium",
         "description": "Hybrid SSR/SSG/ISR rendering model can cause confusing caching and hydration behavior.",
         "mitigation": "Default to SSG for content pages, SSR for authenticated dashboards only. Document the rendering strategy per route.", "signal_trigger": "Performance regressions or hydration mismatch errors in production logs."},
    ],
    "fastapi": [
        {"id": "RISK-FAST-ASYNC", "category": "performance", "likelihood": "medium", "impact": "high",
         "description": "Mixing sync and async handlers can block the event loop under load.",
         "mitigation": "Audit all route handlers; mark sync-only routes explicitly; run load tests before launch.", "signal_trigger": "P99 latency spikes under concurrent request load."},
        {"id": "RISK-FAST-SEC", "category": "security", "likelihood": "low", "impact": "high",
         "description": "FastAPI does not enforce CSRF or rate-limiting by default; these must be configured manually.",
         "mitigation": "Add slowapi for rate-limiting and a CSRF middleware before the first production deployment.", "signal_trigger": "Security audit identifies missing rate limiting."},
    ],
    "python": [
        {"id": "RISK-PY-DEPS", "category": "maintenance", "likelihood": "medium", "impact": "medium",
         "description": "Python dependency resolution can produce non-deterministic builds across environments.",
         "mitigation": "Use pip-tools or Poetry with a checked-in lock file. Pin all transitive dependencies.", "signal_trigger": "CI builds fail due to dependency version mismatch."},
    ],
    "node-ts": [
        {"id": "RISK-NODE-SUPPLY", "category": "security", "likelihood": "medium", "impact": "high",
         "description": "npm supply chain attacks target popular transitive dependencies.",
         "mitigation": "Use npm audit in CI, enable Dependabot, review new dependency additions in PR.", "signal_trigger": "npm audit reports a critical CVE in a transitive dependency."},
    ],
    "electron": [
        {"id": "RISK-ELEC-SIZE", "category": "complexity", "likelihood": "medium", "impact": "medium",
         "description": "Electron bundles a full Chromium runtime; binary size and memory usage are significant.",
         "mitigation": "Use electron-builder with asar compression; lazy-load renderer processes.", "signal_trigger": "User complaints about application size or memory usage."},
    ],
    "chrome-extension": [
        {"id": "RISK-EXT-REVIEW", "category": "deployment", "likelihood": "medium", "impact": "high",
         "description": "Chrome Web Store review can reject or delay updates; changes to manifest permissions are sensitive.",
         "mitigation": "Keep permissions minimal; maintain a detailed privacy justification document.", "signal_trigger": "Extension update is rejected by Chrome Web Store review."},
    ],
    "cli": [
        {"id": "RISK-CLI-CROSS", "category": "deployment", "likelihood": "low", "impact": "medium",
         "description": "Cross-platform CLI packaging (Windows vs Unix path handling) can introduce subtle bugs.",
         "mitigation": "Test on Windows and macOS in CI; use pathlib/Node.js path module consistently.", "signal_trigger": "Windows-specific bug reports for path-related issues."},
    ],
    "generic": [
        {"id": "RISK-GEN-UNDEF", "category": "complexity", "likelihood": "high", "impact": "high",
         "description": "No formal stack selected — all architectural decisions are deferred, increasing integration risk.",
         "mitigation": "Run project-forge init with explicit constraints to produce a stack choice before implementation.", "signal_trigger": "Implementation begins without a stack decision."},
    ],
}

CREATIVE_RISK_TEMPLATES: Dict[str, List[dict]] = {
    "small-scope": [],
    "fast-feedback": [
        {"id": "RISK-FASTFEED-SCOPE", "category": "complexity", "likelihood": "medium", "impact": "low",
         "description": "Fast feedback cycles may prioritize visible features over infrastructure quality.",
         "mitigation": "Allocate 20% of each iteration to non-functional requirements (tests, docs, refactoring).", "signal_trigger": "Test coverage drops below 70% or CI runtime exceeds budget."},
    ],
    "offline-first": [
        {"id": "RISK-OFFLINE-SYNC", "category": "complexity", "likelihood": "high", "impact": "high",
         "description": "Offline-first architectures introduce conflict resolution and data consistency challenges.",
         "mitigation": "Use CRDTs or last-write-wins with server-side conflict audit log.", "signal_trigger": "Sync conflict rate exceeds 1% of operations."},
    ],
    "multi-tenant": [
        {"id": "RISK-MT-ISOLATION", "category": "security", "likelihood": "medium", "impact": "high",
         "description": "Multi-tenant data isolation bugs can expose one tenant's data to another.",
         "mitigation": "Use row-level security; add tenant-isolation integration tests; audit query filters.", "signal_trigger": "Security audit or penetration test finds tenant isolation flaw."},
    ],
    "real-time": [
        {"id": "RISK-RT-SCALE", "category": "performance", "likelihood": "medium", "impact": "high",
         "description": "Real-time WebSocket connections are stateful and harder to scale horizontally than REST.",
         "mitigation": "Use Redis pub/sub as a WebSocket backplane; design for graceful connection loss.", "signal_trigger": "WebSocket connection count exceeds single-server capacity."},
    ],
}


def generate_risks(
    primary_stack: str,
    secondary_stacks: Optional[List[str]] = None,
    creative_signals: Optional[List[str]] = None,
    evidence_provisional: bool = False,
) -> List[RiskItem]:
    """Generate a context-aware risk register for the architecture."""
    risks: List[RiskItem] = []

    # Stack-specific risks (from templates)
    for template_dict in STACK_RISK_TEMPLATES.get(primary_stack, []):
        risks.append(RiskItem.from_dict(template_dict))

    for stack_name in (secondary_stacks or []):
        for template_dict in STACK_RISK_TEMPLATES.get(stack_name, []):
            r = RiskItem.from_dict(template_dict)
            if not any(existing.id == r.id for existing in risks):
                risks.append(r)

    # Creative-signal-specific risks
    for signal in (creative_signals or []):
        for template_dict in CREATIVE_RISK_TEMPLATES.get(signal, []):
            r = RiskItem.from_dict(template_dict)
            if not any(existing.id == r.id for existing in risks):
                risks.append(r)

    # Evidence-quality risk
    if evidence_provisional:
        risks.append(RiskItem(
            id="RISK-EVID-PROVISIONAL",
            category="maintenance",
            description="Architecture decision relies on provisional evidence; stack may need revision when fresh data arrives.",
            likelihood="medium", impact="medium",
            mitigation="Refresh evidence within 30 days. Do not commit to long-term infrastructure contracts on provisional data.",
            signal_trigger="Fresh evidence contradicts the current architecture choice."
        ))

    # Always add a generic revisit trigger
    risks.append(RiskItem(
        id="RISK-REVISIT-SCOPE",
        category="complexity",
        description="Project scope may expand beyond the original creative direction, invalidating current architecture assumptions.",
        likelihood="medium", impact="medium",
        mitigation="Run project-forge revise whenever a significant new feature or constraint is introduced.",
        signal_trigger="A new feature, stakeholder, or constraint is introduced that was not in the original ADR context."
    ))

    return risks


def render_risk_section(risks: List[RiskItem]) -> str:
    """Render the risk register as Markdown for ADRs and handoffs."""
    if not risks:
        return "No formal risks registered."

    lines = ["| ID | Category | Likelihood | Impact | Description | Mitigation |",
             "|----|----------|------------|--------|-------------|------------|"]
    for r in risks:
        lines.append(
            f"| {r.id} | {r.category} | {r.likelihood} | {r.impact} | {r.description} | {r.mitigation} |"
        )
    return "\n".join(lines)
