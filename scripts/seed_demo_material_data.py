"""
Seed Demo Material Data
Sprint 4 Extension - STEP 2

Seeds deterministic material evidence data for demo scenarios:
1. Aerospace & Defence: ST18 - no serial, no auth → BLOCKING
2. Pharma: Batch in HOLD, no deviation → BLOCKING
3. Automotive: Ramp-up, no material yet → OK

This script is REPEATABLE and IDEMPOTENT.
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def get_db_connection():
    """Get PostgreSQL connection"""
    connection_string = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/ragdb'
    )
    return psycopg2.connect(connection_string)


def clear_material_data(conn):
    """Clear existing material evidence data"""
    cursor = conn.cursor()
    
    print("Clearing existing material evidence data...")
    cursor.execute("DELETE FROM operator_certifications")
    cursor.execute("DELETE FROM tooling_status")
    cursor.execute("DELETE FROM material_authorizations")
    cursor.execute("DELETE FROM material_instances")
    
    conn.commit()
    cursor.close()
    print("✓ Cleared material evidence tables")


def seed_aerospace_defence_scenario(conn):
    """
    Seed A&D scenario: ST18 - Missing serial binding, no dry-run authorization
    
    Expected behavior with A&D profile:
    - BLOCKING: missing_serial_binding
    - BLOCKING: no dry_run_authorization for zero output
    - requires_human_confirmation = True
    """
    cursor = conn.cursor()
    
    print("\n=== Seeding Aerospace & Defence Scenario (ST18) ===")
    
    # ST18: NO material instance (missing serial binding)
    # This is intentional - the absence triggers blocking conditions
    
    # ST18: NO dry-run authorization
    # Intentionally not inserting authorization record
    
    # ST18: Tooling NOT calibrated
    cursor.execute("""
        INSERT INTO tooling_status 
        (tooling_id, station_id, calibration_ok, calibration_due_date, last_calibration_date, active, calibrated_by)
        VALUES 
        ('TOOL-ST18-001', 'ST18', false, %s, %s, true, 'system')
    """, (
        datetime.now().date() - timedelta(days=5),  # Overdue
        datetime.now().date() - timedelta(days=35)  # Last cal 35 days ago
    ))
    
    # ST18: Operator NOT certified (expired)
    cursor.execute("""
        INSERT INTO operator_certifications
        (operator_id, station_id, certified, certification_date, certification_expiry, active, certified_by)
        VALUES
        ('OP-12345', 'ST18', false, %s, %s, true, 'training_dept')
    """, (
        datetime.now().date() - timedelta(days=365),  # Certified a year ago
        datetime.now().date() - timedelta(days=30)    # Expired 30 days ago
    ))
    
    conn.commit()
    cursor.close()
    print("✓ ST18: No serial, no auth, no calibration, no cert → BLOCKING (A&D)")


def seed_pharma_scenario(conn):
    """
    Seed Pharma scenario: ST25 - Batch in HOLD, no deviation
    
    Expected behavior with Pharma profile:
    - BLOCKING: quality_status=HOLD without deviation_id
    - requires_human_confirmation = True
    """
    cursor = conn.cursor()
    
    print("\n=== Seeding Pharma Scenario (ST25) ===")
    
    # ST25: Material instance with HOLD status
    cursor.execute("""
        INSERT INTO material_instances
        (plant, line, station, mode, serial, lot, work_order, operation, 
         bom_revision, as_built_revision, quality_status, active)
        VALUES
        ('P001', 'L02', 'ST25', 'lot', NULL, 'LOT-2025-0042', 'WO-88123', 'OP20',
         'C', 'C', 'HOLD', true)
    """)
    
    # ST25: NO deviation (missing required evidence)
    cursor.execute("""
        INSERT INTO material_authorizations
        (station_id, dry_run_authorization, deviation_id, active, authorized_by, reason)
        VALUES
        ('ST25', false, NULL, true, NULL, NULL)
    """)
    
    # ST25: Tooling IS calibrated (OK)
    cursor.execute("""
        INSERT INTO tooling_status
        (tooling_id, station_id, calibration_ok, calibration_due_date, last_calibration_date, active, calibrated_by)
        VALUES
        ('TOOL-ST25-001', 'ST25', true, %s, %s, true, 'cal_lab')
    """, (
        datetime.now().date() + timedelta(days=60),  # Due in 60 days
        datetime.now().date() - timedelta(days=10)   # Calibrated 10 days ago
    ))
    
    # ST25: Operator IS certified (OK)
    cursor.execute("""
        INSERT INTO operator_certifications
        (operator_id, station_id, certified, certification_date, certification_expiry, active, certified_by)
        VALUES
        ('OP-67890', 'ST25', true, %s, %s, true, 'training_dept')
    """, (
        datetime.now().date() - timedelta(days=30),   # Certified 30 days ago
        datetime.now().date() + timedelta(days=335)   # Expires in 335 days
    ))
    
    conn.commit()
    cursor.close()
    print("✓ ST25: LOT-2025-0042 in HOLD, no deviation → BLOCKING (Pharma)")


def seed_automotive_scenario(conn):
    """
    Seed Automotive scenario: ST42 - Ramp-up, no material yet
    
    Expected behavior with Automotive profile:
    - NO BLOCKING: zero_output_allowed_during_startup = true
    - requires_human_confirmation = False
    """
    cursor = conn.cursor()
    
    print("\n=== Seeding Automotive Scenario (ST42) ===")
    
    # ST42: NO material instance (ramp-up, material not loaded yet)
    # This is acceptable for automotive during startup
    
    # ST42: NO authorization needed (automotive doesn't require it)
    
    # ST42: Tooling IS calibrated
    cursor.execute("""
        INSERT INTO tooling_status
        (tooling_id, station_id, calibration_ok, calibration_due_date, last_calibration_date, active, calibrated_by)
        VALUES
        ('TOOL-ST42-001', 'ST42', true, %s, %s, true, 'maint_team')
    """, (
        datetime.now().date() + timedelta(days=90),  # Due in 90 days
        datetime.now().date() - timedelta(days=5)    # Calibrated 5 days ago
    ))
    
    # ST42: Operator IS certified
    cursor.execute("""
        INSERT INTO operator_certifications
        (operator_id, station_id, certified, certification_date, certification_expiry, active, certified_by)
        VALUES
        ('OP-AUTO-123', 'ST42', true, %s, %s, true, 'hr_dept')
    """, (
        datetime.now().date() - timedelta(days=60),   # Certified 60 days ago
        datetime.now().date() + timedelta(days=305)   # Expires in 305 days
    ))
    
    conn.commit()
    cursor.close()
    print("✓ ST42: No material (ramp-up), tooling OK → NO BLOCKING (Automotive)")


def seed_normal_operation_scenario(conn):
    """
    Seed normal operation scenario: ST10 - Everything OK
    
    Expected behavior with any profile:
    - NO violations
    - NO blocking conditions
    """
    cursor = conn.cursor()
    
    print("\n=== Seeding Normal Operation Scenario (ST10) ===")
    
    # ST10: Material instance with RELEASED status
    cursor.execute("""
        INSERT INTO material_instances
        (plant, line, station, mode, serial, lot, work_order, operation,
         bom_revision, as_built_revision, quality_status, active)
        VALUES
        ('P001', 'A01', 'ST10', 'serial', 'SN-100234', NULL, 'WO-77812', 'OP40',
         'B', 'B', 'RELEASED', true)
    """)
    
    # ST10: Authorization present
    cursor.execute("""
        INSERT INTO material_authorizations
        (station_id, dry_run_authorization, deviation_id, active, authorized_by, reason)
        VALUES
        ('ST10', false, NULL, true, 'supervisor_01', 'normal_operation')
    """)
    
    # ST10: Tooling calibrated
    cursor.execute("""
        INSERT INTO tooling_status
        (tooling_id, station_id, calibration_ok, calibration_due_date, last_calibration_date, active, calibrated_by)
        VALUES
        ('TOOL-ST10-001', 'ST10', true, %s, %s, true, 'cal_lab')
    """, (
        datetime.now().date() + timedelta(days=45),
        datetime.now().date() - timedelta(days=15)
    ))
    
    # ST10: Operator certified
    cursor.execute("""
        INSERT INTO operator_certifications
        (operator_id, station_id, certified, certification_date, certification_expiry, active, certified_by)
        VALUES
        ('OP-CERTIFIED-001', 'ST10', true, %s, %s, true, 'training_dept')
    """, (
        datetime.now().date() - timedelta(days=90),
        datetime.now().date() + timedelta(days=275)
    ))
    
    conn.commit()
    cursor.close()
    print("✓ ST10: SN-100234, all evidence OK → NO VIOLATIONS")


def verify_seed_data(conn):
    """Verify seeded data"""
    cursor = conn.cursor()
    
    print("\n=== Verification ===")
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM material_instances")
    mat_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM material_authorizations")
    auth_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tooling_status")
    tool_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM operator_certifications")
    op_count = cursor.fetchone()[0]
    
    print(f"✓ Material instances: {mat_count}")
    print(f"✓ Authorizations: {auth_count}")
    print(f"✓ Tooling status: {tool_count}")
    print(f"✓ Operator certifications: {op_count}")
    
    # Show material evidence view
    print("\n=== Material Evidence View ===")
    cursor.execute("""
        SELECT station, mode, active_serial, active_lot, quality_status,
               dry_run_authorization, tooling_calibration_ok, operator_certified
        FROM v_material_evidence
        ORDER BY station
    """)
    
    for row in cursor.fetchall():
        station, mode, serial, lot, quality, dry_run, tooling, operator = row
        print(f"  {station}: mode={mode}, serial={serial}, lot={lot}, "
              f"quality={quality}, dry_run={dry_run}, tooling={tooling}, operator={operator}")
    
    cursor.close()


def main():
    """Main seeding function"""
    print("=" * 70)
    print("SEED DEMO MATERIAL DATA - Sprint 4 Extension STEP 2")
    print("=" * 70)
    
    try:
        conn = get_db_connection()
        print("✓ Connected to PostgreSQL")
        
        # Clear existing data
        clear_material_data(conn)
        
        # Seed scenarios
        seed_aerospace_defence_scenario(conn)
        seed_pharma_scenario(conn)
        seed_automotive_scenario(conn)
        seed_normal_operation_scenario(conn)
        
        # Verify
        verify_seed_data(conn)
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ MATERIAL DATA SEEDING COMPLETE")
        print("=" * 70)
        print("\nDemo scenarios ready:")
        print("  • ST18 (A&D): Missing serial → BLOCKING")
        print("  • ST25 (Pharma): HOLD without deviation → BLOCKING")
        print("  • ST42 (Automotive): Ramp-up → NO BLOCKING")
        print("  • ST10 (Normal): All OK → NO VIOLATIONS")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
