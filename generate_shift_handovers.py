"""
Generate Shift Handover Reports
Automated end-of-shift summaries with issues and notes
"""
import os
import psycopg
from datetime import datetime, timedelta
import random


# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

SHIFT_NAMES = {'M': 'Morning', 'A': 'Afternoon', 'N': 'Night'}

ISSUE_TYPES = [
    'Equipment Malfunction',
    'Quality Issue',
    'Material Shortage',
    'Tool Change Required',
    'Sensor Calibration',
    'Safety Concern',
    'Process Deviation',
    'Maintenance Required'
]

SAMPLE_NOTES = [
    "Station 2 running slightly slower than normal - monitoring required",
    "New operator on line - performance may be affected",
    "Preventive maintenance scheduled for next shift",
    "Quality checks passed all inspections",
    "Tool wear noticed - replacement recommended within 2 days",
    "Material batch changed midway through shift",
    "Production target achieved ahead of schedule",
    "Minor adjustments made to fixture alignment",
    "Temperature sensors reading within normal range",
    "Shift changeover completed smoothly"
]


def generate_shift_handovers(days: int = 7, start_date: datetime = None):
    """Generate automated shift handover reports from historical data"""
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    print(f"📋 Generating Shift Handover Reports")
    print(f"📅 Period: {start_date.date()} to {(start_date + timedelta(days=days)).date()}")
    print("=" * 70)
    
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    # Get shift data to generate handovers from
    cur.execute("""
        SELECT 
            date, shift, line_id, line_name,
            SUM(total_units_produced) as total_units,
            AVG(oee) as avg_oee,
            SUM(unplanned_downtime_min) as total_downtime,
            COUNT(CASE WHEN main_issue IS NOT NULL THEN 1 END) as issue_count
        FROM oee_station_shift
        WHERE date >= %s AND date < %s
        GROUP BY date, shift, line_id, line_name
        ORDER BY date DESC, shift, line_id
    """, (start_date.date(), (start_date + timedelta(days=days)).date()))
    
    shift_data = cur.fetchall()
    
    print(f"📊 Processing {len(shift_data)} shift records...\n")
    
    # Clear existing handovers for date range
    cur.execute("""
        DELETE FROM shift_handovers 
        WHERE shift_date >= %s AND shift_date < %s
    """, (start_date.date(), (start_date + timedelta(days=days)).date()))
    conn.commit()
    
    handovers = []
    issues = []
    notes = []
    
    handover_counter = 1000
    issue_counter = 5000
    
    for shift_record in shift_data:
        (date, shift, line_id, line_name, 
         total_units, avg_oee, total_downtime, issue_count) = shift_record
        
        handover_id = f"HO{date.strftime('%Y%m%d')}{shift}{line_id}"
        
        # Generate summary
        shift_name = SHIFT_NAMES.get(shift, shift)
        oee_pct = avg_oee * 100
        
        if oee_pct >= 85:
            performance_desc = "excellent performance"
        elif oee_pct >= 75:
            performance_desc = "good performance with some optimization opportunities"
        elif oee_pct >= 65:
            performance_desc = "moderate performance, attention needed"
        else:
            performance_desc = "below target performance, immediate action required"
        
        summary = f"{shift_name} shift for {line_name} completed with {performance_desc}. "
        summary += f"Produced {total_units} units with {oee_pct:.1f}% OEE. "
        
        if total_downtime > 60:
            summary += f"Experienced {total_downtime:.0f} minutes of unplanned downtime. "
        
        if issue_count > 5:
            summary += f"Multiple issues reported ({issue_count} stations affected). "
        elif issue_count > 0:
            summary += f"Minor issues on {issue_count} station(s). "
        else:
            summary += "No major issues reported. "
        
        # Determine status and who created it
        status = 'submitted' if random.random() > 0.2 else 'draft'
        created_by = random.choice(['Operator A', 'Operator B', 'Shift Lead', 'Supervisor'])
        
        handovers.append((
            handover_id, date, shift, line_id,
            created_by, summary, total_units, avg_oee,
            issue_count, total_downtime, status,
            datetime.combine(date, datetime.min.time()) + timedelta(hours=6 if shift == 'M' else (14 if shift == 'A' else 22)),
            datetime.combine(date, datetime.min.time()) + timedelta(hours=14 if shift == 'M' else (22 if shift == 'A' else 6), days=1 if shift == 'N' else 0) if status == 'submitted' else None
        ))
        
        # Generate issues for this shift (if there were problems)
        if issue_count > 0 and random.random() > 0.3:
            num_issues = min(issue_count, random.randint(1, 3))
            
            for i in range(num_issues):
                issue_id = f"ISS{issue_counter:05d}"
                issue_counter += 1
                
                issue_type = random.choice(ISSUE_TYPES)
                severity = random.choice(['low', 'medium', 'high', 'critical'])
                
                # Generate issue description
                descriptions = {
                    'Equipment Malfunction': f"Equipment on {line_id} experienced intermittent failures",
                    'Quality Issue': f"Quality deviation detected in production batch",
                    'Material Shortage': f"Material supply ran low during shift",
                    'Tool Change Required': f"Cutting tool showing signs of wear",
                    'Sensor Calibration': f"Sensor readings drifting from baseline",
                    'Safety Concern': f"Safety interlock triggered twice during shift",
                    'Process Deviation': f"Process parameters outside normal range",
                    'Maintenance Required': f"Equipment requires scheduled maintenance"
                }
                
                description = descriptions.get(issue_type, "Issue reported during shift")
                
                # Generate resolution if resolved
                status_val = 'resolved' if random.random() > 0.4 else 'open'
                resolution = None
                resolved_by = None
                resolved_at = None
                
                if status_val == 'resolved':
                    resolutions = [
                        "Technician adjusted settings and verified operation",
                        "Replacement part installed and tested",
                        "Root cause identified and corrective action taken",
                        "Maintenance team completed repairs",
                        "Process parameters reset to standard values",
                        "Issue escalated to engineering team for permanent fix"
                    ]
                    resolution = random.choice(resolutions)
                    resolved_by = random.choice(['Tech Team', 'Maintenance', 'Engineering', 'Shift Lead'])
                    resolved_at = datetime.combine(date, datetime.min.time()) + timedelta(hours=random.randint(8, 23))
                
                issues.append((
                    issue_id, handover_id, line_id, None,
                    issue_type, severity, description,
                    None, resolution, status_val,
                    created_by, resolved_by,
                    datetime.combine(date, datetime.min.time()) + timedelta(hours=random.randint(6, 23)),
                    resolved_at
                ))
        
        # Generate notes (2-3 per shift)
        num_notes = random.randint(2, 3)
        for i in range(num_notes):
            note_type = random.choice(['observation', 'action_taken', 'follow_up', 'general'])
            note_text = random.choice(SAMPLE_NOTES)
            
            notes.append((
                handover_id, note_type, note_text, created_by,
                datetime.combine(date, datetime.min.time()) + timedelta(hours=random.randint(6, 23))
            ))
    
    # Insert data
    print(f"💾 Inserting {len(handovers)} shift handover reports...")
    cur.executemany("""
        INSERT INTO shift_handovers (
            handover_id, shift_date, shift, line_id,
            created_by, summary, total_production, oee_achieved,
            major_issues, downtime_minutes, status,
            created_at, submitted_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, handovers)
    
    print(f"💾 Inserting {len(issues)} shift issues...")
    cur.executemany("""
        INSERT INTO shift_issues (
            issue_id, handover_id, line_id, station_id,
            issue_type, severity, description,
            root_cause, resolution, status,
            reported_by, resolved_by, reported_at, resolved_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, issues)
    
    print(f"💾 Inserting {len(notes)} shift notes...")
    cur.executemany("""
        INSERT INTO shift_notes (
            handover_id, note_type, note_text,
            created_by, created_at
        ) VALUES (%s, %s, %s, %s, %s)
    """, notes)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ Shift Handover Reports Generated!")
    print(f"📊 Summary:")
    print(f"   • Handover reports: {len(handovers)}")
    print(f"   • Issues documented: {len(issues)}")
    print(f"   • Shift notes: {len(notes)}")
    
    # Count by status
    submitted = len([h for h in handovers if h[10] == 'submitted'])
    draft = len([h for h in handovers if h[10] == 'draft'])
    
    print(f"\n📋 Report Status:")
    print(f"   • Submitted: {submitted}")
    print(f"   • Draft: {draft}")
    
    open_issues = len([i for i in issues if i[9] == 'open'])
    resolved_issues = len([i for i in issues if i[9] == 'resolved'])
    
    print(f"\n🔧 Issues Status:")
    print(f"   • Open: {open_issues}")
    print(f"   • Resolved: {resolved_issues}")
    
    print("\n🎉 Shift handover system ready!")


if __name__ == "__main__":
    import sys
    
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    start_date = datetime.now() - timedelta(days=days)
    
    generate_shift_handovers(days=days, start_date=start_date)
