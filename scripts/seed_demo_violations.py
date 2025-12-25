#!/usr/bin/env python3
"""
Demo Seed Data - Violation Lifecycle Examples
Sprint 4 Extension - STEP 3.1

Seeds demonstration violations showing all lifecycle states:
1. OPEN - A&D violation (missing serial)
2. ACKNOWLEDGED - User has seen it
3. JUSTIFIED - Pharma violation with temporary deviation
4. RESOLVED - Historical violation that was fixed

Run this script to populate demo violations for testing and demonstration.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import Json

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

def seed_demo_violations():
    """Seed demonstration violations showing all lifecycle states."""
    
    print("🌱 Seeding demo violations for lifecycle demonstration...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Clean up any existing demo violations
        print("Cleaning up existing demo violations...")
        cursor.execute("""
            DELETE FROM violation_ack WHERE violation_id IN (
                SELECT id FROM violations WHERE plant = 'DEMO'
            )
        """)
        cursor.execute("DELETE FROM violations WHERE plant = 'DEMO'")
        conn.commit()
        
        # ============================================================================
        # Scenario 1: OPEN A&D Violation (Missing Serial)
        # ============================================================================
        
        print("\n1️⃣  Creating OPEN violation (A&D - Missing Serial)...")
        
        violation_1_id = uuid.uuid4()
        cursor.execute("""
            INSERT INTO violations (
                id, profile, plant, line, station,
                severity, requires_human_confirmation,
                violated_expectations, blocking_conditions, warnings,
                material_ref, snapshot_ref,
                ts_start
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb,
                %s::jsonb, %s::jsonb,
                %s
            )
        """, (
            str(violation_1_id),
            'Aerospace & Defence',
            'DEMO',
            'A01',
            'ST18',
            'critical',
            True,
            Json(['critical_station_requires_evidence', 'missing_serial_binding']),
            Json(['missing_material_context', 'missing_serial_binding']),
            Json(['Station ST18 has no material evidence record']),
            Json({'evidence_present': False, 'mode': 'serial'}),
            Json({'timestamp': datetime.utcnow().isoformat()}),
            datetime.utcnow() - timedelta(hours=2)
        ))
        
        print(f"   ✅ Created OPEN violation: {violation_1_id}")
        print(f"      Station: ST18 | Profile: A&D | Severity: critical")
        print(f"      Blocking: missing_material_context, missing_serial_binding")
        
        # ============================================================================
        # Scenario 2: ACKNOWLEDGED Violation
        # ============================================================================
        
        print("\n2️⃣  Creating ACKNOWLEDGED violation...")
        
        violation_2_id = uuid.uuid4()
        cursor.execute("""
            INSERT INTO violations (
                id, profile, plant, line, station,
                severity, requires_human_confirmation,
                violated_expectations, blocking_conditions, warnings,
                material_ref, snapshot_ref,
                ts_start
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb,
                %s::jsonb, %s::jsonb,
                %s
            )
        """, (
            str(violation_2_id),
            'Aerospace & Defence',
            'DEMO',
            'A01',
            'ST22',
            'warning',
            False,
            Json(['reduced_speed_requires_justification']),
            Json([]),
            Json(['Station running at reduced speed - justification required']),
            Json({'evidence_present': True, 'mode': 'serial', 'active_serial': 'SN-12345'}),
            Json({'timestamp': datetime.utcnow().isoformat()}),
            datetime.utcnow() - timedelta(hours=1)
        ))
        
        # Add acknowledgment
        cursor.execute("""
            INSERT INTO violation_ack (
                violation_id, ack_by, ack_type, comment, ts
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            str(violation_2_id),
            'operator_john',
            'acknowledged',
            'Acknowledged - investigating cause',
            datetime.utcnow() - timedelta(minutes=30)
        ))
        
        print(f"   ✅ Created ACKNOWLEDGED violation: {violation_2_id}")
        print(f"      Station: ST22 | Profile: A&D | Severity: warning")
        print(f"      Acknowledged by: operator_john")
        
        # ============================================================================
        # Scenario 3: JUSTIFIED Pharma Violation (Temporary Deviation)
        # ============================================================================
        
        print("\n3️⃣  Creating JUSTIFIED violation (Pharma - Temporary Deviation)...")
        
        violation_3_id = uuid.uuid4()
        cursor.execute("""
            INSERT INTO violations (
                id, profile, plant, line, station,
                severity, requires_human_confirmation,
                violated_expectations, blocking_conditions, warnings,
                material_ref, snapshot_ref,
                ts_start
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb,
                %s::jsonb, %s::jsonb,
                %s
            )
        """, (
            str(violation_3_id),
            'Pharma Process Industries',
            'DEMO',
            'B01',
            'ST25',
            'critical',
            True,
            Json(['quality_hold_blocks_production']),
            Json(['material_quality_hold']),
            Json(['Material quality status is HOLD - production blocked']),
            Json({
                'evidence_present': True,
                'mode': 'lot',
                'active_lot': 'BATCH-2025-001',
                'quality_status': 'HOLD',
                'deviation_id': 'DEV-2025-042'
            }),
            Json({'timestamp': datetime.utcnow().isoformat()}),
            datetime.utcnow() - timedelta(hours=4)
        ))
        
        # Add justified acknowledgment
        cursor.execute("""
            INSERT INTO violation_ack (
                violation_id, ack_by, ack_type, comment, evidence_ref, ts
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            str(violation_3_id),
            'qa_manager_sarah',
            'justified',
            'Temporary hold for retest - deviation DEV-2025-042 approved by QA Manager. Expected resolution within 24h.',
            'DEV-2025-042',
            datetime.utcnow() - timedelta(hours=3, minutes=30)
        ))
        
        print(f"   ✅ Created JUSTIFIED violation: {violation_3_id}")
        print(f"      Station: ST25 | Profile: Pharma | Severity: critical")
        print(f"      Justified by: qa_manager_sarah")
        print(f"      Evidence: DEV-2025-042")
        
        # ============================================================================
        # Scenario 4: RESOLVED Historical Violation
        # ============================================================================
        
        print("\n4️⃣  Creating RESOLVED historical violation...")
        
        violation_4_id = uuid.uuid4()
        start_time = datetime.utcnow() - timedelta(days=1, hours=3)
        end_time = datetime.utcnow() - timedelta(days=1)
        
        cursor.execute("""
            INSERT INTO violations (
                id, profile, plant, line, station,
                severity, requires_human_confirmation,
                violated_expectations, blocking_conditions, warnings,
                material_ref, snapshot_ref,
                ts_start, ts_end
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb,
                %s::jsonb, %s::jsonb,
                %s, %s
            )
        """, (
            str(violation_4_id),
            'Aerospace & Defence',
            'DEMO',
            'A01',
            'ST19',
            'critical',
            True,
            Json(['missing_deviation_record']),
            Json(['missing_deviation_record']),
            Json(['Quality hold requires deviation record']),
            Json({
                'evidence_present': True,
                'mode': 'serial',
                'active_serial': 'SN-98765',
                'quality_status': 'HOLD',
                'deviation_id': None
            }),
            Json({'timestamp': start_time.isoformat()}),
            start_time,
            end_time
        ))
        
        # Add resolution acknowledgment
        cursor.execute("""
            INSERT INTO violation_ack (
                violation_id, ack_by, ack_type, comment, evidence_ref, ts
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            str(violation_4_id),
            'production_lead_mike',
            'resolved',
            'Deviation record DEV-2025-038 created and linked to work order. Material cleared for production.',
            'DEV-2025-038',
            end_time
        ))
        
        print(f"   ✅ Created RESOLVED violation: {violation_4_id}")
        print(f"      Station: ST19 | Profile: A&D | Severity: critical")
        print(f"      Resolved by: production_lead_mike")
        print(f"      Duration: 3 hours")
        
        # ============================================================================
        # Commit all changes
        # ============================================================================
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ Demo violations seeded successfully!")
        print("="*80)
        print("\nDemo Violations Summary:")
        print(f"1. OPEN         - {violation_1_id} (ST18 - Missing Serial)")
        print(f"2. ACKNOWLEDGED - {violation_2_id} (ST22 - Reduced Speed)")
        print(f"3. JUSTIFIED    - {violation_3_id} (ST25 - Quality Hold)")
        print(f"4. RESOLVED     - {violation_4_id} (ST19 - Historical)")
        
        print("\n📋 Test Commands:")
        print(f"\n# Get active violations:")
        print(f"curl http://localhost:8010/api/violations/active")
        
        print(f"\n# Get timeline for OPEN violation:")
        print(f"curl http://localhost:8010/api/violations/{violation_1_id}/timeline")
        
        print(f"\n# Acknowledge ST18 violation:")
        print(f"""curl -X POST http://localhost:8010/api/violations/{violation_1_id}/ack \\
  -H "Content-Type: application/json" \\
  -d '{{"ack_type":"acknowledged","ack_by":"demo_user","comment":"Investigating root cause"}}'""")
        
        print(f"\n# Get violation history:")
        print(f"curl http://localhost:8010/api/violations/history")
        
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding demo violations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    seed_demo_violations()
