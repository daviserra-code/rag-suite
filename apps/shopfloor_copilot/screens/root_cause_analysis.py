"""
Root Cause Analysis Tool
Pareto charts for defect analysis and correlation between downtime events
"""
from nicegui import ui
from datetime import datetime, timedelta
from sqlalchemy import text
from collections import defaultdict
import math

from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine


def root_cause_analysis_screen():
    """Root cause analysis dashboard with Pareto charts and correlation analysis"""
    
    engine = get_db_engine()
    
    with ui.column().classes('w-full p-4 gap-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Root Cause Analysis').classes('text-3xl font-bold')
            ui.button('Refresh', icon='refresh', on_click=lambda: load_analysis())
        
        # Filters
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full gap-4 items-end'):
                days_filter = ui.select(
                    [7, 14, 30, 60, 90],
                    label='Time Period (days)',
                    value=30
                ).classes('w-48').style('background: white;')
                
                with engine.connect() as conn:
                    lines = [row[0] for row in conn.execute(
                        text("SELECT DISTINCT line_id FROM oee_line_shift ORDER BY line_id")
                    ).fetchall()]
                
                line_filter = ui.select(
                    ['All'] + lines,
                    label='Production Line',
                    value='All'
                ).classes('w-48').style('background: white;')
                
                ui.button('Analyze', icon='analytics', on_click=lambda: load_analysis())
        
        # Analysis containers
        pareto_container = ui.column().classes('w-full gap-4')
        correlation_container = ui.column().classes('w-full gap-4')
        insights_container = ui.column().classes('w-full gap-4')
        
        def load_analysis():
            """Load and display root cause analysis"""
            pareto_container.clear()
            correlation_container.clear()
            insights_container.clear()
            
            with engine.connect() as conn:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days_filter.value)
                
                # Build filters
                params = {'start_date': start_date, 'end_date': end_date}
                
                line_filter_sql = ""
                line_filter_sql_sh = ""
                line_filter_sql_d1 = ""
                
                if line_filter.value != 'All':
                    line_filter_sql = "AND line_id = :line_id"
                    line_filter_sql_sh = "AND sh.line_id = :line_id"
                    line_filter_sql_d1 = "AND d1.line_id = :line_id"
                    params['line_id'] = line_filter.value
                
                # Get downtime events by loss category
                downtime_by_issue = conn.execute(text(f"""
                    SELECT 
                        COALESCE(loss_category, 'Unclassified') as issue_type,
                        COUNT(*) as frequency,
                        SUM(duration_min) as total_downtime,
                        ROUND(AVG(duration_min)::numeric, 1) as avg_duration,
                        COUNT(DISTINCT line_id) as lines_affected
                    FROM oee_downtime_events
                    WHERE date >= :start_date AND date <= :end_date {line_filter_sql}
                    GROUP BY loss_category
                    ORDER BY total_downtime DESC
                """), params).fetchall()
                
                # Get shift issues by type
                shift_issues = conn.execute(text(f"""
                    SELECT 
                        si.issue_type,
                        si.severity,
                        COUNT(*) as frequency,
                        COUNT(CASE WHEN si.status = 'open' THEN 1 END) as open_count,
                        COUNT(CASE WHEN si.status = 'resolved' THEN 1 END) as resolved_count
                    FROM shift_issues si
                    JOIN shift_handovers sh ON si.handover_id = sh.handover_id
                    WHERE sh.shift_date >= :start_date AND sh.shift_date <= :end_date {line_filter_sql_sh}
                    GROUP BY si.issue_type, si.severity
                    ORDER BY frequency DESC
                """), params).fetchall()
                
                # Get correlations between issues (using loss_category from downtime events)
                issue_correlations = conn.execute(text(f"""
                    WITH issue_pairs AS (
                        SELECT 
                            d1.date,
                            d1.line_id,
                            COALESCE(d1.loss_category, 'Unclassified') as issue1,
                            COALESCE(d2.loss_category, 'Unclassified') as issue2,
                            ABS(EXTRACT(EPOCH FROM (d1.start_timestamp - d2.start_timestamp))/3600) as hours_apart
                        FROM oee_downtime_events d1
                        JOIN oee_downtime_events d2 
                            ON d1.date = d2.date 
                            AND d1.line_id = d2.line_id
                            AND d1.event_id < d2.event_id
                        WHERE d1.date >= :start_date AND d1.date <= :end_date {line_filter_sql_d1}
                            AND d1.loss_category IS NOT NULL 
                            AND d2.loss_category IS NOT NULL
                            AND ABS(EXTRACT(EPOCH FROM (d1.start_timestamp - d2.start_timestamp))/3600) < 24
                    )
                    SELECT 
                        issue1,
                        issue2,
                        COUNT(*) as co_occurrence,
                        ROUND(AVG(hours_apart)::numeric, 1) as avg_hours_apart
                    FROM issue_pairs
                    WHERE issue1 != issue2
                    GROUP BY issue1, issue2
                    HAVING COUNT(*) >= 3
                    ORDER BY co_occurrence DESC
                    LIMIT 20
                """), params).fetchall()
                
                # Display Pareto Chart for Downtime Issues
                with pareto_container:
                    ui.label('Pareto Analysis - Downtime by Issue Type').classes('text-2xl font-bold mb-4')
                    
                    if downtime_by_issue:
                        create_pareto_chart(downtime_by_issue, 'downtime')
                    else:
                        ui.label('No downtime data available for selected period').classes('text-gray-500')
                
                # Display Pareto Chart for Shift Issues
                with pareto_container:
                    ui.label('Pareto Analysis - Shift Issues by Type').classes('text-2xl font-bold mt-6 mb-4')
                    
                    if shift_issues:
                        create_shift_issues_chart(shift_issues)
                    else:
                        ui.label('No shift issue data available for selected period').classes('text-gray-500')
                
                # Display Correlation Analysis
                with correlation_container:
                    ui.label('Issue Correlation Analysis').classes('text-2xl font-bold mb-4')
                    
                    if issue_correlations:
                        create_correlation_matrix(issue_correlations)
                    else:
                        ui.label('No significant correlations found').classes('text-gray-500')
                
                # Display Insights
                with insights_container:
                    generate_insights(downtime_by_issue, shift_issues, issue_correlations)
        
        def create_pareto_chart(data, chart_type):
            """Create Pareto chart visualization"""
            if not data:
                return
            
            total_downtime = sum(row[2] for row in data)
            cumulative_pct = 0
            
            with ui.card().classes('w-full p-4'):
                # Chart header
                with ui.row().classes('w-full mb-4'):
                    ui.label(f'Total Downtime: {total_downtime:.0f} minutes').classes('text-lg font-semibold')
                    ui.label(f'Issue Types: {len(data)}').classes('text-sm text-gray-600 ml-4')
                
                # Pareto bars
                for idx, row in enumerate(data):
                    issue, frequency, downtime, avg_duration, lines_affected = row
                    pct = (downtime / total_downtime) * 100
                    cumulative_pct += pct
                    
                    # Color coding based on cumulative percentage (80/20 rule)
                    if cumulative_pct <= 80:
                        bar_color = 'bg-red-500'
                        badge_color = 'red'
                        priority = 'HIGH PRIORITY'
                    elif cumulative_pct <= 95:
                        bar_color = 'bg-orange-500'
                        badge_color = 'orange'
                        priority = 'MEDIUM'
                    else:
                        bar_color = 'bg-blue-500'
                        badge_color = 'blue'
                        priority = 'LOW'
                    
                    with ui.card().classes('w-full p-3 mb-2'):
                        with ui.row().classes('w-full items-center justify-between mb-2'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label(f'{idx + 1}.').classes('text-lg font-bold text-gray-700 w-8')
                                ui.label(issue).classes('text-lg font-semibold')
                                ui.badge(priority, color=badge_color)
                            
                            with ui.column().classes('items-end'):
                                ui.label(f'{pct:.1f}% ({cumulative_pct:.1f}% cumulative)').classes('text-sm font-bold')
                        
                        # Progress bar
                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                            ui.linear_progress(pct / 100).classes(f'flex-1 {bar_color}')
                            ui.label(f'{downtime:.0f} min').classes('text-sm font-semibold w-20 text-right')
                        
                        # Details
                        with ui.row().classes('w-full gap-4 text-xs text-gray-600'):
                            ui.label(f'🔢 {frequency} occurrences')
                            ui.label(f'⏱️ Avg: {avg_duration} min')
                            ui.label(f'🏭 {lines_affected} line(s) affected')
                
                # 80/20 rule indicator
                with ui.card().classes('w-full p-4 bg-blue-50 border-l-4 border-blue-500 mt-4'):
                    ui.label('📊 Pareto Principle (80/20 Rule)').classes('text-sm font-bold mb-2')
                    top_issues = sum(1 for i, row in enumerate(data) if sum(r[2] for r in data[:i+1]) / total_downtime <= 0.8)
                    ui.label(f'The top {top_issues} issue(s) account for 80% of total downtime').classes('text-sm')
                    ui.label('Focus your root cause analysis efforts on these high-priority issues').classes('text-xs text-gray-600 mt-1')
        
        def create_shift_issues_chart(data):
            """Create shift issues analysis chart"""
            if not data:
                return
            
            # Group by issue type
            issue_summary = defaultdict(lambda: {'total': 0, 'open': 0, 'resolved': 0, 'severities': defaultdict(int)})
            
            for row in data:
                issue_type, severity, frequency, open_count, resolved_count = row
                issue_summary[issue_type]['total'] += frequency
                issue_summary[issue_type]['open'] += open_count
                issue_summary[issue_type]['resolved'] += resolved_count
                issue_summary[issue_type]['severities'][severity] += frequency
            
            # Sort by total frequency
            sorted_issues = sorted(issue_summary.items(), key=lambda x: x[1]['total'], reverse=True)
            total_issues = sum(item[1]['total'] for item in sorted_issues)
            
            with ui.card().classes('w-full p-4'):
                ui.label(f'Total Issues: {total_issues}').classes('text-lg font-semibold mb-4')
                
                cumulative_pct = 0
                for idx, (issue_type, stats) in enumerate(sorted_issues):
                    pct = (stats['total'] / total_issues) * 100
                    cumulative_pct += pct
                    resolution_rate = (stats['resolved'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    
                    with ui.card().classes('w-full p-3 mb-2'):
                        with ui.row().classes('w-full items-center justify-between mb-2'):
                            ui.label(f'{idx + 1}. {issue_type}').classes('text-lg font-semibold')
                            ui.label(f'{pct:.1f}% ({cumulative_pct:.1f}% cumulative)').classes('text-sm font-bold')
                        
                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                            ui.linear_progress(pct / 100).classes('flex-1 bg-purple-500')
                            ui.label(f'{stats["total"]}').classes('text-sm font-semibold w-16 text-right')
                        
                        with ui.row().classes('w-full gap-4 text-xs'):
                            ui.label(f'✅ Resolved: {stats["resolved"]} ({resolution_rate:.0f}%)').classes('text-green-700')
                            ui.label(f'⚠️ Open: {stats["open"]}').classes('text-red-700')
                            
                            # Severity breakdown
                            severity_text = ' | '.join([f'{sev}: {count}' for sev, count in stats['severities'].items()])
                            ui.label(f'Severity: {severity_text}').classes('text-gray-600')
        
        def create_correlation_matrix(correlations):
            """Display issue correlation analysis"""
            if not correlations:
                return
            
            with ui.card().classes('w-full p-4'):
                ui.label('Frequently Co-occurring Issues').classes('text-lg font-semibold mb-4')
                ui.label('Issues that tend to happen together may share common root causes').classes('text-sm text-gray-600 mb-4')
                
                for row in correlations:
                    issue1, issue2, co_occurrence, avg_hours_apart = row
                    
                    # Correlation strength
                    if co_occurrence >= 10:
                        strength = 'STRONG'
                        color = 'red'
                    elif co_occurrence >= 5:
                        strength = 'MODERATE'
                        color = 'orange'
                    else:
                        strength = 'WEAK'
                        color = 'blue'
                    
                    with ui.card().classes('w-full p-3 mb-2 border-l-4 border-purple-500'):
                        with ui.row().classes('w-full items-start justify-between'):
                            with ui.column().classes('flex-1'):
                                with ui.row().classes('items-center gap-2 mb-2'):
                                    ui.icon('link', size='sm').classes('text-purple-600')
                                    ui.label(f'{issue1}').classes('font-semibold')
                                    ui.icon('arrow_forward', size='sm').classes('text-gray-400')
                                    ui.label(f'{issue2}').classes('font-semibold')
                                
                                with ui.row().classes('gap-4 text-sm text-gray-600'):
                                    ui.label(f'Co-occurred {co_occurrence} times')
                                    ui.label(f'Avg. {avg_hours_apart} hours apart')
                            
                            ui.badge(strength, color=color)
                        
                        # Insight
                        if avg_hours_apart < 4:
                            ui.label('💡 These issues occur within hours of each other - likely related').classes('text-xs text-blue-700 mt-2')
                        elif avg_hours_apart < 12:
                            ui.label('💡 These issues occur within the same shift - may share root cause').classes('text-xs text-blue-700 mt-2')
        
        def generate_insights(downtime_data, shift_data, correlation_data):
            """Generate actionable insights"""
            with insights_container:
                ui.label('Actionable Insights').classes('text-2xl font-bold mb-4')
                
                with ui.card().classes('w-full p-4'):
                    insights = []
                    
                    # Top downtime issue
                    if downtime_data:
                        top_issue = downtime_data[0]
                        issue_name, frequency, downtime, avg_duration, lines_affected = top_issue
                        pct = (downtime / sum(row[2] for row in downtime_data)) * 100
                        
                        insights.append({
                            'icon': '🎯',
                            'title': 'Primary Focus Area',
                            'description': f'{issue_name} accounts for {pct:.1f}% of all downtime ({downtime:.0f} minutes)',
                            'action': f'Conduct detailed root cause analysis. This issue occurs {frequency} times with average duration of {avg_duration} minutes.',
                            'priority': 'CRITICAL'
                        })
                    
                    # Resolution rate
                    if shift_data:
                        total_shift_issues = sum(row[2] for row in shift_data)
                        total_resolved = sum(row[4] for row in shift_data)
                        resolution_rate = (total_resolved / total_shift_issues * 100) if total_shift_issues > 0 else 0
                        
                        insights.append({
                            'icon': '📈',
                            'title': 'Issue Resolution Performance',
                            'description': f'{resolution_rate:.1f}% of issues are being resolved ({total_resolved}/{total_shift_issues})',
                            'action': 'Review open issues to identify bottlenecks in resolution process' if resolution_rate < 80 else 'Good resolution rate - maintain current practices',
                            'priority': 'HIGH' if resolution_rate < 80 else 'MEDIUM'
                        })
                    
                    # Correlations
                    if correlation_data and len(correlation_data) >= 3:
                        insights.append({
                            'icon': '🔗',
                            'title': 'Pattern Detection',
                            'description': f'{len(correlation_data)} significant issue correlations detected',
                            'action': 'Investigate co-occurring issues - they may share common root causes or trigger each other',
                            'priority': 'HIGH'
                        })
                    
                    # Multi-line issues
                    if downtime_data:
                        multi_line_issues = [row for row in downtime_data if row[4] > 1]
                        if multi_line_issues:
                            insights.append({
                                'icon': '🏭',
                                'title': 'Systemic Issues',
                                'description': f'{len(multi_line_issues)} issue types affect multiple production lines',
                                'action': 'These may indicate process-level or equipment-level problems requiring coordinated solutions',
                                'priority': 'HIGH'
                            })
                    
                    # Display insights
                    for insight in insights:
                        priority_colors = {
                            'CRITICAL': 'border-red-500 bg-red-50',
                            'HIGH': 'border-orange-500 bg-orange-50',
                            'MEDIUM': 'border-yellow-500 bg-yellow-50'
                        }
                        
                        with ui.card().classes(f'w-full p-4 border-l-4 {priority_colors.get(insight["priority"], "border-blue-500")} mb-3'):
                            with ui.row().classes('w-full items-start justify-between mb-2'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(insight['icon']).classes('text-2xl')
                                    ui.label(insight['title']).classes('text-lg font-bold')
                                ui.badge(insight['priority'], color=insight['priority'].lower())
                            
                            ui.label(insight['description']).classes('text-sm font-semibold mb-2')
                            ui.label(f'💡 Recommended Action: {insight["action"]}').classes('text-sm text-gray-700')
        
        # Initial load
        load_analysis()
