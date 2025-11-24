"""
Mock MES Database Schema and Seed Data
Creates tables and populates with sample data for A01 line pilot
"""

CREATE_SCHEMA_SQL = """
-- KPI OEE Metrics
CREATE TABLE IF NOT EXISTS kpi_oee (
    id SERIAL PRIMARY KEY,
    line VARCHAR(10) NOT NULL,
    shift_date DATE NOT NULL,
    shift VARCHAR(10) NOT NULL,
    availability DECIMAL(5,2) NOT NULL,
    performance DECIMAL(5,2) NOT NULL,
    quality DECIMAL(5,2) NOT NULL,
    oee DECIMAL(5,2) NOT NULL,
    planned_production_time INTEGER NOT NULL,
    actual_runtime INTEGER NOT NULL,
    ideal_cycle_time DECIMAL(10,2) NOT NULL,
    total_pieces INTEGER NOT NULL,
    good_pieces INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kpi_oee_line_date ON kpi_oee(line, shift_date DESC);

-- KPI FPY Metrics
CREATE TABLE IF NOT EXISTS kpi_fpy (
    id SERIAL PRIMARY KEY,
    line VARCHAR(10) NOT NULL,
    shift_date DATE NOT NULL,
    shift VARCHAR(10) NOT NULL,
    total_units INTEGER NOT NULL,
    first_pass_units INTEGER NOT NULL,
    fpy DECIMAL(5,2) NOT NULL,
    defect_count INTEGER NOT NULL,
    rework_count INTEGER NOT NULL,
    scrap_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kpi_fpy_line_date ON kpi_fpy(line, shift_date DESC);

-- KPI MTTR Metrics
CREATE TABLE IF NOT EXISTS kpi_mttr (
    id SERIAL PRIMARY KEY,
    line VARCHAR(10) NOT NULL,
    shift_date DATE NOT NULL,
    shift VARCHAR(10) NOT NULL,
    total_downtime_minutes INTEGER NOT NULL,
    failure_count INTEGER NOT NULL,
    mttr_minutes DECIMAL(10,2) NOT NULL,
    longest_downtime_minutes INTEGER NOT NULL,
    shortest_downtime_minutes INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kpi_mttr_line_date ON kpi_mttr(line, shift_date DESC);

-- Downtime Events
CREATE TABLE IF NOT EXISTS downtime_events (
    id SERIAL PRIMARY KEY,
    line VARCHAR(10) NOT NULL,
    station VARCHAR(10),
    event_start TIMESTAMP NOT NULL,
    event_end TIMESTAMP,
    duration_minutes INTEGER,
    reason_code VARCHAR(20),
    reason_description TEXT,
    operator_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_downtime_line_start ON downtime_events(line, event_start DESC);
"""

