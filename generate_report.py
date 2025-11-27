"""
Automated Reporting System
Generates scheduled and on-demand reports for plant operations
"""
import os
import psycopg
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
sys.path.insert(0, '/app')

from packages.export_utils.pdf_export import export_to_pdf


DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")


def get_overall_kpis(start_date: datetime, end_date: datetime) -> Dict:
    """Get overall plant KPIs for the reporting period"""
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(DISTINCT line_id) as active_lines,
            COUNT(*) as total_shifts,
            AVG(oee) * 100 as avg_oee,
            AVG(availability) * 100 as avg_availability,
            AVG(performance) * 100 as avg_performance,
            AVG(quality) * 100 as avg_quality,
            SUM(total_units_produced) as total_units,
            SUM(good_units) as total_good_units,
            SUM(scrap_units) as total_scrap,
            AVG(unplanned_downtime_min) as avg_unplanned_downtime
        FROM oee_line_shift
        WHERE date >= %s AND date <= %s
    """, (start_date.date(), end_date.date()))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row:
        return {
            'active_lines': int(row[0]),
            'total_shifts': int(row[1]),
            'avg_oee': float(row[2] or 0),
            'avg_availability': float(row[3] or 0),
            'avg_performance': float(row[4] or 0),
            'avg_quality': float(row[5] or 0),
            'total_units': int(row[6] or 0),
            'total_good_units': int(row[7] or 0),
            'total_scrap': int(row[8] or 0),
            'avg_unplanned_downtime': float(row[9] or 0),
            'scrap_rate': (float(row[8] or 0) / float(row[6] or 1)) * 100
        }
    return {}


def get_line_performance(start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get performance breakdown by production line"""
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            line_id,
            line_name,
            AVG(oee) * 100 as avg_oee,
            AVG(availability) * 100 as avg_availability,
            AVG(performance) * 100 as avg_performance,
            AVG(quality) * 100 as avg_quality,
            SUM(total_units_produced) as total_units,
            SUM(good_units) as good_units,
            SUM(scrap_units) as scrap_units,
            COUNT(*) as shifts_worked
        FROM oee_line_shift
        WHERE date >= %s AND date <= %s
        GROUP BY line_id, line_name
        ORDER BY avg_oee DESC
    """, (start_date.date(), end_date.date()))
    
    lines = []
    for row in cur.fetchall():
        lines.append({
            'line_id': row[0],
            'line_name': row[1],
            'avg_oee': float(row[2] or 0),
            'avg_availability': float(row[3] or 0),
            'avg_performance': float(row[4] or 0),
            'avg_quality': float(row[5] or 0),
            'total_units': int(row[6] or 0),
            'good_units': int(row[7] or 0),
            'scrap_units': int(row[8] or 0),
            'shifts_worked': int(row[9] or 0),
            'scrap_rate': (float(row[8] or 0) / float(row[6] or 1)) * 100
        })
    
    cur.close()
    conn.close()
    return lines


def get_downtime_analysis(start_date: datetime, end_date: datetime) -> Dict:
    """Get downtime analysis by category"""
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            loss_category,
            COUNT(*) as event_count,
            SUM(duration_min) as total_duration,
            AVG(duration_min) as avg_duration
        FROM oee_downtime_events
        WHERE date >= %s AND date <= %s
        GROUP BY loss_category
        ORDER BY total_duration DESC
    """, (start_date.date(), end_date.date()))
    
    categories = []
    for row in cur.fetchall():
        categories.append({
            'category': row[0],
            'event_count': int(row[1]),
            'total_duration': float(row[2] or 0),
            'avg_duration': float(row[3] or 0)
        })
    
    cur.close()
    conn.close()
    return {'categories': categories}


