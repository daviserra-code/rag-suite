"""
External Context Providers - Sprint 7
Read-only, non-intrusive connectivity skeletons

Core Principle:
    External systems enrich context.
    They never drive decisions directly.

All providers are:
- Read-only
- Optional
- Pluggable
- Disabled by default
"""

from .interface import ExternalContextProvider
from .sap_stub import SAPStubProvider
from .plm_stub import PLMStubProvider
from .qms_stub import QMSStubProvider
from .cmms_stub import CMMSStubProvider
from .opcua_stub import OPCUAStubProvider

__all__ = [
    "ExternalContextProvider",
    "SAPStubProvider",
    "PLMStubProvider", 
    "QMSStubProvider",
    "CMMSStubProvider",
    "OPCUAStubProvider"
]
