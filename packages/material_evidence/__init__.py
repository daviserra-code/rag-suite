"""
Material Evidence Provider
Sprint 4 Extension - STEP 2

Provides material context and evidence for expectation evaluation.
This is a demo-realistic provider that reads from PostgreSQL.

In production, this would integrate with:
- ERP systems (SAP, Oracle)
- MES systems (Siemens Opcenter, GE Digital)
- PLM systems (PTC Windchill, Siemens Teamcenter)
- QMS systems (TrackWise, MasterControl)

For demo purposes, this reads from local PostgreSQL tables.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


@dataclass
class MaterialContext:
    """
    Material evidence context for a specific station at a point in time.
    
    This provides concrete evidence for profile-driven expectations.
    """
    # Material identification
    mode: Optional[str] = None  # "serial" | "lot" | None
    active_serial: Optional[str] = None
    active_lot: Optional[str] = None
    
    # Work order context
    work_order: Optional[str] = None
    operation: Optional[str] = None
    
    # Engineering/revision control
    bom_revision: Optional[str] = None
    as_built_revision: Optional[str] = None
    
    # Quality status
    quality_status: Optional[str] = None  # "RELEASED" | "HOLD" | "QUARANTINE"
    deviation_id: Optional[str] = None
    
    # Authorization & compliance
    dry_run_authorization: bool = False
    tooling_calibration_ok: bool = False
    operator_certified: bool = False
    
    # Additional context
    material_ref: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "mode": self.mode,
            "active_serial": self.active_serial,
            "active_lot": self.active_lot,
            "work_order": self.work_order,
            "operation": self.operation,
            "bom_revision": self.bom_revision,
            "as_built_revision": self.as_built_revision,
            "quality_status": self.quality_status,
            "deviation_id": self.deviation_id,
            "dry_run_authorization": self.dry_run_authorization,
            "tooling_calibration_ok": self.tooling_calibration_ok,
            "operator_certified": self.operator_certified
        }


class MaterialEvidenceProvider:
    """
    Provider for material evidence from demo PostgreSQL database.
    
    This is a READ-ONLY provider that queries material context
    for expectation evaluation.
    """
    
    def __init__(self, db_connection_string: Optional[str] = None):
        """
        Initialize provider with database connection.
        
        Args:
            db_connection_string: PostgreSQL connection string
                                 If None, reads from environment
        """
        self.connection_string = db_connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/ragdb'
        )
    
    def get_material_context(
        self,
        plant: str,
        line: str,
        station: str
    ) -> MaterialContext:
        """
        Get material context for a specific station.
        
        This queries:
        - material_instances (serial/lot binding)
        - material_authorizations (dry-run auth, deviations)
        - tooling_status (calibration)
        - operator_certifications (operator qualifications)
        
        Args:
            plant: Plant identifier
            line: Line identifier
            station: Station identifier
        
        Returns:
            MaterialContext with all available evidence
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Query material instance
            material = self._get_material_instance(cursor, plant, line, station)
            
            # Query authorizations
            auth = self._get_authorizations(cursor, station)
            
            # Query tooling status
            tooling = self._get_tooling_status(cursor, station)
            
            # Query operator certification
            operator = self._get_operator_certification(cursor, station)
            
            # Combine into MaterialContext
            context = MaterialContext(
                mode=material.get('mode'),
                active_serial=material.get('serial'),
                active_lot=material.get('lot'),
                work_order=material.get('work_order'),
                operation=material.get('operation'),
                bom_revision=material.get('bom_revision'),
                as_built_revision=material.get('as_built_revision'),
                quality_status=material.get('quality_status'),
                deviation_id=auth.get('deviation_id'),
                dry_run_authorization=auth.get('dry_run_authorization', False),
                tooling_calibration_ok=tooling.get('calibration_ok', False),
                operator_certified=operator.get('certified', False),
                material_ref={
                    "material_id": material.get('id'),
                    "station_id": station
                }
            )
            
            cursor.close()
            conn.close()
            
            logger.info(f"Material context retrieved for {station}: mode={context.mode}, serial={context.active_serial}")
            
            return context
            
        except Exception as e:
            logger.warning(f"Could not retrieve material context for {station}: {e}")
            # Return empty context on error (demo-friendly)
            return MaterialContext()
    
    def _get_material_instance(self, cursor, plant: str, line: str, station: str) -> Dict:
        """Query material_instances table"""
        try:
            cursor.execute("""
                SELECT 
                    id, mode, serial, lot, work_order, operation,
                    bom_revision, as_built_revision, quality_status
                FROM material_instances
                WHERE plant = %s AND line = %s AND station = %s
                  AND active = true
                ORDER BY ts DESC
                LIMIT 1
            """, (plant, line, station))
            
            result = cursor.fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.debug(f"No material instance found: {e}")
            return {}
    
    def _get_authorizations(self, cursor, station: str) -> Dict:
        """Query material_authorizations table"""
        try:
            cursor.execute("""
                SELECT dry_run_authorization, deviation_id
                FROM material_authorizations
                WHERE station_id = %s
                  AND active = true
                ORDER BY ts DESC
                LIMIT 1
            """, (station,))
            
            result = cursor.fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.debug(f"No authorizations found: {e}")
            return {}
    
    def _get_tooling_status(self, cursor, station: str) -> Dict:
        """Query tooling_status table"""
        try:
            cursor.execute("""
                SELECT calibration_ok, calibration_due_date
                FROM tooling_status
                WHERE station_id = %s
                  AND active = true
                ORDER BY ts DESC
                LIMIT 1
            """, (station,))
            
            result = cursor.fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.debug(f"No tooling status found: {e}")
            return {}
    
    def _get_operator_certification(self, cursor, station: str) -> Dict:
        """Query operator_certifications table"""
        try:
            cursor.execute("""
                SELECT certified, operator_id
                FROM operator_certifications
                WHERE station_id = %s
                  AND active = true
                ORDER BY ts DESC
                LIMIT 1
            """, (station,))
            
            result = cursor.fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.debug(f"No operator certification found: {e}")
            return {}


# Global singleton instance
_provider = None


def get_material_evidence_provider() -> MaterialEvidenceProvider:
    """Get or create global MaterialEvidenceProvider instance"""
    global _provider
    if _provider is None:
        _provider = MaterialEvidenceProvider()
    return _provider


def get_material_context(plant: str, line: str, station: str) -> MaterialContext:
    """
    Convenience function to get material context.
    
    Args:
        plant: Plant identifier
        line: Line identifier
        station: Station identifier
    
    Returns:
        MaterialContext with all available evidence
    """
    provider = get_material_evidence_provider()
    return provider.get_material_context(plant, line, station)
