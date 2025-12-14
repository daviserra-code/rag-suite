"""
Generate Station-Level OEE Data
Populates oee_station_shift table with realistic station performance
"""
import os
import random
import psycopg
from datetime import datetime, timedelta
from typing import Dict, List

# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

# Station configurations per line type
STATION_CONFIGS = {
    'M10': [
        {'station_id': 'M10-S01', 'station_name': 'Component Pick & Place', 'base_oee': 0.88},
        {'station_id': 'M10-S02', 'station_name': 'PCB Assembly', 'base_oee': 0.82},
        {'station_id': 'M10-S03', 'station_name': 'Soldering Station', 'base_oee': 0.79},
        {'station_id': 'M10-S04', 'station_name': 'Quality Inspection', 'base_oee': 0.92},
        {'station_id': 'M10-S05', 'station_name': 'Final Assembly', 'base_oee': 0.85},
    ],
    'B02': [
        {'station_id': 'B02-S01', 'station_name': 'Cell Insertion', 'base_oee': 0.91},
        {'station_id': 'B02-S02', 'station_name': 'Welding Station', 'base_oee': 0.84},
        {'station_id': 'B02-S03', 'station_name': 'BMS Integration', 'base_oee': 0.87},
        {'station_id': 'B02-S04', 'station_name': 'Testing Station', 'base_oee': 0.93},
    ],
    'C03': [
        {'station_id': 'C03-S01', 'station_name': 'Component Prep', 'base_oee': 0.89},
        {'station_id': 'C03-S02', 'station_name': 'Assembly Robot 1', 'base_oee': 0.86},
        {'station_id': 'C03-S03', 'station_name': 'Assembly Robot 2', 'base_oee': 0.88},
        {'station_id': 'C03-S04', 'station_name': 'Quality Check', 'base_oee': 0.95},
    ],
    'D01': [
        {'station_id': 'D01-S01', 'station_name': 'Sub-Assembly Integration', 'base_oee': 0.83},
        {'station_id': 'D01-S02', 'station_name': 'Main Assembly', 'base_oee': 0.78},
        {'station_id': 'D01-S03', 'station_name': 'Functional Testing', 'base_oee': 0.88},
        {'station_id': 'D01-S04', 'station_name': 'Packaging', 'base_oee': 0.94},
    ],
    'SMT1': [
        {'station_id': 'SMT1-S01', 'station_name': 'Solder Paste Application', 'base_oee': 0.90},
        {'station_id': 'SMT1-S02', 'station_name': 'Pick & Place Machine 1', 'base_oee': 0.85},
        {'station_id': 'SMT1-S03', 'station_name': 'Pick & Place Machine 2', 'base_oee': 0.86},
        {'station_id': 'SMT1-S04', 'station_name': 'Reflow Oven', 'base_oee': 0.92},
        {'station_id': 'SMT1-S05', 'station_name': 'AOI Inspection', 'base_oee': 0.93},
    ],
    'WC01': [
        {'station_id': 'WC01-S01', 'station_name': 'Wire Feeder', 'base_oee': 0.84},
        {'station_id': 'WC01-S02', 'station_name': 'Cutting Station 1', 'base_oee': 0.80},
        {'station_id': 'WC01-S03', 'station_name': 'Cutting Station 2', 'base_oee': 0.82},
        {'station_id': 'WC01-S04', 'station_name': 'Terminal Crimping', 'base_oee': 0.88},
        {'station_id': 'WC01-S05', 'station_name': 'Quality Inspection', 'base_oee': 0.91},
    ]
}

STATION_ISSUES = [
    'Minor jam cleared',
    'Tool adjustment needed',
    'Sensor calibration',
    'Material feed issue',
    'Quality rejection spike',
    'Operator assistance required',
    'Cycle time deviation',
    None  # No issue
]


