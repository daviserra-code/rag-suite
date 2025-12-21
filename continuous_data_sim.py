"""
Continuous Data Simulator
Runs continuously to generate fresh OEE data every shift
"""
import os
import random
import time
import psycopg
from datetime import datetime, timedelta
from typing import Dict

# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

# Production Lines Configuration
LINES = {
    'A01': {'name': 'Assembly Line A01', 'base_oee': 0.83},
    'A02': {'name': 'Assembly Line A02', 'base_oee': 0.81},
    'B01': {'name': 'Battery Assembly Line B01', 'base_oee': 0.79},
    'B02': {'name': 'Battery Cell Testing B02', 'base_oee': 0.85},
    'C01': {'name': 'Component Line C01', 'base_oee': 0.88},
    'C03': {'name': 'Cable Harness Line C03', 'base_oee': 0.82},
    'D01': {'name': 'Final Drive Assembly D01', 'base_oee': 0.76},
    'M10': {'name': 'PCB Assembly Line M10', 'base_oee': 0.84},
    'M11': {'name': 'PCB Assembly Line M11', 'base_oee': 0.83},
    'SMT1': {'name': 'Sensor Module Line SMT1', 'base_oee': 0.87},
    'WC01': {'name': 'Wire Coil Line WC01', 'base_oee': 0.78}
}

SHIFTS = ['M', 'A', 'N']  # Morning, Afternoon, Night


def generate_shift_data(line_id: str, line_config: Dict, date: datetime.date, shift: str) -> Dict:
    """Generate realistic OEE data for a shift"""
    base_oee = line_config['base_oee']
    
    # Add randomness
    variation = random.uniform(-0.15, 0.15)
    oee = max(0.4, min(0.98, base_oee + variation))
    
    # Break down OEE into components
    availability = oee / random.uniform(0.85, 0.95)
    performance = oee / availability / random.uniform(0.88, 0.96)
    quality = oee / (availability * performance)
    
    # Clamp values
    availability = max(0.5, min(0.99, availability))
    performance = max(0.6, min(0.99, performance))
    quality = max(0.85, min(0.995, quality))
    
    # Calculate units
    theoretical_output = random.randint(800, 1200)
    total_units = int(theoretical_output * performance)
    good_units = int(total_units * quality)
    scrap_units = total_units - good_units
    
    # Downtime
    total_shift_minutes = 8 * 60
    planned_downtime = random.randint(15, 40)
    unplanned_downtime = int((1 - availability) * (total_shift_minutes - planned_downtime))
    runtime_minutes = total_shift_minutes - planned_downtime - unplanned_downtime
    
    return {
        'line_id': line_id,
        'line_name': line_config['name'],
        'date': date,
        'shift': shift,
        'oee': oee,
        'availability': availability,
        'performance': performance,
        'quality': quality,
        'total_units_produced': total_units,
        'good_units': good_units,
        'scrap_units': scrap_units,
        'theoretical_output': theoretical_output,
        'runtime_minutes': runtime_minutes,
        'planned_downtime_minutes': planned_downtime,
        'unplanned_downtime_minutes': unplanned_downtime,
        'total_shift_minutes': total_shift_minutes
    }


def upsert_shift_data(conn, data: Dict):
    """Insert or update shift data"""
    cur = conn.cursor()
    
    # Check if record exists
    cur.execute("""
        SELECT COUNT(*) FROM oee_line_shift 
        WHERE line_id = %s AND date = %s AND shift = %s
    """, (data['line_id'], data['date'], data['shift']))
    
    exists = cur.fetchone()[0] > 0
    
    if exists:
        # Update existing record
        cur.execute("""
            UPDATE oee_line_shift SET
                oee = %s,
                availability = %s,
                performance = %s,
                quality = %s,
                total_units_produced = %s,
                good_units = %s,
                scrap_units = %s,
                theoretical_output_units = %s,
                operating_time_min = %s,
                planned_time_min = 480,
                unplanned_downtime_min = %s
            WHERE line_id = %s AND date = %s AND shift = %s
        """, (
            data['oee'], data['availability'], data['performance'], data['quality'],
            data['total_units_produced'], data['good_units'], data['scrap_units'],
            data['theoretical_output'], data['runtime_minutes'],
            data['unplanned_downtime_minutes'],
            data['line_id'], data['date'], data['shift']
        ))
    else:
        # Insert new record
        cur.execute("""
            INSERT INTO oee_line_shift (
                line_id, line_name, date, shift,
                oee, availability, performance, quality,
                total_units_produced, good_units, scrap_units,
                theoretical_output_units, operating_time_min,
                planned_time_min, unplanned_downtime_min
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 480, %s
            )
        """, (
            data['line_id'], data['line_name'], data['date'], data['shift'],
            data['oee'], data['availability'], data['performance'], data['quality'],
            data['total_units_produced'], data['good_units'], data['scrap_units'],
            data['theoretical_output'], data['runtime_minutes'],
            data['unplanned_downtime_minutes']
        ))
    
    conn.commit()


def get_current_shift() -> str:
    """Determine current shift based on time"""
    hour = datetime.now().hour
    if 6 <= hour < 14:
        return 'M'  # Morning: 6am-2pm
    elif 14 <= hour < 22:
        return 'A'  # Afternoon: 2pm-10pm
    else:
        return 'N'  # Night: 10pm-6am


def simulate_continuous():
    """Run continuous simulation"""
    print("🚀 Starting continuous data simulator...")
    print(f"📊 Simulating {len(LINES)} production lines")
    print(f"🔄 Update interval: Every 5 minutes")
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            now = datetime.now()
            current_date = now.date()
            current_shift = get_current_shift()
            
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Iteration #{iteration}")
            print(f"📅 Date: {current_date}, Shift: {current_shift}")
            
            conn = psycopg.connect(DB_URL)
            
            # Generate data for current shift (all lines)
            for line_id, line_config in LINES.items():
                data = generate_shift_data(line_id, line_config, current_date, current_shift)
                upsert_shift_data(conn, data)
                print(f"  ✓ {line_id}: OEE={data['oee']:.1%}, A={data['availability']:.1%}, "
                      f"P={data['performance']:.1%}, Q={data['quality']:.1%}")
            
            conn.close()
            
            print(f"✅ Updated {len(LINES)} lines for {current_date} shift {current_shift}")
            
            # Sleep for 5 minutes
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n⚠️  Simulation stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    # Wait for database to be ready
    print("⏳ Waiting for database...")
    time.sleep(10)
    
    # Backfill last 2 days if needed
    print("🔄 Backfilling recent data...")
    try:
        conn = psycopg.connect(DB_URL)
        cur = conn.cursor()
        
        # Check if we have today's data
        cur.execute("""
            SELECT COUNT(*) FROM oee_line_shift 
            WHERE date >= CURRENT_DATE - INTERVAL '2 days'
        """)
        recent_count = cur.fetchone()[0]
        
        if recent_count < 10:
            print("📦 Generating last 2 days of data...")
            for days_ago in range(2, -1, -1):  # 2 days ago, 1 day ago, today
                date = (datetime.now() - timedelta(days=days_ago)).date()
                for shift in SHIFTS:
                    for line_id, line_config in LINES.items():
                        data = generate_shift_data(line_id, line_config, date, shift)
                        upsert_shift_data(conn, data)
            print(f"✅ Backfilled {len(LINES) * len(SHIFTS) * 3} records")
        else:
            print(f"✅ Recent data exists ({recent_count} records)")
        
        conn.close()
    except Exception as e:
        print(f"⚠️  Backfill error: {e}")
    
    # Start continuous simulation
    simulate_continuous()
