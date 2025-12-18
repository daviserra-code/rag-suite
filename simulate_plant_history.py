"""
Realistic Plant Data Simulator
Generates OEE history with realistic patterns for manufacturing lines
"""
import os
import random
import psycopg
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

# Production Lines Configuration (aligned with plant_model.json)
LINES = {
    # TORINO Plant Lines
    'A01': {
        'name': 'Assembly Line A01',
        'ideal_cycle_time': 45.0,  # seconds per unit
        'theoretical_output': 960,  # units per shift (8 hours)
        'base_availability': 0.90,
        'base_performance': 0.88,
        'base_quality': 0.93,
        'downtime_prone': 0.15
    },
    'A02': {
        'name': 'Assembly Line A02',
        'ideal_cycle_time': 45.0,
        'theoretical_output': 960,
        'base_availability': 0.89,
        'base_performance': 0.87,
        'base_quality': 0.92,
        'downtime_prone': 0.16
    },
    'B01': {
        'name': 'Battery Assembly Line B01',
        'ideal_cycle_time': 52.0,
        'theoretical_output': 830,
        'base_availability': 0.87,
        'base_performance': 0.85,
        'base_quality': 0.94,
        'downtime_prone': 0.18
    },
    'C01': {
        'name': 'Component Line C01',
        'ideal_cycle_time': 36.0,
        'theoretical_output': 1200,
        'base_availability': 0.92,
        'base_performance': 0.90,
        'base_quality': 0.91,
        'downtime_prone': 0.12
    },
    # MILAN Plant Lines
    'M10': {
        'name': 'PCB Assembly Line M10',
        'ideal_cycle_time': 31.0,
        'theoretical_output': 1400,
        'base_availability': 0.93,
        'base_performance': 0.91,
        'base_quality': 0.96,
        'downtime_prone': 0.10
    },
    'M11': {
        'name': 'PCB Assembly Line M11',
        'ideal_cycle_time': 31.0,
        'theoretical_output': 1400,
        'base_availability': 0.92,
        'base_performance': 0.90,
        'base_quality': 0.95,
        'downtime_prone': 0.11
    },
    'D01': {
        'name': 'Final Drive Assembly D01',
        'ideal_cycle_time': 60.0,
        'theoretical_output': 720,
        'base_availability': 0.88,
        'base_performance': 0.86,
        'base_quality': 0.97,
        'downtime_prone': 0.17
    },
    # ROME Plant Lines
    'B02': {
        'name': 'Battery Cell Testing B02',
        'ideal_cycle_time': 18.0,
        'theoretical_output': 2400,
        'base_availability': 0.95,
        'base_performance': 0.94,
        'base_quality': 0.98,
        'downtime_prone': 0.08
    },
    'C03': {
        'name': 'Cable Harness Line C03',
        'ideal_cycle_time': 24.0,
        'theoretical_output': 1800,
        'base_availability': 0.91,
        'base_performance': 0.89,
        'base_quality': 0.93,
        'downtime_prone': 0.13
    },
    'SMT1': {
        'name': 'Sensor Module Line SMT1',
        'ideal_cycle_time': 14.0,
        'theoretical_output': 3200,
        'base_availability': 0.94,
        'base_performance': 0.92,
        'base_quality': 0.97,
        'downtime_prone': 0.09
    },
    'WC01': {
        'name': 'Wire Coil Line WC01',
        'ideal_cycle_time': 48.0,
        'theoretical_output': 900,
        'base_availability': 0.89,
        'base_performance': 0.87,
        'base_quality': 0.95,
        'downtime_prone': 0.16
    }
}

# Downtime Categories with realistic durations (minutes)
DOWNTIME_TYPES = [
    ('Changeover', (15, 45), 'Planned'),
    ('Minor Stop', (2, 10), 'Unplanned'),
    ('Reduced Speed', (5, 30), 'Performance'),
    ('Quality Rework', (10, 25), 'Quality'),
    ('Equipment Failure', (30, 120), 'Unplanned'),
    ('Material Shortage', (20, 60), 'Unplanned'),
    ('Planned Maintenance', (45, 90), 'Planned'),
    ('Tooling Change', (15, 35), 'Planned'),
    ('Adjustment', (5, 15), 'Performance'),
    ('Emergency Stop', (10, 40), 'Safety')
]

# Shift patterns
SHIFTS = ['M', 'A', 'N']  # Morning, Afternoon, Night
SHIFT_HOURS = {'M': (6, 14), 'A': (14, 22), 'N': (22, 6)}


