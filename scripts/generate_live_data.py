#!/usr/bin/env python3
"""Generate live OEE data for current shift"""
import os, sys, random
from datetime import date, datetime
import psycopg

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "ragdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

LINES = [
    ("A01", "Assembly Line A01"), ("A02", "Assembly Line A02"),
    ("B01", "Battery Assembly Line B01"), ("C01", "Component Line C01"),
    ("M10", "PCB Assembly Line M10"), ("M11", "PCB Assembly Line M11"),
    ("D01", "Final Drive Assembly D01"), ("B02", "Battery Cell Testing B02"),
    ("C03", "Cable Harness Line C03"), ("SMT1", "Sensor Module Line SMT1"),
    ("WC01", "Wire Coil Line WC01")
]

def get_shift():
    h = datetime.now().hour
    return 'M' if 6 <= h < 14 else 'A' if 14 <= h < 22 else 'N'

try:
    conn = psycopg.connect(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    cur = conn.cursor()
    today, shift = date.today(), get_shift()
    print(f"Generating data for {today} shift {shift}")
    
    for line_id, line_name in LINES:
        avail, perf, qual = random.uniform(0.85, 0.95), random.uniform(0.85, 0.93), random.uniform(0.92, 0.98)
        oee = avail * perf * qual
        units = int(random.randint(400, 600) * perf)
        good = int(units * qual)
        
        cur.execute("""
            INSERT INTO oee_line_shift (date, shift, line_id, line_name, planned_time_min,
                unplanned_downtime_min, operating_time_min, ideal_cycle_time_sec,
                theoretical_output_units, total_units_produced, good_units, scrap_units,
                availability, performance, quality, oee, main_loss_category)
            VALUES (%s, %s, %s, %s, 480, %s, %s, 45, 500, %s, %s, %s, %s, %s, %s, %s, NULL)
            ON CONFLICT (date, shift, line_id) DO UPDATE SET
                total_units_produced=EXCLUDED.total_units_produced, good_units=EXCLUDED.good_units,
                scrap_units=EXCLUDED.scrap_units, oee=EXCLUDED.oee
        """, (today, shift, line_id, line_name, int(480*(1-avail)), int(480*avail),
              units, good, units-good, round(avail,4), round(perf,4), round(qual,4), round(oee,4)))
        
        for i in range(3):
            st_oee = random.uniform(0.65, 0.90)
            cur.execute("""
                INSERT INTO oee_station_shift (date, shift, line_id, line_name, station_id,
                    station_name, oee, availability, performance, quality, main_issue)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)
                ON CONFLICT (date, shift, line_id, station_id) DO UPDATE SET oee=EXCLUDED.oee
            """, (today, shift, line_id, line_name, f"{line_id}_ST0{i+1}", f"Station {i+1}",
                  round(st_oee,4), round(random.uniform(0.85,0.95),4),
                  round(random.uniform(0.80,0.92),4), round(random.uniform(0.90,0.98),4)))
    
    conn.commit()
    print(f"✅ Generated data for {len(LINES)} lines")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
