"""
SAP ERP Stub Provider - Sprint 7

Stub implementation for SAP integration.
Returns deterministic mock data.

DO NOT implement real SAP connection in this sprint.
"""

from typing import Optional, Dict, Any
from .interface import ExternalContextProvider


class SAPStubProvider(ExternalContextProvider):
    """
    Stub provider for SAP ERP integration.
    
    Future implementation would connect to:
    - SAP ECC or S/4HANA
    - SAP MII (Manufacturing Integration & Intelligence)
    - SAP ME (Manufacturing Execution)
    
    Currently returns mock data only.
    """
    
    def get_material_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get material context from SAP (stub).
        
        Real implementation would query:
        - AFPO (Production Order Items)
        - MARC (Plant Data for Material)
        - MARA (General Material Data)
        """
        if not self.enabled:
            return None
        
        # Mock data - profile-aware
        return {
            "source": "SAP_STUB",
            "work_order": f"WO-{equipment_id}-{hash(equipment_id) % 10000}",
            "material_number": f"MAT-{hash(equipment_id) % 1000:04d}",
            "batch_lot": f"BATCH-2025-{hash(equipment_id) % 100:03d}",
            "quantity_planned": 100,
            "quantity_completed": hash(equipment_id) % 50,
            "bom_revision": "A",
            "routing_revision": "001",
            "plant": "1000",
            "mrp_controller": "001"
        }
    
    def get_quality_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get quality context from SAP QM (stub).
        
        Real implementation would query:
        - QALS (Quality Notifications)
        - QAVE (Usage Decisions)
        - QM01 (Inspection Lot)
        """
        if not self.enabled:
            return None
        
        # Mock data based on equipment ID hash
        status_options = ["RELEASED", "HOLD", "INSPECTION", "APPROVED"]
        status = status_options[hash(equipment_id) % len(status_options)]
        
        return {
            "source": "SAP_QM_STUB",
            "quality_status": status,
            "inspection_lot": f"IL-{hash(equipment_id) % 100000:06d}",
            "usage_decision": "UD-PENDING" if status == "HOLD" else "UD-APPROVED",
            "quality_score": 95.5 + (hash(equipment_id) % 5),
            "last_inspection": "2025-12-25T10:00:00Z",
            "inspector": "QC_TEAM_001"
        }
    
    def get_tooling_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tooling/equipment context from SAP PM (stub).
        
        Real implementation would query:
        - EQUI (Equipment Master)
        - ILOA (Functional Location)
        - PM03 (Maintenance Orders)
        """
        if not self.enabled:
            return None
        
        return {
            "source": "SAP_PM_STUB",
            "equipment_number": equipment_id,
            "calibration_due": "2025-12-31",
            "calibration_status": "VALID",
            "maintenance_plan": f"PM-{equipment_id}-001",
            "next_maintenance": "2026-01-15",
            "functional_location": f"PLANT-AREA-{equipment_id}",
            "asset_number": f"ASSET-{hash(equipment_id) % 10000:05d}"
        }
    
    def get_process_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get process parameters from SAP MII/PCo (stub).
        
        Real implementation would query:
        - SAP MII Workbench
        - Process Historian
        - Recipe Management
        """
        if not self.enabled:
            return None
        
        return {
            "source": "SAP_MII_STUB",
            "recipe_id": f"RECIPE-{hash(equipment_id) % 100:03d}",
            "recipe_version": "1.2",
            "process_parameters": {
                "temperature": 25.0 + (hash(equipment_id) % 10),
                "pressure": 1.0 + (hash(equipment_id) % 5) * 0.1,
                "speed": 100 + (hash(equipment_id) % 50)
            },
            "cpk": 1.33 + (hash(equipment_id) % 10) * 0.1,
            "process_capability": "CAPABLE"
        }
    
    def get_traceability_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get traceability data from SAP (stub).
        
        Real implementation would query:
        - SAP ME Traceability
        - Serial Number Management
        - Batch Genealogy
        """
        if not self.enabled:
            return None
        
        return {
            "source": "SAP_ME_STUB",
            "serial_numbers": [f"SN-{equipment_id}-{i:05d}" for i in range(1, 4)],
            "parent_serial": f"PARENT-{equipment_id}-00001",
            "supplier_batch": f"SUPPLIER-BATCH-{hash(equipment_id) % 1000}",
            "receiving_inspection": "PASS",
            "material_cert": f"CERT-{hash(equipment_id) % 10000}"
        }