def calculate_shift_performance(line_config: Dict, shift: str, day_of_week: int) -> Dict:
    """Calculate realistic shift performance with variations"""
    
    # Base metrics
    availability = line_config['base_availability']
    performance = line_config['base_performance']
    quality = line_config['base_quality']
    
    # Shift variations (night shift typically lower)
    if shift == 'N':
        availability *= random.uniform(0.92, 0.98)
        performance *= random.uniform(0.94, 0.99)
        quality *= random.uniform(0.96, 1.00)
    elif shift == 'A':
        availability *= random.uniform(0.96, 1.02)
        performance *= random.uniform(0.98, 1.03)
        quality *= random.uniform(0.98, 1.01)
    else:  # Morning shift - typically best
        availability *= random.uniform(0.98, 1.04)
        performance *= random.uniform(1.00, 1.05)
        quality *= random.uniform(0.99, 1.02)
    
    # Day of week variations (Monday ramp-up, Friday fatigue)
    if day_of_week == 0:  # Monday
        availability *= random.uniform(0.92, 0.97)
        performance *= random.uniform(0.94, 0.98)
    elif day_of_week == 4:  # Friday
        availability *= random.uniform(0.95, 0.99)
        performance *= random.uniform(0.96, 1.00)
    
    # Random variations (simulate real-world unpredictability)
    availability *= random.uniform(0.95, 1.05)
    performance *= random.uniform(0.96, 1.04)
    quality *= random.uniform(0.97, 1.02)
    
    # Clamp values to realistic ranges
    availability = max(0.60, min(0.99, availability))
    performance = max(0.65, min(0.98, performance))
    quality = max(0.85, min(0.995, quality))
    
    # Calculate OEE
    oee = availability * performance * quality
    
    # Calculate units produced
    theoretical = line_config['theoretical_output']
    total_units = int(theoretical * performance * availability)
    good_units = int(total_units * quality)
    scrap_units = total_units - good_units
    
    # Calculate times (8 hour shift = 480 minutes)
    planned_time = 480
    unplanned_downtime = planned_time * (1 - availability) * random.uniform(0.7, 1.3)
    operating_time = planned_time - unplanned_downtime
    
    return {
        'availability': availability,
        'performance': performance,
        'quality': quality,
        'oee': oee,
        'total_units': total_units,
        'good_units': good_units,
        'scrap_units': scrap_units,
        'planned_time_min': planned_time,
        'unplanned_downtime_min': unplanned_downtime,
        'operating_time_min': operating_time,
        'theoretical_output': theoretical
    }


def generate_downtime_events(line_id: str, line_config: Dict, date: datetime, 
                             shift: str, availability: float) -> List[Dict]:
    """Generate realistic downtime events for a shift"""
    events = []
    
    # Number of events based on availability (lower availability = more events)
    num_events = random.choices(
        [0, 1, 2, 3, 4],
        weights=[
            max(0, availability - 0.7) * 100,  # High availability = fewer events
            30,
            20,
            10,
            5
        ]
    )[0]
    
    shift_start, shift_end = SHIFT_HOURS[shift]
    current_time = date.replace(hour=shift_start, minute=0, second=0)
    
    for _ in range(num_events):
        # Select downtime type
        downtime_type, duration_range, category = random.choice(DOWNTIME_TYPES)
        
        # Adjust probability for line-specific downtime proneness
        if random.random() > line_config['downtime_prone']:
            # Less prone to downtime - shorter duration
            duration = random.uniform(duration_range[0], (duration_range[0] + duration_range[1]) / 2)
        else:
            # More prone - full range
            duration = random.uniform(duration_range[0], duration_range[1])
        
        # Random time within shift (avoid exact start/end)
        hour_offset = random.uniform(0.5, 7.5)
        event_time = current_time + timedelta(hours=hour_offset)
        
        events.append({
            'line_id': line_id,
            'line_name': line_config['name'],
            'date': date.date(),
            'shift': shift,
            'start_timestamp': event_time,
            'duration_min': duration,
            'loss_category': category,
            'description': f"{downtime_type} on {line_id} during shift {shift}"
        })
    
    return events


def main_loss_category(availability: float, performance: float, quality: float) -> str:
    """Determine main loss category based on metrics"""
    losses = {
        'Availability Loss': 1 - availability,
        'Performance Loss': 1 - performance,
        'Quality Loss': 1 - quality
    }
    return max(losses, key=losses.get)


