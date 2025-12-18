"""
Diagnostics Package
Sprint 3 — AI-Grounded Diagnostics & Explainability

Provides AI-driven, explainable diagnostics based on:
- Semantic signals (Sprint 2)
- Loss category taxonomy
- Runtime context (OPC / semantic snapshot)
- RAG knowledge (WI, SOP, tickets)
"""

from .explainer import DiagnosticsExplainer

__all__ = ['DiagnosticsExplainer']
