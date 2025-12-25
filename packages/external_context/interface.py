"""
External Context Provider Interface - Sprint 7

Defines common interface for all external system integrations.
All methods are read-only and return optional enrichment data.
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class ExternalContextProvider(ABC):
    """
    Base interface for external context providers.
    
    Core Principles:
    - Read-only: No write operations to external systems
    - Optional: System works without external data
    - Enrichment: Data supplements diagnostics, never drives decisions
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration (credentials, URLs, etc.)
        """
        self.config = config
        self.enabled = config.get("enabled", False)
    
    @abstractmethod
    def get_material_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get material/work order context for equipment.
        
        Examples:
        - Work order number
        - Material batch/lot
        - BOM information
        - Revision level
        
        Args:
            equipment_id: Station/equipment identifier
            
        Returns:
            Dictionary with material context, or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_quality_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get quality/inspection context for equipment.
        
        Examples:
        - Quality status (RELEASED, HOLD, REJECTED)
        - Inspection results
        - Deviation records
        - NCR (Non-Conformance Report) status
        
        Args:
            equipment_id: Station/equipment identifier
            
        Returns:
            Dictionary with quality context, or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_tooling_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tooling/maintenance context for equipment.
        
        Examples:
        - Tool calibration status
        - Maintenance schedule
        - Preventive maintenance due date
        - Tool life remaining
        
        Args:
            equipment_id: Station/equipment identifier
            
        Returns:
            Dictionary with tooling context, or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_process_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get process parameters context for equipment.
        
        Examples:
        - Process recipe
        - Parameter setpoints
        - Operating window limits
        - Process capability (Cpk)
        
        Args:
            equipment_id: Station/equipment identifier
            
        Returns:
            Dictionary with process context, or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_traceability_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get traceability context for equipment.
        
        Examples:
        - Serial numbers
        - Genealogy/parent-child relationships
        - Material evidence records
        - Supplier traceability
        
        Args:
            equipment_id: Station/equipment identifier
            
        Returns:
            Dictionary with traceability context, or None if unavailable
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self.enabled
    
    def get_provider_name(self) -> str:
        """Get human-readable provider name."""
        return self.__class__.__name__
