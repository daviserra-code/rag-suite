"""
Violation Audit Persistence
Sprint 4 Extension - STEP 3

Provides audit-grade persistence for expectation violations.
Supports A&D compliance requirements:
- No duplicates
- Full traceability
- Human acknowledgment
- Historical analysis
"""

import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger(__name__)


class ViolationPersistence:
    """
    Manages violation persistence to PostgreSQL.
    
    Key responsibilities:
    - Upsert violations (create or update)
    - No duplicates (same station + conditions)
    - Close violations when resolved
    - Query active/historical violations
    """
    
    def __init__(self, db_connection_string: Optional[str] = None):
        """
        Initialize persistence layer.
        
        Args:
            db_connection_string: PostgreSQL connection string
                                 If None, reads from environment
        """
        self.connection_string = db_connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/ragdb'
        )
    
    def upsert_violation(
        self,
        profile: str,
        plant: str,
        line: str,
        station: str,
        expectation_result,
        material_context: Optional[Dict] = None,
        snapshot_ref: Optional[Dict] = None
    ) -> uuid.UUID:
        """
        Upsert a violation.
        
        If a violation with same station and blocking_conditions exists,
        update it. Otherwise, create new violation.
        
        Args:
            profile: Domain profile name
            plant: Plant identifier
            line: Line identifier
            station: Station identifier
            expectation_result: ExpectationResult from evaluation
            material_context: Material context snapshot
            snapshot_ref: OPC snapshot reference
        
        Returns:
            UUID of violation record
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check for existing active violation with same conditions
            cursor.execute("""
                SELECT id FROM violations
                WHERE station = %s
                  AND ts_end IS NULL
                  AND blocking_conditions = %s::jsonb
                ORDER BY ts_start DESC
                LIMIT 1
            """, (
                station,
                Json(expectation_result.blocking_conditions)
            ))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing violation
                violation_id = existing['id']
                cursor.execute("""
                    UPDATE violations
                    SET violated_expectations = %s::jsonb,
                        warnings = %s::jsonb,
                        severity = %s,
                        requires_human_confirmation = %s,
                        material_ref = %s::jsonb,
                        snapshot_ref = %s::jsonb,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    Json(expectation_result.violated_expectations),
                    Json(expectation_result.warnings),
                    expectation_result.severity,
                    expectation_result.requires_human_confirmation,
                    Json(material_context or {}),
                    Json(snapshot_ref or {}),
                    violation_id
                ))
                
                logger.info(f"Updated existing violation {violation_id} for {station}")
            else:
                # Create new violation
                cursor.execute("""
                    INSERT INTO violations (
                        profile, plant, line, station,
                        severity, requires_human_confirmation,
                        violated_expectations, blocking_conditions, warnings,
                        material_ref, snapshot_ref
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb)
                    RETURNING id
                """, (
                    profile,
                    plant,
                    line,
                    station,
                    expectation_result.severity,
                    expectation_result.requires_human_confirmation,
                    Json(expectation_result.violated_expectations),
                    Json(expectation_result.blocking_conditions),
                    Json(expectation_result.warnings),
                    Json(material_context or {}),
                    Json(snapshot_ref or {})
                ))
                
                violation_id = cursor.fetchone()['id']
                logger.info(f"Created new violation {violation_id} for {station}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return violation_id
            
        except Exception as e:
            logger.error(f"Failed to upsert violation for {station}: {e}")
            raise
    
    def close_violation(self, violation_id: uuid.UUID) -> bool:
        """
        Close a violation (set ts_end).
        
        Args:
            violation_id: UUID of violation to close
        
        Returns:
            True if closed, False if not found or already closed
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE violations
                SET ts_end = NOW()
                WHERE id = %s AND ts_end IS NULL
            """, (str(violation_id),))
            
            rows_affected = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"Closed violation {violation_id}")
                return True
            else:
                logger.warning(f"Violation {violation_id} not found or already closed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to close violation {violation_id}: {e}")
            return False
    
    def close_violations_by_station(self, station: str) -> int:
        """
        Close all active violations for a station.
        
        Args:
            station: Station identifier
        
        Returns:
            Number of violations closed
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE violations
                SET ts_end = NOW()
                WHERE station = %s AND ts_end IS NULL
            """, (station,))
            
            rows_affected = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Closed {rows_affected} violations for {station}")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Failed to close violations for {station}: {e}")
            return 0
    
    def add_acknowledgment(
        self,
        violation_id: uuid.UUID,
        ack_by: str,
        ack_type: str,
        comment: Optional[str] = None,
        evidence_ref: Optional[str] = None
    ) -> Optional[int]:
        """
        Add acknowledgment to a violation.
        
        Args:
            violation_id: UUID of violation
            ack_by: User ID/name
            ack_type: 'acknowledged', 'justified', 'false_positive', 'resolved'
            comment: Optional comment
            evidence_ref: Optional reference to external evidence
        
        Returns:
            Acknowledgment ID, or None if failed
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO violation_ack (
                    violation_id, ack_by, ack_type, comment, evidence_ref
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(violation_id),
                ack_by,
                ack_type,
                comment,
                evidence_ref
            ))
            
            ack_id = cursor.fetchone()[0]
            
            # If ack_type is 'resolved', close the violation
            if ack_type == 'resolved':
                cursor.execute("""
                    UPDATE violations
                    SET ts_end = NOW()
                    WHERE id = %s AND ts_end IS NULL
                """, (str(violation_id),))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Added acknowledgment {ack_id} to violation {violation_id} by {ack_by}")
            return ack_id
            
        except Exception as e:
            logger.error(f"Failed to add acknowledgment to {violation_id}: {e}")
            return None
    
    def get_active_violations(
        self,
        station: Optional[str] = None,
        profile: Optional[str] = None,
        blocking_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get active violations.
        
        Args:
            station: Optional filter by station
            profile: Optional filter by profile
            blocking_only: If True, only return blocking violations
        
        Returns:
            List of violation records
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM v_violations_active WHERE 1=1"
            params = []
            
            if station:
                query += " AND station = %s"
                params.append(station)
            
            if profile:
                query += " AND profile = %s"
                params.append(profile)
            
            if blocking_only:
                query += " AND requires_human_confirmation = true"
            
            query += " ORDER BY ts_start DESC"
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query active violations: {e}")
            return []
    
    def get_violation_history(
        self,
        station: Optional[str] = None,
        profile: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get violation history (closed violations).
        
        Args:
            station: Optional filter by station
            profile: Optional filter by profile
            limit: Maximum number of records
        
        Returns:
            List of historical violation records
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM v_violations_history WHERE 1=1"
            params = []
            
            if station:
                query += " AND station = %s"
                params.append(station)
            
            if profile:
                query += " AND profile = %s"
                params.append(profile)
            
            query += " ORDER BY ts_end DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query violation history: {e}")
            return []
    
    def get_violation_by_id(self, violation_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific violation by ID.
        
        Args:
            violation_id: UUID of violation
        
        Returns:
            Violation record, or None if not found
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM violations WHERE id = %s
            """, (str(violation_id),))
            
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get violation {violation_id}: {e}")
            return None
    
    def get_violation_timeline(self, violation_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get full timeline for a violation including all acknowledgments.
        
        Returns:
            {
                'violation': {...},
                'acknowledgments': [...],
                'state': 'OPEN' | 'ACKNOWLEDGED' | 'JUSTIFIED' | 'RESOLVED'
            }
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get violation
            cursor.execute("""
                SELECT * FROM violations WHERE id = %s
            """, (str(violation_id),))
            
            violation = cursor.fetchone()
            
            if not violation:
                cursor.close()
                conn.close()
                return None
            
            # Get all acknowledgments
            cursor.execute("""
                SELECT * FROM violation_ack
                WHERE violation_id = %s
                ORDER BY ts ASC
            """, (str(violation_id),))
            
            acks = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            # Determine state
            state = self._compute_violation_state(dict(violation), acks)
            
            return {
                'violation': dict(violation),
                'acknowledgments': acks,
                'state': state,
                'ack_count': len(acks)
            }
            
        except Exception as e:
            logger.error(f"Failed to get timeline for {violation_id}: {e}")
            return None
    
    def _compute_violation_state(self, violation: Dict, acks: List[Dict]) -> str:
        """
        Compute current state of a violation based on ts_end and acknowledgments.
        
        State logic:
        - RESOLVED: ts_end is set
        - JUSTIFIED: has 'justified' ack and ts_end is NULL
        - ACKNOWLEDGED: has 'acknowledged' ack and ts_end is NULL
        - OPEN: no acks and ts_end is NULL
        """
        if violation.get('ts_end'):
            return 'RESOLVED'
        
        if not acks:
            return 'OPEN'
        
        # Check for justified state
        for ack in reversed(acks):  # Most recent first
            if ack['ack_type'] == 'justified':
                return 'JUSTIFIED'
            elif ack['ack_type'] == 'acknowledged':
                return 'ACKNOWLEDGED'
        
        return 'OPEN'
    
    def acknowledge_violation(
        self,
        violation_id: uuid.UUID,
        ack_by: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Acknowledge a violation (user has seen it).
        
        This is a convenience wrapper for add_acknowledgment.
        """
        ack_id = self.add_acknowledgment(
            violation_id=violation_id,
            ack_by=ack_by,
            ack_type='acknowledged',
            comment=comment
        )
        return ack_id is not None
    
    def justify_violation(
        self,
        violation_id: uuid.UUID,
        ack_by: str,
        comment: str,
        evidence_ref: Optional[str] = None
    ) -> bool:
        """
        Justify a violation (temporary acceptance with reason).
        
        Requires a comment explaining the justification.
        """
        if not comment:
            logger.error("Justification requires a comment")
            return False
        
        ack_id = self.add_acknowledgment(
            violation_id=violation_id,
            ack_by=ack_by,
            ack_type='justified',
            comment=comment,
            evidence_ref=evidence_ref
        )
        return ack_id is not None
    
    def resolve_violation(
        self,
        violation_id: uuid.UUID,
        ack_by: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Resolve a violation (close it).
        
        This should only be called when the underlying condition is fixed.
        Adds a 'resolved' acknowledgment and sets ts_end.
        """
        ack_id = self.add_acknowledgment(
            violation_id=violation_id,
            ack_by=ack_by,
            ack_type='resolved',
            comment=comment
        )
        return ack_id is not None


# Global singleton instance
_persistence = None


def get_violation_persistence() -> ViolationPersistence:
    """Get or create global ViolationPersistence instance"""
    global _persistence
    if _persistence is None:
        _persistence = ViolationPersistence()
    return _persistence