def get_top_issues(start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict]:
    """Get top downtime issues by total duration"""
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            line_id,
            description,
            loss_category,
            COUNT(*) as occurrences,
            SUM(duration_min) as total_duration
        FROM oee_downtime_events
        WHERE date >= %s AND date <= %s
        GROUP BY line_id, description, loss_category
        ORDER BY total_duration DESC
        LIMIT %s
    """, (start_date.date(), end_date.date(), limit))
    
    issues = []
    for row in cur.fetchall():
        issues.append({
            'line_id': row[0],
            'description': row[1],
            'category': row[2],
            'occurrences': int(row[3]),
            'total_duration': float(row[4] or 0)
        })
    
    cur.close()
    conn.close()
    return issues


def get_shift_performance(start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get performance by shift (M/A/N)"""
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            shift,
            AVG(oee) * 100 as avg_oee,
            AVG(availability) * 100 as avg_availability,
            AVG(performance) * 100 as avg_performance,
            AVG(quality) * 100 as avg_quality,
            SUM(total_units_produced) as total_units,
            COUNT(*) as shift_count
        FROM oee_line_shift
        WHERE date >= %s AND date <= %s
        GROUP BY shift
        ORDER BY shift
    """, (start_date.date(), end_date.date()))
    
    shifts = []
    shift_names = {'M': 'Morning', 'A': 'Afternoon', 'N': 'Night'}
    for row in cur.fetchall():
        shifts.append({
            'shift': shift_names.get(row[0], row[0]),
            'avg_oee': float(row[1] or 0),
            'avg_availability': float(row[2] or 0),
            'avg_performance': float(row[3] or 0),
            'avg_quality': float(row[4] or 0),
            'total_units': int(row[5] or 0),
            'shift_count': int(row[6] or 0)
        })
    
    cur.close()
    conn.close()
    return shifts


def generate_executive_report(start_date: datetime, end_date: datetime, 
                              report_type: str = "weekly") -> bytes:
    """
    Generate executive summary report
    
    Args:
        start_date: Report start date
        end_date: Report end date
        report_type: "daily", "weekly", "monthly", "quarterly", "annual"
    """
    
    # Gather data
    kpis = get_overall_kpis(start_date, end_date)
    lines = get_line_performance(start_date, end_date)
    downtime = get_downtime_analysis(start_date, end_date)
    top_issues = get_top_issues(start_date, end_date, limit=10)
    shift_perf = get_shift_performance(start_date, end_date)
    
    # Build HTML report
    html_parts = []
    
    # Header
    html_parts.append(f"""
        <div style='text-align: center; margin-bottom: 40px;'>
            <h1 style='color: #0d9488; margin-bottom: 10px;'>Plant Operations Executive Report</h1>
            <h2 style='color: #666; font-weight: normal;'>{report_type.title()} Report</h2>
            <p style='color: #888; font-size: 14px;'>
                Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}
            </p>
            <p style='color: #888; font-size: 12px;'>
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    """)
    
    # Executive Summary - Key Metrics
    html_parts.append("""
        <h2 style='color: #0d9488; border-bottom: 2px solid #0d9488; padding-bottom: 10px; margin-top: 40px;'>
            Executive Summary
        </h2>
    """)
    
    html_parts.append(f"""
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 30px 0;'>
            <div style='background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%); padding: 20px; border-radius: 8px; color: white;'>
                <div style='font-size: 36px; font-weight: bold; margin-bottom: 5px;'>{kpis['avg_oee']:.1f}%</div>
                <div style='font-size: 14px; opacity: 0.9;'>Average OEE</div>
            </div>
            <div style='background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); padding: 20px; border-radius: 8px; color: white;'>
                <div style='font-size: 36px; font-weight: bold; margin-bottom: 5px;'>{kpis['total_units']:,}</div>
                <div style='font-size: 14px; opacity: 0.9;'>Units Produced</div>
            </div>
            <div style='background: linear-gradient(135deg, #10b981 0%, #34d399 100%); padding: 20px; border-radius: 8px; color: white;'>
                <div style='font-size: 36px; font-weight: bold; margin-bottom: 5px;'>{kpis['scrap_rate']:.2f}%</div>
                <div style='font-size: 14px; opacity: 0.9;'>Scrap Rate</div>
            </div>
            <div style='background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%); padding: 20px; border-radius: 8px; color: white;'>
                <div style='font-size: 36px; font-weight: bold; margin-bottom: 5px;'>{kpis['avg_unplanned_downtime']:.0f}</div>
                <div style='font-size: 14px; opacity: 0.9;'>Avg Downtime (min)</div>
            </div>
        </div>
    """)
    
    # OEE Components Breakdown
    html_parts.append(f"""
        <div style='background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;'>
            <h3 style='color: #374151; margin-top: 0;'>OEE Components</h3>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;'>
                <div>
                    <div style='color: #6b7280; font-size: 12px; margin-bottom: 5px;'>AVAILABILITY</div>
                    <div style='font-size: 24px; font-weight: bold; color: #0d9488;'>{kpis['avg_availability']:.1f}%</div>
                    <div style='height: 8px; background: #e5e7eb; border-radius: 4px; margin-top: 8px; overflow: hidden;'>
                        <div style='height: 100%; background: #0d9488; width: {kpis['avg_availability']:.0f}%;'></div>
                    </div>
                </div>
                <div>
                    <div style='color: #6b7280; font-size: 12px; margin-bottom: 5px;'>PERFORMANCE</div>
                    <div style='font-size: 24px; font-weight: bold; color: #3b82f6;'>{kpis['avg_performance']:.1f}%</div>
                    <div style='height: 8px; background: #e5e7eb; border-radius: 4px; margin-top: 8px; overflow: hidden;'>
                        <div style='height: 100%; background: #3b82f6; width: {kpis['avg_performance']:.0f}%;'></div>
                    </div>
                </div>
                <div>
                    <div style='color: #6b7280; font-size: 12px; margin-bottom: 5px;'>QUALITY</div>
                    <div style='font-size: 24px; font-weight: bold; color: #10b981;'>{kpis['avg_quality']:.1f}%</div>
                    <div style='height: 8px; background: #e5e7eb; border-radius: 4px; margin-top: 8px; overflow: hidden;'>
                        <div style='height: 100%; background: #10b981; width: {kpis['avg_quality']:.0f}%;'></div>
                    </div>
                </div>
            </div>
        </div>
    """)
    
    # Production Line Performance
    html_parts.append("""
        <h2 style='color: #0d9488; border-bottom: 2px solid #0d9488; padding-bottom: 10px; margin-top: 40px; page-break-before: always;'>
            Production Line Performance
        </h2>
    """)
    
    html_parts.append("""
        <table style='width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px;'>
            <thead>
                <tr style='background: #f3f4f6;'>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: left;'>Line</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>OEE</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Avail</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Perf</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Quality</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: right;'>Units</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: right;'>Good</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Scrap %</th>
                </tr>
            </thead>
            <tbody>
    """)
    
    for line in lines:
        oee_color = '#10b981' if line['avg_oee'] >= 75 else '#f59e0b' if line['avg_oee'] >= 65 else '#ef4444'
        html_parts.append(f"""
                <tr>
                    <td style='border: 1px solid #ddd; padding: 10px;'><strong>{line['line_id']}</strong> - {line['line_name']}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center; background: {oee_color}20; color: {oee_color}; font-weight: bold;'>{line['avg_oee']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{line['avg_availability']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{line['avg_performance']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{line['avg_quality']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: right;'>{line['total_units']:,}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: right;'>{line['good_units']:,}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{line['scrap_rate']:.2f}%</td>
                </tr>
        """)
    
    html_parts.append("</tbody></table>")
    
    # Downtime Analysis
    html_parts.append("""
        <h2 style='color: #0d9488; border-bottom: 2px solid #0d9488; padding-bottom: 10px; margin-top: 40px;'>
            Downtime Analysis
        </h2>
    """)
    
    html_parts.append("""
        <table style='width: 100%; border-collapse: collapse; margin-top: 20px;'>
            <thead>
                <tr style='background: #f3f4f6;'>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: left;'>Category</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Events</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: right;'>Total Duration (hrs)</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: right;'>Avg Duration (min)</th>
                </tr>
            </thead>
            <tbody>
    """)
    
    for cat in downtime['categories']:
        html_parts.append(f"""
                <tr>
                    <td style='border: 1px solid #ddd; padding: 10px;'><strong>{cat['category']}</strong></td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{cat['event_count']}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: right;'>{cat['total_duration'] / 60:.1f}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: right;'>{cat['avg_duration']:.1f}</td>
                </tr>
        """)
    
    html_parts.append("</tbody></table>")
    
    # Top Issues
    html_parts.append("""
        <h2 style='color: #0d9488; border-bottom: 2px solid #0d9488; padding-bottom: 10px; margin-top: 40px; page-break-before: always;'>
            Top 10 Downtime Issues
        </h2>
    """)
    
    html_parts.append("""
        <table style='width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px;'>
            <thead>
                <tr style='background: #f3f4f6;'>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: left;'>Line</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: left;'>Issue Description</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Category</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Occurrences</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: right;'>Total Duration (hrs)</th>
                </tr>
            </thead>
            <tbody>
    """)
    
    for idx, issue in enumerate(top_issues, 1):
        bg_color = '#fef2f2' if idx <= 3 else ''
        html_parts.append(f"""
                <tr style='background: {bg_color};'>
                    <td style='border: 1px solid #ddd; padding: 10px;'><strong>{issue['line_id']}</strong></td>
                    <td style='border: 1px solid #ddd; padding: 10px;'>{issue['description']}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{issue['category']}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{issue['occurrences']}</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: right;'>{issue['total_duration'] / 60:.1f}</td>
                </tr>
        """)
    
    html_parts.append("</tbody></table>")
    
    # Shift Performance
    html_parts.append("""
        <h2 style='color: #0d9488; border-bottom: 2px solid #0d9488; padding-bottom: 10px; margin-top: 40px;'>
            Shift Performance Comparison
        </h2>
    """)
    
    html_parts.append("""
        <table style='width: 100%; border-collapse: collapse; margin-top: 20px;'>
            <thead>
                <tr style='background: #f3f4f6;'>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: left;'>Shift</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>OEE</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Availability</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Performance</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: center;'>Quality</th>
                    <th style='border: 1px solid #ddd; padding: 10px; text-align: right;'>Units Produced</th>
                </tr>
            </thead>
            <tbody>
    """)
    
    for shift in shift_perf:
        html_parts.append(f"""
                <tr>
                    <td style='border: 1px solid #ddd; padding: 10px;'><strong>{shift['shift']}</strong></td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{shift['avg_oee']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{shift['avg_availability']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{shift['avg_performance']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{shift['avg_quality']:.1f}%</td>
                    <td style='border: 1px solid #ddd; padding: 10px; text-align: right;'>{shift['total_units']:,}</td>
                </tr>
        """)
    
    html_parts.append("</tbody></table>")
    
    # Footer
    html_parts.append("""
        <div style='margin-top: 60px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #888; font-size: 11px;'>
            <p>This report is automatically generated by the Shopfloor Copilot system.</p>
            <p>For questions or clarifications, please contact the Production Management team.</p>
        </div>
    """)
    
    html_content = ''.join(html_parts)
    
    # Generate PDF
    return export_to_pdf(
        title=f"{report_type.title()} Operations Report",
        content_html=html_content
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate plant operations reports')
    parser.add_argument('--type', choices=['daily', 'weekly', 'monthly', 'quarterly', 'annual'], 
                       default='weekly', help='Report type')
    parser.add_argument('--days', type=int, help='Number of days to include (overrides type)')
    parser.add_argument('--output', default='report.pdf', help='Output filename')
    
    args = parser.parse_args()
    
    # Calculate date range
    end_date = datetime.now()
    
    if args.days:
        start_date = end_date - timedelta(days=args.days)
        report_type = f"{args.days}-day"
    else:
        type_days = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'annual': 365
        }
        days = type_days[args.type]
        start_date = end_date - timedelta(days=days)
        report_type = args.type
    
    print(f"📊 Generating {report_type} report...")
    print(f"📅 Period: {start_date.date()} to {end_date.date()}")
    
    pdf_bytes = generate_executive_report(start_date, end_date, report_type)
    
    # Save report
    with open(args.output, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"✅ Report saved to: {args.output}")
    print(f"📄 File size: {len(pdf_bytes) / 1024:.1f} KB")