def generate_station_data(days: int = 90, start_date: datetime = None):
    """Generate station-level performance data based on line shifts"""
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    print(f"🏭 Generating Station-Level Data")
    print(f"📅 Period: {start_date.date()} to {(start_date + timedelta(days=days)).date()}")
    print(f"🔧 Total stations: {sum(len(stations) for stations in STATION_CONFIGS.values())}")
    print()
    
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    # Clear existing station data in date range
    print("🗑️  Clearing existing station data...")
    cur.execute("""
        DELETE FROM oee_station_shift 
        WHERE date >= %s AND date < %s
    """, (start_date.date(), (start_date + timedelta(days=days)).date()))
    conn.commit()
    print(f"✅ Cleared old station data\n")
    
    # Fetch line shift data to base stations on
    cur.execute("""
        SELECT date, shift, line_id, line_name, 
               availability, performance, quality, oee,
               total_units_produced, good_units, scrap_units,
               planned_time_min, unplanned_downtime_min, operating_time_min
        FROM oee_line_shift
        WHERE date >= %s AND date < %s
        ORDER BY date, shift, line_id
    """, (start_date.date(), (start_date + timedelta(days=days)).date()))
    
    line_shifts = cur.fetchall()
    print(f"📊 Processing {len(line_shifts)} line shifts...")
    
    station_records = []
    
    for line_shift in line_shifts:
        (date, shift, line_id, line_name, 
         line_avail, line_perf, line_qual, line_oee,
         line_total_units, line_good_units, line_scrap_units,
         line_planned_time, line_unplanned_dt, line_operating_time) = line_shift
        
        # Get stations for this line
        stations = STATION_CONFIGS.get(line_id, [])
        if not stations:
            continue
        
        # Distribute units across stations
        units_per_station = line_total_units // len(stations)
        good_per_station = line_good_units // len(stations)
        
        for station in stations:
            # Vary station performance around line average
            base_oee = station['base_oee']
            
            # Station OEE varies around its base, influenced by line performance
            station_oee = base_oee * random.uniform(0.92, 1.08)
            station_oee = max(0.50, min(0.99, station_oee))
            
            # Calculate station metrics
            station_avail = line_avail * random.uniform(0.95, 1.05)
            station_perf = line_perf * random.uniform(0.93, 1.07)
            station_qual = line_qual * random.uniform(0.97, 1.03)
            
            # Clamp values
            station_avail = max(0.60, min(0.99, station_avail))
            station_perf = max(0.65, min(0.98, station_perf))
            station_qual = max(0.85, min(0.995, station_qual))
            
            # Recalculate OEE from components
            station_oee = station_avail * station_perf * station_qual
            
            # Calculate station units (with some variation)
            station_total = int(units_per_station * random.uniform(0.95, 1.05))
            station_good = int(station_total * station_qual)
            station_scrap = station_total - station_good
            
            # Calculate times
            station_planned = line_planned_time
            station_unplanned_dt = station_planned * (1 - station_avail) * random.uniform(0.8, 1.2)
            station_operating = station_planned - station_unplanned_dt
            
            # Assign issue if OEE is below threshold
            main_issue = None
            if station_oee < 0.75:
                main_issue = random.choice([i for i in STATION_ISSUES if i is not None])
            elif random.random() < 0.2:  # 20% chance of minor issue
                main_issue = random.choice(STATION_ISSUES)
            
            station_records.append((
                date, shift, line_id, line_name,
                station['station_id'], station['station_name'],
                station_planned, station_unplanned_dt, station_operating,
                station_total, station_good, station_scrap,
                station_avail, station_perf, station_qual, station_oee,
                main_issue
            ))
    
    print(f"\n💾 Inserting {len(station_records)} station records...")
    cur.executemany("""
        INSERT INTO oee_station_shift (
            date, shift, line_id, line_name,
            station_id, station_name,
            planned_time_min, unplanned_downtime_min, operating_time_min,
            total_units_produced, good_units, scrap_units,
            availability, performance, quality, oee,
            main_issue
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, station_records)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ Station Data Generation Complete!")
    print(f"📊 Summary:")
    print(f"   • {len(station_records)} station-shift records generated")
    print(f"   • Average {len(station_records) / len(line_shifts):.1f} stations per line")
    
    # Calculate statistics
    total_stations = len(set(r[4] for r in station_records))
    avg_station_oee = sum(r[15] for r in station_records) / len(station_records) * 100
    
    print(f"\n📈 Station Statistics:")
    print(f"   • Total unique stations: {total_stations}")
    print(f"   • Average station OEE: {avg_station_oee:.2f}%")
    print(f"\n🎉 Station-level monitoring ready!")


if __name__ == "__main__":
    import sys
    
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    start_date = datetime.now() - timedelta(days=days)
    
    generate_station_data(days=days, start_date=start_date)
