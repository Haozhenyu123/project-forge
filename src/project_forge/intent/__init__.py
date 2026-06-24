"""Project Forge intent classification and domain profile system.

Classifies user project ideas into domain labels (medical, finance, gaming, etc.),
product forms (web-app, mini-program, etc.), and technical features (ai-ml, real-time, etc.).
Provides domain-specific configuration: required questions, architecture patterns,
compliance constraints, evidence sources, and risk-adjusted scoring weights.
"""

from .classifier import classify_intent
from .models import DomainProfile, IntentResult

__all__ = ["classify_intent", "DomainProfile", "IntentResult"]
