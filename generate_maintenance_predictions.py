"""
Predictive Maintenance Alert Generator
Analyzes historical downtime data to predict equipment failures and generate alerts
"""
import os
import psycopg
from datetime import datetime, timedelta
from collections import defaultdict
import random


# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")

# Equipment types by station with typical MTBF (Mean Time Between Failures in hours)
EQUIPMENT_MAP = {
    'M10-S01': {'equipment': 'Pick & Place Robot', 'mtbf_base': 720},
    'M10-S02': {'equipment': 'PCB Assembly Machine', 'mtbf_base': 650},
    'M10-S03': {'equipment': 'Soldering System', 'mtbf_base': 580},
    'M10-S04': {'equipment': 'Vision Inspection Camera', 'mtbf_base': 800},
    'M10-S05': {'equipment': 'Assembly Robot', 'mtbf_base': 700},
    'B02-S01': {'equipment': 'Cell Insertion Robot', 'mtbf_base': 750},
    'B02-S02': {'equipment': 'Spot Welder', 'mtbf_base': 550},
    'B02-S03': {'equipment': 'BMS Controller', 'mtbf_base': 900},
    'B02-S04': {'equipment': 'Battery Tester', 'mtbf_base': 850},
    'C03-S01': {'equipment': 'Component Feeder', 'mtbf_base': 680},
    'C03-S02': {'equipment': 'Assembly Robot A1', 'mtbf_base': 720},
    'C03-S03': {'equipment': 'Assembly Robot A2', 'mtbf_base': 720},
    'C03-S04': {'equipment': 'Quality Scanner', 'mtbf_base': 880},
    'D01-S01': {'equipment': 'Integration Fixture', 'mtbf_base': 620},
    'D01-S02': {'equipment': 'Main Assembly Press', 'mtbf_base': 590},
    'D01-S03': {'equipment': 'Test Equipment', 'mtbf_base': 780},
    'D01-S04': {'equipment': 'Packaging Machine', 'mtbf_base': 820},
    'SMT1-S01': {'equipment': 'Solder Paste Printer', 'mtbf_base': 640},
    'SMT1-S02': {'equipment': 'Pick & Place M1', 'mtbf_base': 700},
    'SMT1-S03': {'equipment': 'Pick & Place M2', 'mtbf_base': 700},
    'SMT1-S04': {'equipment': 'Reflow Oven', 'mtbf_base': 760},
    'SMT1-S05': {'equipment': 'AOI System', 'mtbf_base': 850},
    'WC01-S01': {'equipment': 'Wire Feed System', 'mtbf_base': 580},
    'WC01-S02': {'equipment': 'Cutting Machine C1', 'mtbf_base': 520},
    'WC01-S03': {'equipment': 'Cutting Machine C2', 'mtbf_base': 520},
    'WC01-S04': {'equipment': 'Crimping Press', 'mtbf_base': 610},
    'WC01-S05': {'equipment': 'Quality Tester', 'mtbf_base': 800},
}