SEED_DATA_SQL = """
-- Seed OEE data for Line A01 (last 14 days, 3 shifts per day)
INSERT INTO kpi_oee (line, shift_date, shift, availability, performance, quality, oee, 
                     planned_production_time, actual_runtime, ideal_cycle_time, total_pieces, good_pieces)
VALUES
    ('A01', CURRENT_DATE - 1, 'T1', 85.5, 92.3, 96.8, 76.4, 480, 410, 2.5, 4200, 4066),
    ('A01', CURRENT_DATE - 1, 'T2', 88.2, 89.7, 95.2, 75.3, 480, 423, 2.5, 4150, 3951),
    ('A01', CURRENT_DATE - 1, 'T3', 82.1, 91.5, 97.1, 72.9, 480, 394, 2.5, 4080, 3962),
    ('A01', CURRENT_DATE - 2, 'T1', 90.2, 94.1, 96.5, 81.9, 480, 433, 2.5, 4350, 4198),
    ('A01', CURRENT_DATE - 2, 'T2', 87.5, 88.9, 94.8, 73.7, 480, 420, 2.5, 4100, 3887),
    ('A01', CURRENT_DATE - 2, 'T3', 84.3, 90.2, 96.1, 73.1, 480, 405, 2.5, 4150, 3988),
    ('A01', CURRENT_DATE - 3, 'T1', 86.7, 93.5, 97.2, 78.8, 480, 416, 2.5, 4280, 4160),
    ('A01', CURRENT_DATE - 3, 'T2', 89.1, 91.8, 95.5, 78.1, 480, 428, 2.5, 4220, 4030),
    ('A01', CURRENT_DATE - 3, 'T3', 83.5, 89.4, 96.8, 72.3, 480, 401, 2.5, 4050, 3920),
    ('A01', CURRENT_DATE - 4, 'T1', 91.5, 95.2, 97.8, 85.2, 480, 439, 2.5, 4450, 4352),
    ('A01', CURRENT_DATE - 4, 'T2', 88.9, 92.6, 96.2, 79.2, 480, 427, 2.5, 4300, 4137),
    ('A01', CURRENT_DATE - 4, 'T3', 85.2, 90.8, 95.9, 74.2, 480, 409, 2.5, 4180, 4009),
    ('A01', CURRENT_DATE - 5, 'T1', 87.3, 91.2, 96.5, 76.8, 480, 419, 2.5, 4250, 4101),
    ('A01', CURRENT_DATE - 5, 'T2', 84.1, 88.5, 94.7, 70.5, 480, 404, 2.5, 4050, 3835),
    ('A01', CURRENT_DATE - 5, 'T3', 86.5, 92.8, 97.1, 77.9, 480, 415, 2.5, 4300, 4175);

-- Seed FPY data for Line A01
INSERT INTO kpi_fpy (line, shift_date, shift, total_units, first_pass_units, fpy, 
                     defect_count, rework_count, scrap_count)
VALUES
    ('A01', CURRENT_DATE - 1, 'T1', 4200, 4066, 96.8, 98, 36, 0),
    ('A01', CURRENT_DATE - 1, 'T2', 4150, 3951, 95.2, 165, 34, 0),
    ('A01', CURRENT_DATE - 1, 'T3', 4080, 3962, 97.1, 92, 26, 0),
    ('A01', CURRENT_DATE - 2, 'T1', 4350, 4198, 96.5, 124, 28, 0),
    ('A01', CURRENT_DATE - 2, 'T2', 4100, 3887, 94.8, 186, 27, 0),
    ('A01', CURRENT_DATE - 2, 'T3', 4150, 3988, 96.1, 139, 23, 0),
    ('A01', CURRENT_DATE - 3, 'T1', 4280, 4160, 97.2, 96, 24, 0),
    ('A01', CURRENT_DATE - 3, 'T2', 4220, 4030, 95.5, 163, 27, 0),
    ('A01', CURRENT_DATE - 3, 'T3', 4050, 3920, 96.8, 110, 20, 0),
    ('A01', CURRENT_DATE - 4, 'T1', 4450, 4352, 97.8, 78, 20, 0),
    ('A01', CURRENT_DATE - 4, 'T2', 4300, 4137, 96.2, 140, 23, 0),
    ('A01', CURRENT_DATE - 4, 'T3', 4180, 4009, 95.9, 148, 23, 0),
    ('A01', CURRENT_DATE - 5, 'T1', 4250, 4101, 96.5, 127, 22, 0),
    ('A01', CURRENT_DATE - 5, 'T2', 4050, 3835, 94.7, 188, 27, 0),
    ('A01', CURRENT_DATE - 5, 'T3', 4300, 4175, 97.1, 102, 23, 0);

-- Seed MTTR data for Line A01
INSERT INTO kpi_mttr (line, shift_date, shift, total_downtime_minutes, failure_count, 
                      mttr_minutes, longest_downtime_minutes, shortest_downtime_minutes)
VALUES
    ('A01', CURRENT_DATE - 1, 'T1', 70, 4, 17.5, 32, 8),
    ('A01', CURRENT_DATE - 1, 'T2', 57, 3, 19.0, 28, 12),
    ('A01', CURRENT_DATE - 1, 'T3', 86, 5, 17.2, 35, 6),
    ('A01', CURRENT_DATE - 2, 'T1', 47, 3, 15.7, 22, 10),
    ('A01', CURRENT_DATE - 2, 'T2', 60, 4, 15.0, 25, 8),
    ('A01', CURRENT_DATE - 2, 'T3', 75, 4, 18.8, 38, 9),
    ('A01', CURRENT_DATE - 3, 'T1', 64, 4, 16.0, 30, 7),
    ('A01', CURRENT_DATE - 3, 'T2', 52, 3, 17.3, 26, 11),
    ('A01', CURRENT_DATE - 3, 'T3', 79, 5, 15.8, 32, 8),
    ('A01', CURRENT_DATE - 4, 'T1', 41, 2, 20.5, 26, 15),
    ('A01', CURRENT_DATE - 4, 'T2', 53, 3, 17.7, 28, 10),
    ('A01', CURRENT_DATE - 4, 'T3', 71, 4, 17.8, 34, 9),
    ('A01', CURRENT_DATE - 5, 'T1', 61, 4, 15.3, 27, 8),
    ('A01', CURRENT_DATE - 5, 'T2', 76, 5, 15.2, 30, 7),
    ('A01', CURRENT_DATE - 5, 'T3', 65, 4, 16.3, 29, 9);

-- Seed downtime events for Line A01 (last 3 days)
INSERT INTO downtime_events (line, station, event_start, event_end, duration_minutes, 
                             reason_code, reason_description, operator_notes)
VALUES
    ('A01', 'S110', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour 28 minutes', 32, 'MECH_FAIL', 'Conveyor belt misalignment', 'Adjusted tension, tested OK'),
    ('A01', 'S120', CURRENT_TIMESTAMP - INTERVAL '5 hours', CURRENT_TIMESTAMP - INTERVAL '4 hours 48 minutes', 12, 'TOOL_CHANGE', 'Scheduled tool replacement', 'Routine maintenance'),
    ('A01', 'S110', CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_TIMESTAMP - INTERVAL '1 day' + INTERVAL '28 minutes', 28, 'MATERIAL', 'Material shortage - waiting for parts', 'Logistics delay'),
    ('A01', 'S130', CURRENT_TIMESTAMP - INTERVAL '1 day 6 hours', CURRENT_TIMESTAMP - INTERVAL '1 day 5 hours 45 minutes', 15, 'QUALITY', 'Quality check failure - dimensions out of spec', 'Calibrated measuring equipment'),
    ('A01', 'S110', CURRENT_TIMESTAMP - INTERVAL '2 days', CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '35 minutes', 35, 'ELEC_FAIL', 'Sensor malfunction', 'Replaced proximity sensor'),
    ('A01', 'S120', CURRENT_TIMESTAMP - INTERVAL '2 days 4 hours', CURRENT_TIMESTAMP - INTERVAL '2 days 3 hours 54 minutes', 6, 'SETUP', 'Product changeover', 'Standard changeover procedure'),
    ('A01', 'S140', CURRENT_TIMESTAMP - INTERVAL '2 days 8 hours', CURRENT_TIMESTAMP - INTERVAL '2 days 7 hours 32 minutes', 28, 'MECH_FAIL', 'Pneumatic cylinder leak', 'Replaced seals'),
    ('A01', 'S110', CURRENT_TIMESTAMP - INTERVAL '3 days', CURRENT_TIMESTAMP - INTERVAL '3 days' + INTERVAL '22 minutes', 22, 'SOFTWARE', 'PLC communication error', 'Reset PLC, checked network'),
    ('A01', 'S130', CURRENT_TIMESTAMP - INTERVAL '3 days 5 hours', CURRENT_TIMESTAMP - INTERVAL '3 days 4 hours 50 minutes', 10, 'TOOL_CHANGE', 'Cutting tool replacement', 'Routine wear replacement');
"""

def init_mes_database():
    """Initialize MES database with schema and seed data"""
    import psycopg
    import os
    
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ragdb")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    conn_str = f"host={host} port={port} dbname={db} user={user} password={password}"
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                # Create schema
                print("Creating MES tables...")
                cur.execute(CREATE_SCHEMA_SQL)
                
                # Insert seed data
                print("Inserting seed data...")
                cur.execute(SEED_DATA_SQL)
                
                conn.commit()
                print("✅ MES database initialized successfully!")
                
                # Verify
                cur.execute("SELECT COUNT(*) FROM kpi_oee")
                oee_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM downtime_events")
                dt_count = cur.fetchone()[0]
                
                print(f"   - OEE records: {oee_count}")
                print(f"   - Downtime events: {dt_count}")
                
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    init_mes_database()
