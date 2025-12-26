"""
Pages Module - Route-based navigation for Shopfloor Copilot

This module contains all @ui.page decorated routes.
Import this module to register all routes before running the app.
"""

# Import all page modules to register routes
from . import landing, legacy, violations
from .operations import live, lines, plant, dashboard, heatmap
from .quality import rca, why, compare
from .maintenance import diagnostics, predictive, handover
from .connectivity import opc_explorer, semantic_signals, opc_studio
from .intelligence import copilot, qna, filters, citations
from .analytics import kpi, reports, energy
from .advanced import twin, tickets, mobile
from .settings import profiles

__all__ = [
    'landing',
    'legacy',
    'violations',
    'live', 'lines', 'plant', 'dashboard', 'heatmap',
    'rca', 'why', 'compare',
    'diagnostics', 'predictive', 'handover',
    'opc_explorer', 'semantic_signals', 'opc_studio',
    'copilot', 'qna', 'filters', 'citations',
    'kpi', 'reports', 'energy',
    'twin', 'tickets', 'mobile',
    'profiles',
]
