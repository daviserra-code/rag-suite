"""
Comparative Analytics Dashboard
Line-to-line benchmarking, shift comparisons, trend analysis, and best practice identification
"""
from nicegui import ui
from datetime import datetime, timedelta
from sqlalchemy import text
from collections import defaultdict

from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine


def comparative_analytics_screen():
    """Comparative analytics dashboard"""
    
    engine = get_db_engine()
    
    with ui.column().classes('w-full p-4 gap-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Comparative Analytics').classes('text-3xl font-bold')
            ui.button('Refresh', icon='refresh', on_click=lambda: load_analytics())
        
        # Filters
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full gap-4 items-end'):
                weeks_filter = ui.select(
                    [4, 8, 12, 16],
                    label='Weeks to Analyze',
                    value=8
                ).classes('w-48').style('background: #1f2937; color: #e5e7eb;')
                
                comparison_type = ui.select(
                    ['All Comparisons', 'Line Performance', 'Shift Analysis', 'Weekly Trends'],
                    label='View',
                    value='All Comparisons'
                ).classes('w-48').style('background: #1f2937; color: #e5e7eb;')
                
                ui.button('Analyze', icon='analytics', on_click=lambda: load_analytics())
        
        # Analytics containers
        line_comparison_container = ui.column().classes('w-full gap-4')
        shift_comparison_container = ui.column().classes('w-full gap-4')
        trend_container = ui.column().classes('w-full gap-4')
        best_practices_container = ui.column().classes('w-full gap-4')
        
        def load_analytics():
            """Load comparative analytics"""
            line_comparison_container.clear()
            shift_comparison_container.clear()
            trend_container.clear()
            best_practices_container.clear()
            
            with engine.connect() as conn:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(weeks=weeks_filter.value)
                
                params = {'start_date': start_date, 'end_date': end_date}
                
                show_all = comparison_type.value == 'All Comparisons'
                
                # Line-to-Line Performance Benchmarking
                if show_all or comparison_type.value == 'Line Performance':
                    line_performance = conn.execute(text("""
                        SELECT 
                            line_id,
                            line_name,
                            COUNT(DISTINCT date) as operating_days,
                            ROUND(AVG(oee)::numeric * 100, 1) as avg_oee,
                            ROUND(AVG(availability)::numeric * 100, 1) as avg_availability,
                            ROUND(AVG(performance)::numeric * 100, 1) as avg_performance,
                            ROUND(AVG(quality)::numeric * 100, 1) as avg_quality,
                            SUM(total_units_produced) as total_production,
                            SUM(unplanned_downtime_min) as total_downtime,
                            ROUND(AVG(unplanned_downtime_min)::numeric, 1) as avg_downtime_per_shift
                        FROM oee_line_shift
                        WHERE date >= :start_date AND date <= :end_date
                        GROUP BY line_id, line_name
                        ORDER BY avg_oee DESC
                    """), params).fetchall()
                    
                    with line_comparison_container:
                        create_line_comparison(line_performance)
                
                # Shift-to-Shift Comparison
                if show_all or comparison_type.value == 'Shift Analysis':
                    shift_performance = conn.execute(text("""
                        SELECT 
                            shift,
                            COUNT(*) as total_shifts,
                            ROUND(AVG(oee)::numeric * 100, 1) as avg_oee,
                            ROUND(AVG(availability)::numeric * 100, 1) as avg_availability,
                            ROUND(AVG(performance)::numeric * 100, 1) as avg_performance,
                            ROUND(AVG(quality)::numeric * 100, 1) as avg_quality,
                            SUM(total_units_produced) as total_production,
                            ROUND(AVG(total_units_produced)::numeric, 0) as avg_production_per_shift,
                            SUM(unplanned_downtime_min) as total_downtime,
                            ROUND(AVG(unplanned_downtime_min)::numeric, 1) as avg_downtime
                        FROM oee_line_shift
                        WHERE date >= :start_date AND date <= :end_date
                        GROUP BY shift
                        ORDER BY 
                            CASE shift 
                                WHEN 'M' THEN 1 
                                WHEN 'A' THEN 2 
                                WHEN 'N' THEN 3 
                            END
                    """), params).fetchall()
                    
                    # Per-line shift performance
                    shift_by_line = conn.execute(text("""
                        SELECT 
                            line_id,
                            shift,
                            ROUND(AVG(oee)::numeric * 100, 1) as avg_oee,
                            COUNT(*) as shift_count
                        FROM oee_line_shift
                        WHERE date >= :start_date AND date <= :end_date
                        GROUP BY line_id, shift
                        ORDER BY line_id, shift
                    """), params).fetchall()
                    
                    with shift_comparison_container:
                        create_shift_comparison(shift_performance, shift_by_line)
                
                # Week-over-Week Trend Analysis
                if show_all or comparison_type.value == 'Weekly Trends':
                    weekly_trends = conn.execute(text("""
                        SELECT 
                            DATE_TRUNC('week', date)::date as week_start,
                            ROUND(AVG(oee)::numeric * 100, 1) as avg_oee,
                            SUM(total_units_produced) as total_production,
                            SUM(unplanned_downtime_min) as total_downtime,
                            COUNT(DISTINCT line_id) as active_lines,
                            COUNT(*) as total_shifts
                        FROM oee_line_shift
                        WHERE date >= :start_date AND date <= :end_date
                        GROUP BY DATE_TRUNC('week', date)
                        ORDER BY week_start
                    """), params).fetchall()
                    
                    # Per-line weekly trends
                    line_weekly_trends = conn.execute(text("""
                        SELECT 
                            line_id,
                            DATE_TRUNC('week', date)::date as week_start,
                            ROUND(AVG(oee)::numeric * 100, 1) as avg_oee
                        FROM oee_line_shift
                        WHERE date >= :start_date AND date <= :end_date
                        GROUP BY line_id, DATE_TRUNC('week', date)
                        ORDER BY line_id, week_start
                    """), params).fetchall()
                    
                    with trend_container:
                        create_trend_analysis(weekly_trends, line_weekly_trends)
                
                # Best Practice Identification
                if show_all:
                    with best_practices_container:
                        identify_best_practices(line_performance, shift_performance, weekly_trends)
        
        def create_line_comparison(data):
            """Create line-to-line performance comparison"""
            if not data:
                return
            
            ui.label('Line-to-Line Performance Benchmarking').classes('text-2xl font-bold mb-4')
            
            # Calculate benchmarks
            avg_oee = sum(row[3] for row in data) / len(data)
            best_line = data[0]
            worst_line = data[-1]
            
            # Summary cards
            with ui.row().classes('w-full gap-4 mb-4'):
                with ui.card().classes('flex-1 p-4'):
                    ui.label('🏆 Top Performer').classes('text-sm font-semibold mb-2')
                    ui.label(f'{best_line[1]}').classes('text-xl font-bold text-green-600')
                    ui.label(f'{best_line[3]}% OEE').classes('text-lg')
                
                with ui.card().classes('flex-1 p-4'):
                    ui.label('📊 Fleet Average').classes('text-sm font-semibold mb-2')
                    ui.label(f'{avg_oee:.1f}% OEE').classes('text-xl font-bold text-blue-600')
                    ui.label(f'{len(data)} Production Lines').classes('text-sm text-gray-600')
                
                with ui.card().classes('flex-1 p-4'):
                    ui.label('📉 Improvement Opportunity').classes('text-sm font-semibold mb-2')
                    ui.label(f'{worst_line[1]}').classes('text-xl font-bold text-orange-600')
                    ui.label(f'{worst_line[3]}% OEE ({best_line[3] - worst_line[3]:.1f}% gap)').classes('text-lg')
            
            # Detailed comparison table
            with ui.card().classes('w-full p-4'):
                ui.label('Detailed Performance Comparison').classes('text-lg font-semibold mb-4')
                
                for idx, row in enumerate(data):
                    (line_id, line_name, operating_days, avg_oee, avg_availability,
                     avg_performance, avg_quality, total_production, total_downtime,
                     avg_downtime_per_shift) = row
                    
                    # Color coding based on performance vs average
                    if avg_oee >= avg_oee + 5:
                        border_color = 'border-green-500'
                        badge_text = 'EXCELLENT'
                        badge_color = 'green'
                    elif avg_oee >= avg_oee - 5:
                        border_color = 'border-blue-500'
                        badge_text = 'GOOD'
                        badge_color = 'blue'
                    else:
                        border_color = 'border-orange-500'
                        badge_text = 'NEEDS ATTENTION'
                        badge_color = 'orange'
                    
                    with ui.card().classes(f'w-full p-4 mb-3 border-l-4 {border_color}'):
                        with ui.row().classes('w-full items-start justify-between mb-3'):
                            with ui.column():
                                with ui.row().classes('items-center gap-2 mb-1'):
                                    ui.label(f'#{idx + 1}').classes('text-sm font-bold text-gray-500')
                                    ui.label(line_name).classes('text-xl font-bold')
                                    ui.badge(badge_text, color=badge_color)
                                ui.label(f'{operating_days} operating days').classes('text-sm text-gray-600')
                            
                            ui.label(f'{avg_oee}%').classes('text-3xl font-bold text-blue-600')
                        
                        # OEE Components
                        with ui.row().classes('w-full gap-4 mb-3'):
                            with ui.column().classes('flex-1'):
                                ui.label('Availability').classes('text-xs font-semibold text-gray-600')
                                with ui.row().classes('items-center gap-2'):
                                    ui.linear_progress(avg_availability / 100).classes('flex-1 bg-green-500')
                                    ui.label(f'{avg_availability}%').classes('text-sm font-bold')
                            
                            with ui.column().classes('flex-1'):
                                ui.label('Performance').classes('text-xs font-semibold text-gray-600')
                                with ui.row().classes('items-center gap-2'):
                                    ui.linear_progress(avg_performance / 100).classes('flex-1 bg-blue-500')
                                    ui.label(f'{avg_performance}%').classes('text-sm font-bold')
                            
                            with ui.column().classes('flex-1'):
                                ui.label('Quality').classes('text-xs font-semibold text-gray-600')
                                with ui.row().classes('items-center gap-2'):
                                    ui.linear_progress(avg_quality / 100).classes('flex-1 bg-purple-500')
                                    ui.label(f'{avg_quality}%').classes('text-sm font-bold')
                        
                        # Key metrics
                        with ui.row().classes('w-full gap-4 text-sm text-gray-700'):
                            ui.label(f'📦 Production: {total_production:,} units')
                            ui.label(f'⏱️ Downtime: {total_downtime:.0f} min total')
                            ui.label(f'📊 Avg per shift: {avg_downtime_per_shift} min')
        
        def create_shift_comparison(shift_data, shift_by_line_data):
            """Create shift-to-shift comparison"""
            if not shift_data:
                return
            
            ui.label('Shift-to-Shift Comparison').classes('text-2xl font-bold mb-4')
            
            shift_names = {'M': 'Morning', 'A': 'Afternoon', 'N': 'Night'}
            
            # Overall shift comparison
            with ui.card().classes('w-full p-4 mb-4'):
                ui.label('Overall Shift Performance').classes('text-lg font-semibold mb-4')
                
                for row in shift_data:
                    (shift, total_shifts, avg_oee, avg_availability, avg_performance,
                     avg_quality, total_production, avg_production, total_downtime,
                     avg_downtime) = row
                    
                    shift_name = shift_names.get(shift, shift)
                    
                    # Determine best shift
                    best_oee = max(r[2] for r in shift_data)
                    is_best = avg_oee == best_oee
                    
                    with ui.card().classes(f'w-full p-4 mb-3 {"border-l-4 border-green-500" if is_best else ""}'):
                        with ui.row().classes('w-full items-center justify-between mb-3'):
                            with ui.column():
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(shift_name).classes('text-xl font-bold')
                                    if is_best:
                                        ui.badge('BEST PERFORMING', color='green')
                                ui.label(f'{total_shifts} shifts analyzed').classes('text-sm text-gray-600')
                            
                            ui.label(f'{avg_oee}%').classes('text-3xl font-bold text-blue-600')
                        
                        # Metrics comparison
                        with ui.row().classes('w-full gap-6 text-sm'):
                            with ui.column():
                                ui.label('Availability').classes('text-xs text-gray-600 mb-1')
                                ui.label(f'{avg_availability}%').classes('font-bold')
                            
                            with ui.column():
                                ui.label('Performance').classes('text-xs text-gray-600 mb-1')
                                ui.label(f'{avg_performance}%').classes('font-bold')
                            
                            with ui.column():
                                ui.label('Quality').classes('text-xs text-gray-600 mb-1')
                                ui.label(f'{avg_quality}%').classes('font-bold')
                            
                            with ui.column():
                                ui.label('Avg Production').classes('text-xs text-gray-600 mb-1')
                                ui.label(f'{avg_production:,.0f} units').classes('font-bold')
                            
                            with ui.column():
                                ui.label('Avg Downtime').classes('text-xs text-gray-600 mb-1')
                                ui.label(f'{avg_downtime} min').classes('font-bold')
            
            # Per-line shift comparison
            with ui.card().classes('w-full p-4'):
                ui.label('Shift Performance by Production Line').classes('text-lg font-semibold mb-4')
                
                # Organize data by line
                line_shifts = defaultdict(dict)
                for row in shift_by_line_data:
                    line_id, shift, avg_oee, shift_count = row
                    line_shifts[line_id][shift] = avg_oee
                
                for line_id, shifts in line_shifts.items():
                    with ui.card().classes('w-full p-3 mb-2'):
                        ui.label(line_id).classes('font-bold mb-2')
                        
                        with ui.row().classes('w-full gap-4'):
                            for shift in ['M', 'A', 'N']:
                                oee = shifts.get(shift, 0)
                                shift_name = shift_names.get(shift, shift)
                                
                                # Find best shift for this line
                                best_shift_oee = max(shifts.values()) if shifts else 0
                                is_best = oee == best_shift_oee and oee > 0
                                
                                with ui.column().classes('flex-1'):
                                    with ui.row().classes('items-center gap-2 mb-1'):
                                        ui.label(shift_name).classes('text-sm font-semibold')
                                        if is_best:
                                            ui.icon('star', size='xs').classes('text-yellow-500')
                                    
                                    if oee > 0:
                                        with ui.row().classes('items-center gap-2'):
                                            ui.linear_progress(oee / 100).classes('flex-1 bg-blue-500')
                                            ui.label(f'{oee}%').classes('text-sm font-bold')
                                    else:
                                        ui.label('No data').classes('text-xs text-gray-400')
        
        def create_trend_analysis(weekly_data, line_weekly_data):
            """Create week-over-week trend analysis"""
            if not weekly_data:
                return
            
            ui.label('Week-over-Week Trend Analysis').classes('text-2xl font-bold mb-4')
            
            # Calculate trends
            if len(weekly_data) >= 2:
                first_week_oee = weekly_data[0][1]
                last_week_oee = weekly_data[-1][1]
                trend_change = last_week_oee - first_week_oee
                trend_direction = '📈 Improving' if trend_change > 0 else '📉 Declining' if trend_change < 0 else '➡️ Stable'
            else:
                trend_direction = 'Insufficient data'
                trend_change = 0
            
            # Summary
            with ui.card().classes('w-full p-4 mb-4'):
                with ui.row().classes('w-full gap-4'):
                    with ui.column().classes('flex-1'):
                        ui.label('Overall Trend').classes('text-sm font-semibold mb-2')
                        ui.label(trend_direction).classes('text-xl font-bold')
                        if trend_change != 0:
                            ui.label(f'{abs(trend_change):.1f}% {"increase" if trend_change > 0 else "decrease"}').classes('text-sm text-gray-600')
                    
                    with ui.column().classes('flex-1'):
                        ui.label(f'{len(weekly_data)} Weeks Analyzed').classes('text-sm font-semibold mb-2')
                        total_production = sum(row[2] for row in weekly_data)
                        ui.label(f'{total_production:,} units produced').classes('text-lg')
            
            # Weekly breakdown
            with ui.card().classes('w-full p-4'):
                ui.label('Weekly Performance Breakdown').classes('text-lg font-semibold mb-4')
                
                for idx, row in enumerate(weekly_data):
                    week_start, avg_oee, total_production, total_downtime, active_lines, total_shifts = row
                    
                    # Calculate week-over-week change
                    if idx > 0:
                        prev_oee = weekly_data[idx - 1][1]
                        wow_change = avg_oee - prev_oee
                        wow_icon = '🟢' if wow_change > 0 else '🔴' if wow_change < 0 else '🟡'
                        wow_text = f'{wow_icon} {abs(wow_change):.1f}% vs prev week'
                    else:
                        wow_text = 'Baseline week'
                    
                    with ui.card().classes('w-full p-3 mb-2'):
                        with ui.row().classes('w-full items-center justify-between mb-2'):
                            with ui.column():
                                ui.label(f'Week of {week_start.strftime("%b %d, %Y")}').classes('font-bold')
                                ui.label(wow_text).classes('text-xs text-gray-600')
                            
                            ui.label(f'{avg_oee}%').classes('text-2xl font-bold text-blue-600')
                        
                        with ui.row().classes('w-full gap-4 text-sm text-gray-700'):
                            ui.label(f'📦 {total_production:,} units')
                            ui.label(f'⏱️ {total_downtime:.0f} min downtime')
                            ui.label(f'🏭 {active_lines} lines')
                            ui.label(f'📊 {total_shifts} shifts')
        
        def identify_best_practices(line_data, shift_data, weekly_data):
            """Identify and highlight best practices"""
            ui.label('Best Practice Identification').classes('text-2xl font-bold mb-4')
            
            with ui.card().classes('w-full p-4'):
                ui.label('🏆 Key Insights & Recommendations').classes('text-lg font-semibold mb-4')
                
                insights = []
                
                # Best performing line
                if line_data:
                    best_line = line_data[0]
                    insights.append({
                        'icon': '🌟',
                        'title': 'Top Performing Line',
                        'description': f'{best_line[1]} achieves {best_line[3]}% OEE',
                        'recommendation': f'Study {best_line[1]} operations and replicate successful practices across other lines. Key factors: {best_line[4]:.1f}% availability, {best_line[5]:.1f}% performance.',
                        'priority': 'HIGH'
                    })
                    
                    # Identify gap
                    if len(line_data) > 1:
                        worst_line = line_data[-1]
                        gap = best_line[3] - worst_line[3]
                        if gap > 10:
                            insights.append({
                                'icon': '📊',
                                'title': 'Performance Gap Identified',
                                'description': f'{gap:.1f}% OEE difference between best and worst lines',
                                'recommendation': f'Focus improvement efforts on {worst_line[1]}. Potential annual savings if gap is closed: significant.',
                                'priority': 'CRITICAL'
                            })
                
                # Best shift
                if shift_data:
                    best_shift = max(shift_data, key=lambda x: x[2])
                    shift_names = {'M': 'Morning', 'A': 'Afternoon', 'N': 'Night'}
                    insights.append({
                        'icon': '⏰',
                        'title': 'Optimal Shift Performance',
                        'description': f'{shift_names.get(best_shift[0], best_shift[0])} shift performs best at {best_shift[2]}% OEE',
                        'recommendation': f'Investigate what makes {shift_names.get(best_shift[0])} shift successful. Consider crew training transfer, equipment condition at shift start, or process adherence.',
                        'priority': 'MEDIUM'
                    })
                
                # Trend analysis
                if weekly_data and len(weekly_data) >= 4:
                    recent_weeks = weekly_data[-4:]
                    avg_recent = sum(w[1] for w in recent_weeks) / len(recent_weeks)
                    older_weeks = weekly_data[:-4]
                    avg_older = sum(w[1] for w in older_weeks) / len(older_weeks) if older_weeks else avg_recent
                    
                    if avg_recent > avg_older + 2:
                        insights.append({
                            'icon': '📈',
                            'title': 'Positive Momentum',
                            'description': f'Performance improving: {avg_recent:.1f}% OEE in recent weeks vs {avg_older:.1f}% previously',
                            'recommendation': 'Continue current improvement initiatives. Document recent changes that led to improvement.',
                            'priority': 'POSITIVE'
                        })
                    elif avg_recent < avg_older - 2:
                        insights.append({
                            'icon': '⚠️',
                            'title': 'Performance Decline',
                            'description': f'Performance declining: {avg_recent:.1f}% OEE in recent weeks vs {avg_older:.1f}% previously',
                            'recommendation': 'Investigate recent changes. Review maintenance records, staffing changes, or process modifications.',
                            'priority': 'CRITICAL'
                        })
                
                # Display insights
                for insight in insights:
                    priority_colors = {
                        'CRITICAL': 'border-red-500 bg-red-50',
                        'HIGH': 'border-orange-500 bg-orange-50',
                        'MEDIUM': 'border-yellow-500 bg-yellow-50',
                        'POSITIVE': 'border-green-500 bg-green-50'
                    }
                    
                    with ui.card().classes(f'w-full p-4 border-l-4 {priority_colors.get(insight["priority"], "border-blue-500")} mb-3'):
                        with ui.row().classes('w-full items-start justify-between mb-2'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label(insight['icon']).classes('text-2xl')
                                ui.label(insight['title']).classes('text-lg font-bold')
                            ui.badge(insight['priority'], color=insight['priority'].lower())
                        
                        ui.label(insight['description']).classes('text-sm font-semibold mb-2')
                        ui.label(f'💡 {insight["recommendation"]}').classes('text-sm text-gray-700')
        
        # Initial load
        load_analytics()
