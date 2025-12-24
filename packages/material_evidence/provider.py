"""Material Evidence package - provides material context for expectation evaluation"""

from .provider import (
    MaterialContext,
    MaterialEvidenceProvider,
    get_material_context,
    get_material_evidence_provider
)

__all__ = [
    'MaterialContext',
    'MaterialEvidenceProvider',
    'get_material_context',
    'get_material_evidence_provider'
]