def analyze_downtime_patterns():
    """Analyze historical downtime to identify patterns and predict failures"""
    
    print("🔍 Analyzing Downtime Patterns for Predictive Maintenance")
    print("=" * 70)
    
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    # Get downtime events from last 90 days grouped by line and analyze per station
    cur.execute("""
        SELECT 
            ols.line_id,
            ols.line_name,
            ols.station_id,
            ols.station_name,
            COUNT(DISTINCT ols.date || ols.shift) as total_shifts,
            AVG(ols.oee) as avg_oee,
            AVG(ols.availability) as avg_availability,
            SUM(ols.unplanned_downtime_min) as total_downtime_min,
            COUNT(CASE WHEN ols.main_issue IS NOT NULL THEN 1 END) as issue_count,
            MAX(ols.date) as last_issue_date
        FROM oee_station_shift ols
        WHERE ols.date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY ols.line_id, ols.line_name, ols.station_id, ols.station_name
        HAVING AVG(ols.oee) < 0.80 OR SUM(ols.unplanned_downtime_min) > 500
        ORDER BY avg_oee ASC, total_downtime_min DESC
    """)
    
    station_failures = cur.fetchall()
    
    print(f"📊 Found {len(station_failures)} stations with significant failure patterns\n")
    
    # Calculate health scores and generate alerts
    alerts = []
    health_scores = []
    alert_id_counter = 1000
    
    for station in station_failures:
        (line_id, line_name, station_id, station_name, 
         total_shifts, avg_oee, avg_availability, total_downtime, issue_count, last_issue_date) = station
        
        # Estimate failure count from issues and downtime
        failure_count = max(3, int(issue_count * 0.3))  # Assume 30% of issues are failures
        
        # Get equipment info
        equipment_info = EQUIPMENT_MAP.get(station_id, {'equipment': f'{station_name} Equipment', 'mtbf_base': 700})
        equipment_name = equipment_info['equipment']
        mtbf_base = equipment_info['mtbf_base']
        
        # Calculate metrics
        days_since_failure = (datetime.now().date() - last_issue_date).days if last_issue_date else 90
        last_failure = last_issue_date
        
        # Calculate MTBF (Mean Time Between Failures)
        mtbf_actual = (90 * 24) / failure_count if failure_count > 0 else mtbf_base
        
        # Health score (0-100): based on MTBF ratio, failure frequency, and time since last failure
        mtbf_ratio = min(mtbf_actual / mtbf_base, 1.5)
        frequency_factor = max(0, 1 - (failure_count / 30))  # Normalize to 30 failures max
        recency_factor = min(days_since_failure / 30, 1.0)   # Normalize to 30 days
        
        health_score = (mtbf_ratio * 0.4 + frequency_factor * 0.4 + recency_factor * 0.2) * 100
        health_score = max(0, min(100, health_score))
        
        # Failure probability (next 30 days)
        failure_probability = 1 - (health_score / 100)
        
        # Determine if alert should be generated
        generate_alert = False
        severity = None
        alert_type = None
        predicted_days = None
        
        if health_score < 50:
            generate_alert = True
            severity = 'critical'
            alert_type = 'imminent_failure'
            predicted_days = 3 + int(health_score / 10)
        elif health_score < 65:
            generate_alert = True
            severity = 'high'
            alert_type = 'degrading_performance'
            predicted_days = 7 + int(health_score / 5)
        elif health_score < 75:
            generate_alert = True
            severity = 'medium'
            alert_type = 'maintenance_due'
            predicted_days = 14 + int(health_score / 3)
        elif failure_count > 10:
            generate_alert = True
            severity = 'low'
            alert_type = 'high_failure_rate'
            predicted_days = 21
        
        # Store health score
        health_scores.append((
            line_id, station_id, equipment_name,
            health_score, mtbf_actual, failure_probability,
            last_failure, failure_count,
            datetime.now()
        ))
        
        # Generate alert if needed
        if generate_alert:
            alert_id = f"MA{alert_id_counter:05d}"
            alert_id_counter += 1
            
            predicted_failure_date = datetime.now().date() + timedelta(days=predicted_days)
            confidence = min(95, 50 + (100 - health_score) * 0.5)
            
            # Determine pattern and recommendation
            pattern = f"Detected {failure_count} failures in 90 days. " \
                     f"Total downtime: {total_downtime:.1f} min. " \
                     f"Average OEE: {avg_oee*100:.1f}%. Issues reported: {issue_count}"
            
            recommendations = {
                'imminent_failure': f"URGENT: Schedule immediate inspection of {equipment_name}. Replace worn components.",
                'degrading_performance': f"Plan maintenance within 7 days for {equipment_name}. Check for wear patterns.",
                'maintenance_due': f"Schedule preventive maintenance for {equipment_name} within 2 weeks.",
                'high_failure_rate': f"Review operating procedures for {equipment_name}. Consider root cause analysis."
            }
            
            recommended_action = recommendations.get(alert_type, "Schedule inspection")
            
            alerts.append((
                alert_id, line_id, station_id, equipment_name,
                alert_type, severity, predicted_failure_date,
                confidence, pattern, recommended_action,
                'active', datetime.now()
            ))
            
            print(f"⚠️  Alert {alert_id}: {severity.upper()} - {line_id}/{station_name}")
            print(f"   Equipment: {equipment_name}")
            print(f"   Health Score: {health_score:.1f}%")
            print(f"   Predicted Issue: {predicted_days} days ({predicted_failure_date})")
            print(f"   Confidence: {confidence:.1f}%")
            print()
    
    # Clear old alerts (keep last 30 days only)
    print("\n🗑️  Clearing old alerts...")
    cur.execute("""
        DELETE FROM maintenance_alerts 
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
    """)
    
    cur.execute("""
        DELETE FROM equipment_health_score 
        WHERE calculated_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
    """)
    conn.commit()
    
    # Insert new health scores
    print(f"\n💾 Inserting {len(health_scores)} equipment health scores...")
    cur.executemany("""
        INSERT INTO equipment_health_score (
            line_id, station_id, equipment_name,
            health_score, mtbf_hours, failure_probability,
            last_failure_date, cycles_since_maintenance, calculated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, health_scores)
    
    # Insert new alerts
    print(f"💾 Inserting {len(alerts)} maintenance alerts...")
    cur.executemany("""
        INSERT INTO maintenance_alerts (
            alert_id, line_id, station_id, equipment_name,
            alert_type, severity, predicted_failure_date,
            confidence_score, pattern_detected, recommended_action,
            current_status, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (alert_id) DO NOTHING
    """, alerts)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ Predictive Maintenance Analysis Complete!")
    print(f"📊 Summary:")
    print(f"   • Equipment analyzed: {len(health_scores)}")
    print(f"   • Alerts generated: {len(alerts)}")
    
    # Count by severity
    severity_counts = defaultdict(int)
    for alert in alerts:
        severity_counts[alert[5]] += 1
    
    print(f"\n🚨 Alerts by Severity:")
    for severity in ['critical', 'high', 'medium', 'low']:
        if severity_counts[severity] > 0:
            print(f"   • {severity.upper()}: {severity_counts[severity]}")
    
    if health_scores:
        print(f"\n🎯 Average Equipment Health: {sum(hs[3] for hs in health_scores) / len(health_scores):.1f}%")
    print("🎉 Predictive maintenance system ready!")


if __name__ == "__main__":
    analyze_downtime_patterns()
