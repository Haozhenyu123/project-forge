"""Typed intent and domain profile records."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DomainProfile:
    domain: str
    domain_profile: str = ""
    probing_axes: List[Dict] = field(default_factory=list)
    compliance: List[str] = field(default_factory=list)
    risk_weights: Dict[str, float] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "DomainProfile":
        return cls(
            domain=data.get("domain", "general"),
            domain_profile=data.get("domain_profile", ""),
            probing_axes=data.get("probing_axes", []),
            compliance=data.get("compliance", []),
            risk_weights=data.get("risk_weights", {}),
            capabilities=data.get("capabilities", []),
        )

    def to_dict(self) -> Dict:
        return {
            "domain": self.domain,
            "domain_profile": self.domain_profile,
            "probing_axes": self.probing_axes,
            "compliance": self.compliance,
            "risk_weights": self.risk_weights,
            "capabilities": self.capabilities,
        }


@dataclass
class IntentResult:
    primary_domain: str
    domain_confidence: float
    all_domains: Dict[str, float] = field(default_factory=dict)
    product_form: str = "web-app"
    product_form_confidence: float = 0.0
    technical_features: List[str] = field(default_factory=list)
    recommended_questions: List[str] = field(default_factory=list)
    domain_profile: Optional[DomainProfile] = None

    def to_dict(self) -> Dict:
        return {
            "primary_domain": self.primary_domain,
            "domain_confidence": self.domain_confidence,
            "all_domains": self.all_domains,
            "product_form": self.product_form,
            "product_form_confidence": self.product_form_confidence,
            "technical_features": self.technical_features,
            "recommended_questions": self.recommended_questions,
        }