def simulate_plant_history(days: int = 90, start_date: datetime = None):
    """
    Simulate realistic plant operation history
    
    Args:
        days: Number of days to simulate (default 90 for 3 months)
        start_date: Starting date (default: 90 days before today)
    """
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    print(f"🏭 Starting Plant Simulation")
    print(f"📅 Period: {start_date.date()} to {(start_date + timedelta(days=days)).date()}")
    print(f"🔧 Lines: {len(LINES)}")
    print(f"⚙️  Generating {days} days × 3 shifts × {len(LINES)} lines = {days * 3 * len(LINES)} shift records")
    print()
    
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    # Clear existing data in date range
    print("🗑️  Clearing existing data in date range...")
    cur.execute("""
        DELETE FROM oee_downtime_events 
        WHERE date >= %s AND date < %s
    """, (start_date.date(), (start_date + timedelta(days=days)).date()))
    
    cur.execute("""
        DELETE FROM oee_line_shift 
        WHERE date >= %s AND date < %s
    """, (start_date.date(), (start_date + timedelta(days=days)).date()))
    
    conn.commit()
    print(f"✅ Cleared old data\n")
    
    # Get next available event_id
    cur.execute("SELECT COALESCE(MAX(event_id), 0) + 1 FROM oee_downtime_events")
    event_id = cur.fetchone()[0]
    print(f"📝 Starting event_id: {event_id}\n")
    
    shift_records = []
    downtime_events = []
    
    # Generate data
    print("⚙️  Generating shift data...")
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        day_of_week = current_date.weekday()
        
        if day % 10 == 0:
            print(f"   Day {day + 1}/{days} - {current_date.date()}")
        
        for shift in SHIFTS:
            for line_id, line_config in LINES.items():
                # Calculate shift performance
                perf = calculate_shift_performance(line_config, shift, day_of_week)
                
                # Generate shift record
                shift_records.append((
                    current_date.date(),
                    shift,
                    line_id,
                    line_config['name'],
                    perf['planned_time_min'],
                    perf['unplanned_downtime_min'],
                    perf['operating_time_min'],
                    line_config['ideal_cycle_time'],
                    perf['theoretical_output'],
                    perf['total_units'],
                    perf['good_units'],
                    perf['scrap_units'],
                    perf['availability'],
                    perf['performance'],
                    perf['quality'],
                    perf['oee'],
                    main_loss_category(perf['availability'], perf['performance'], perf['quality'])
                ))
                
                # Generate downtime events
                events = generate_downtime_events(
                    line_id, line_config, current_date, shift, perf['availability']
                )
                
                for event in events:
                    downtime_events.append((
                        event_id,
                        event['line_id'],
                        event['line_name'],
                        event['date'],
                        event['shift'],
                        event['start_timestamp'],
                        event['duration_min'],
                        event['loss_category'],
                        event['description']
                    ))
                    event_id += 1
    
    print(f"\n💾 Inserting {len(shift_records)} shift records...")
    cur.executemany("""
        INSERT INTO oee_line_shift (
            date, shift, line_id, line_name,
            planned_time_min, unplanned_downtime_min, operating_time_min,
            ideal_cycle_time_sec, theoretical_output_units,
            total_units_produced, good_units, scrap_units,
            availability, performance, quality, oee, main_loss_category
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, shift_records)
    
    print(f"💾 Inserting {len(downtime_events)} downtime events...")
    cur.executemany("""
        INSERT INTO oee_downtime_events (
            event_id, line_id, line_name, date, shift,
            start_timestamp, duration_min, loss_category, description
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, downtime_events)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ Simulation Complete!")
    print(f"📊 Summary:")
    print(f"   • {len(shift_records)} shift records generated")
    print(f"   • {len(downtime_events)} downtime events generated")
    print(f"   • Average {len(downtime_events) / len(shift_records):.2f} events per shift")
    
    # Calculate and display overall statistics
    total_units = sum(r[9] for r in shift_records)
    total_good = sum(r[10] for r in shift_records)
    avg_oee = sum(r[15] for r in shift_records) / len(shift_records) * 100
    
    print(f"\n📈 Overall Statistics:")
    print(f"   • Total units produced: {total_units:,}")
    print(f"   • Total good units: {total_good:,}")
    print(f"   • Overall scrap rate: {((total_units - total_good) / total_units * 100):.2f}%")
    print(f"   • Average OEE: {avg_oee:.2f}%")
    print(f"\n🎉 Plant history simulation ready for Siemens presentation!")


if __name__ == "__main__":
    import sys
    
    # Allow command-line arguments for customization
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    
    # Start from 90 days ago to current date
    start_date = datetime.now() - timedelta(days=days)
    
    simulate_plant_history(days=days, start_date=start_date)
