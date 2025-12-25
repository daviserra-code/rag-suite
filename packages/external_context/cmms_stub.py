"""
CMMS (Computerized Maintenance Management System) Stub Provider - Sprint 7

Stub implementation for CMMS integration.
Returns deterministic mock data for maintenance context.

DO NOT implement real CMMS connection in this sprint.
"""

from typing import Optional, Dict, Any
from .interface import ExternalContextProvider


class CMMSStubProvider(ExternalContextProvider):
    """
    Stub provider for CMMS integration.
    
    Future implementation would connect to:
    - IBM Maximo
    - Infor EAM
    - SAP PM
    - Fiix
    
    Currently returns mock data only.
    """
    
    def get_material_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get spare parts inventory from CMMS (stub).
        
        Real implementation would query:
        - Spare parts availability
        - Parts usage history
        - Reorder points
        """
        if not self.enabled:
            return None
        
        return {
            "source": "CMMS_PARTS_STUB",
            "critical_spares": [
                {
                    "part_number": f"SPARE-{hash(equipment_id + str(i)) % 1000:04d}",
                    "description": f"Critical Component {i}",
                    "quantity_on_hand": 5 + (hash(equipment_id + str(i)) % 10),
                    "min_stock": 3,
                    "leadtime_days": 14
                }
                for i in range(1, 4)
            ],
            "parts_criticality": "HIGH" if hash(equipment_id) % 3 == 0 else "MEDIUM"
        }
    
    def get_quality_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get equipment reliability data from CMMS (stub).
        
        Real implementation would query:
        - Failure history
        - MTBF/MTTR metrics
        - Reliability analysis
        """
        if not self.enabled:
            return None
        
        return {
            "source": "CMMS_RELIABILITY_STUB",
            "mtbf_hours": 1000 + (hash(equipment_id) % 500),
            "mttr_hours": 2 + (hash(equipment_id) % 10) * 0.5,
            "failure_rate": 0.001 + (hash(equipment_id) % 10) * 0.0001,
            "reliability_score": 85 + (hash(equipment_id) % 15),
            "recent_failures": hash(equipment_id) % 5,
            "failure_trend": "STABLE"
        }
    
    def get_tooling_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get maintenance and calibration records from CMMS (stub).
        
        Real implementation would query:
        - Maintenance history
        - Work orders
        - Calibration schedules
        """
        if not self.enabled:
            return None
        
        # Deterministic maintenance status
        days_since_pm = hash(equipment_id) % 90
        pm_overdue = days_since_pm > 80
        
        return {
            "source": "CMMS_MAINTENANCE_STUB",
            "last_pm_date": "2025-10-01",
            "next_pm_date": "2026-01-01",
            "pm_status": "OVERDUE" if pm_overdue else "SCHEDULED",
            "work_orders_open": [
                {
                    "wo_number": f"WO-{hash(equipment_id + str(i)) % 10000:06d}",
                    "type": "PREVENTIVE" if i == 1 else "CORRECTIVE",
                    "priority": "HIGH" if pm_overdue else "MEDIUM",
                    "status": "OPEN",
                    "created_date": "2025-12-20"
                }
                for i in range(1, 2 if not pm_overdue else 3)
            ],
            "maintenance_backlog_hours": hash(equipment_id) % 50,
            "equipment_condition": "GOOD" if not pm_overdue else "FAIR"
        }
    
    def get_process_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get equipment performance data from CMMS (stub).
        
        Real implementation would query:
        - OEE (Overall Equipment Effectiveness)
        - Availability metrics
        - Performance metrics
        """
        if not self.enabled:
            return None
        
        availability = 85 + (hash(equipment_id) % 15)
        performance = 90 + (hash(equipment_id) % 10)
        quality = 95 + (hash(equipment_id) % 5)
        oee = (availability * performance * quality) / 10000
        
        return {
            "source": "CMMS_PERFORMANCE_STUB",
            "oee_percentage": round(oee, 2),
            "availability_percentage": availability,
            "performance_percentage": performance,
            "quality_percentage": quality,
            "downtime_hours_last_30d": hash(equipment_id) % 20,
            "utilization_percentage": 75 + (hash(equipment_id) % 25)
        }
    
    def get_traceability_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get equipment history from CMMS (stub).
        
        Real implementation would query:
        - Equipment modifications
        - Upgrade history
        - Configuration changes
        """
        if not self.enabled:
            return None
        
        return {
            "source": "CMMS_HISTORY_STUB",
            "equipment_age_years": 5 + (hash(equipment_id) % 10),
            "major_overhauls": hash(equipment_id) % 3,
            "last_major_repair": "2024-06-15",
            "configuration_changes": [
                {
                    "date": "2025-03-10",
                    "change": "Software upgrade v2.1",
                    "change_order": f"CO-{hash(equipment_id) % 1000:04d}"
                }
            ],
            "warranty_status": "EXPIRED" if hash(equipment_id) % 2 == 0 else "ACTIVE",
            "warranty_expiry": "2026-12-31"
        }
