import os
from nicegui import ui, app
from sqlalchemy import create_engine, text
from typing import List, Dict
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import io

# Import export utilities
import sys
sys.path.insert(0, '/app')
from packages.export_utils.csv_export import create_csv_download
from packages.export_utils.pdf_export import (
    export_to_pdf, 
    generate_pdf_metric_cards, 
    generate_pdf_table,
    generate_pdf_section
)

# Database connection
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "ragdb")

engine = create_engine(f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def get_production_lines_summary(days: int = 30) -> List[Dict]:
    """Get comprehensive summary for all production lines"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    line_id,
                    line_name,
                    COUNT(DISTINCT date || shift) as total_shifts,
                    AVG(oee) * 100 as avg_oee,
                    AVG(availability) * 100 as avg_availability,
                    AVG(performance) * 100 as avg_performance,
                    AVG(quality) * 100 as avg_quality,
                    SUM(total_units_produced) as total_units,
                    SUM(good_units) as total_good_units,
                    MAX(date) as last_updated
                FROM oee_line_shift
                WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY line_id, line_name
                ORDER BY avg_oee DESC
            """))
            
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error fetching production lines: {e}")
        return []

def get_line_recent_issues(line_id: str, limit: int = 3) -> List[Dict]:
    """Get recent issues for a specific line"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    date,
                    shift,
                    loss_category,
                    description as station,
                    duration_min,
                    start_timestamp
                FROM oee_downtime_events
                WHERE line_id = :line_id
                ORDER BY start_timestamp DESC
                LIMIT :limit
            """), {"line_id": line_id, "limit": limit})
            
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error fetching issues for {line_id}: {e}")
        return []

def get_line_status(line_id: str) -> Dict:
    """Get real-time status of a production line"""
    try:
        with engine.connect() as conn:
            # Check latest shift data - use OEE to determine status
            result = conn.execute(text("""
                WITH latest_shift AS (
                    SELECT 
                        line_id,
                        date,
                        shift,
                        oee * 100 as oee,
                        availability * 100 as availability,
                        date + INTERVAL '1 day' * 
                            CASE shift 
                                WHEN 'M' THEN 0
                                WHEN 'A' THEN 0.33
                                WHEN 'N' THEN 0.67
                            END as shift_end
                    FROM oee_line_shift
                    WHERE line_id = :line_id
                    ORDER BY date DESC, shift DESC
                    LIMIT 1
                ),
                max_timestamp AS (
                    SELECT MAX(start_timestamp) as latest_time
                    FROM oee_downtime_events
                    WHERE line_id = :line_id
                ),
                active_downtime AS (
                    SELECT COUNT(*) as downtime_count,
                           SUM(duration_min) as total_downtime_min
                    FROM oee_downtime_events, max_timestamp
                    WHERE oee_downtime_events.line_id = :line_id
                      AND oee_downtime_events.start_timestamp >= max_timestamp.latest_time - INTERVAL '30 minutes'
                      AND oee_downtime_events.start_timestamp <= max_timestamp.latest_time
                      AND oee_downtime_events.duration_min > 10
                )
                SELECT 
                    ls.line_id,
                    ls.date,
                    ls.shift,
                    ls.oee,
                    ls.availability,
                    ls.shift_end,
                    ad.downtime_count,
                    CASE 
                        WHEN ls.availability < 50 THEN 'stopped'
                        WHEN ls.oee < 70 THEN 'warning'
                        ELSE 'running'
                    END as status
                FROM latest_shift ls, active_downtime ad
            """), {"line_id": line_id})
            
            row = result.fetchone()
            if row:
                return {
                    'status': row[7],  # running, stopped, warning
                    'last_updated': f"{row[1]} {row[2]}",
                    'current_oee': float(row[3] or 0),
                    'downtime_events': int(row[6] or 0)
                }
            else:
                return {'status': 'unknown', 'last_updated': 'N/A', 'current_oee': 0, 'downtime_events': 0}
    except Exception as e:
        print(f"Error fetching status for {line_id}: {e}")
        return {'status': 'unknown', 'last_updated': 'N/A', 'current_oee': 0, 'downtime_events': 0}

def get_line_trend(line_id: str, days: int = 7) -> Dict:
    """Get OEE trend data for a specific line"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    date,
                    shift,
                    oee * 100 as oee
                FROM oee_line_shift
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
                ORDER BY date, shift
            """), {"line_id": line_id})
            
            rows = result.fetchall()
            return {
                'dates': [f"{row[0]} {row[1]}" for row in rows],
                'oee': [float(row[2] or 0) for row in rows]
            }
    except Exception as e:
        print(f"Error fetching trend for {line_id}: {e}")
        return {'dates': [], 'oee': []}

def build_production_lines_overview():
    """Production Lines Overview - Enhanced with real-time data and interactive features"""
    
    # State
    if 'lines_days_filter' not in app.storage.user:
        app.storage.user['lines_days_filter'] = 30
    if 'lines_sort_by' not in app.storage.user:
        app.storage.user['lines_sort_by'] = 'oee'
    if 'selected_line_detail' not in app.storage.user:
        app.storage.user['selected_line_detail'] = None
    if 'selected_lines_compare' not in app.storage.user:
        app.storage.user['selected_lines_compare'] = []
    if 'comparison_mode' not in app.storage.user:
        app.storage.user['comparison_mode'] = False
    
    def update_filter(days: int):
        """Update time filter"""
        app.storage.user['lines_days_filter'] = days
        summary_cards.refresh()
        lines_table.refresh()
    
    def update_sort(sort_by: str):
        """Update sort order"""
        app.storage.user['lines_sort_by'] = sort_by
        lines_table.refresh()
    
    def view_line_detail(line_id: str):
        """Show detailed view for a line"""
        app.storage.user['selected_line_detail'] = line_id
        line_detail_display.refresh()
    
    def close_detail():
        """Close detail view"""
        app.storage.user['selected_line_detail'] = None
        line_detail_display.refresh()
    
    def toggle_comparison_mode():
        """Toggle comparison mode"""
        app.storage.user['comparison_mode'] = not app.storage.user['comparison_mode']
        if not app.storage.user['comparison_mode']:
            app.storage.user['selected_lines_compare'] = []
        lines_table.refresh()
        comparison_display.refresh()
        # Refresh header to update button text
        summary_cards.refresh()
    
    def toggle_line_selection(line_id: str):
        """Toggle line selection for comparison"""
        selected = app.storage.user['selected_lines_compare']
        if line_id in selected:
            selected.remove(line_id)
        else:
            if len(selected) < 4:  # Max 4 lines
                selected.append(line_id)
            else:
                ui.notify('Maximum 4 lines can be compared', type='warning')
        app.storage.user['selected_lines_compare'] = selected
        lines_table.refresh()
        comparison_display.refresh()
    
    def clear_comparison():
        """Clear all selected lines"""
        app.storage.user['selected_lines_compare'] = []
        lines_table.refresh()
        comparison_display.refresh()
    
    def export_csv():
        """Export production lines data to CSV"""
        days = app.storage.user['lines_days_filter']
        lines_data = get_production_lines_summary(days)
        
        if not lines_data:
            ui.notify('No data to export', type='warning')
            return
        
        # Prepare data for CSV
        csv_data = []
        for line in lines_data:
            csv_data.append({
                'Line ID': line['line_id'],
                'Line Name': line['line_name'],
                'Total Shifts': line.get('total_shifts', 0),
                'Average OEE (%)': round(line['avg_oee'], 2),
                'Availability (%)': round(line['avg_availability'], 2),
                'Performance (%)': round(line['avg_performance'], 2),
                'Quality (%)': round(line['avg_quality'], 2),
                'Total Units': line.get('total_units', 0),
                'Good Units': line.get('total_good_units', 0),
                'Last Updated': line.get('last_updated', 'N/A')
            })
        
        # Generate CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"production_lines_{timestamp}.csv"
        csv_content = create_csv_download(csv_data, filename)
        
        # Create download
        ui.download(csv_content, filename)
        ui.notify(f'Exported {len(csv_data)} lines to CSV', type='positive')
    
    def export_pdf():
        """Export production lines report to PDF"""
        days = app.storage.user['lines_days_filter']
        lines_data = get_production_lines_summary(days)
        
        if not lines_data:
            ui.notify('No data to export', type='warning')
            return
        
        # Calculate summary metrics
        avg_oee = sum(line['avg_oee'] for line in lines_data) / len(lines_data) if lines_data else 0
        total_units = sum(line.get('total_units', 0) for line in lines_data)
        total_good = sum(line.get('total_good_units', 0) for line in lines_data)
        quality_rate = (total_good / total_units * 100) if total_units > 0 else 0
        
        # Metric cards
        metrics = [
            {'label': 'Total Lines', 'value': str(len(lines_data)), 'subtitle': 'Active Production Lines'},
            {'label': 'Average OEE', 'value': f'{avg_oee:.1f}%', 'subtitle': f'Last {days} Days'},
            {'label': 'Total Production', 'value': f'{total_units:,.0f}', 'subtitle': 'Units Produced'},
            {'label': 'Quality Rate', 'value': f'{quality_rate:.1f}%', 'subtitle': 'Good Units / Total'}
        ]
        
        # Prepare table data with status
        table_data = []
        for line in lines_data:
            line_status = get_line_status(line['line_id'])
            status = line_status['status']
            
            if status == 'running':
                status_badge = '🟢 Running'
            elif status == 'stopped':
                status_badge = '🔴 Stopped'
            elif status == 'warning':
                status_badge = '🟡 Warning'
            else:
                status_badge = '⚪ Unknown'
            
            table_data.append({
                'status': status_badge,
                'line_id': line['line_id'],
                'line_name': line['line_name'],
                'shifts': f"{line.get('total_shifts', 0):,}",
                'oee': f"{line['avg_oee']:.1f}%",
                'availability': f"{line['avg_availability']:.1f}%",
                'performance': f"{line['avg_performance']:.1f}%",
                'quality': f"{line['avg_quality']:.1f}%",
                'units': f"{line.get('total_units', 0):,.0f}"
            })
        
        # Build PDF content
        content_html = generate_pdf_metric_cards(metrics)
        content_html += generate_pdf_table(
            table_data,
            columns=['status', 'line_id', 'line_name', 'shifts', 'oee', 'availability', 'performance', 'quality', 'units'],
            title='Production Lines Summary'
        )
        
        # Add recent issues section
        issues_html = '<h2>Recent Issues Summary</h2>'
        for line in lines_data[:3]:  # Top 3 lines
            issues = get_line_recent_issues(line['line_id'], 3)
            if issues:
                issues_html += f'<h3>{line["line_id"]} - {line["line_name"]}</h3>'
                for issue in issues:
                    issues_html += f'''
                    <div class="issue-item">
                        <strong>{issue["loss_category"]}</strong> - 
                        {issue["date"]} {issue["shift"]} - 
                        {issue["station"]} - 
                        {issue["duration_min"]:.0f} minutes
                    </div>
                    '''
        
        content_html += issues_html
        
        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"production_lines_report_{timestamp}.pdf"
        
        pdf_bytes = export_to_pdf(
            title='Production Lines Overview',
            subtitle=f'Performance Report - Last {days} Days',
            content_html=content_html,
            filename=filename
        )
        
        # Create download
        ui.download(pdf_bytes, filename)
        ui.notify('PDF report generated successfully', type='positive')
    
    @ui.refreshable
    def summary_cards():
        """Summary statistics cards"""
        days = app.storage.user['lines_days_filter']
        lines_data = get_production_lines_summary(days)
        
        with ui.row().classes('w-full gap-4 mb-6'):
            with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-blue-600 to-blue-700 text-white'):
                ui.label('Total Lines').classes('text-xs opacity-80')
                ui.label(str(len(lines_data))).classes('text-4xl font-bold')
                ui.label('Active Production Lines').classes('text-xs opacity-80 mt-2')
            
            avg_oee = sum(line['avg_oee'] for line in lines_data) / len(lines_data) if lines_data else 0
            with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-teal-600 to-teal-700 text-white'):
                ui.label('Average OEE').classes('text-xs opacity-80')
                ui.label(f'{avg_oee:.1f}%').classes('text-4xl font-bold')
                ui.label(f'Last {days} Days').classes('text-xs opacity-80 mt-2')
            
            total_units = sum(line.get('total_units', 0) for line in lines_data)
            with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-purple-600 to-purple-700 text-white'):
                ui.label('Total Production').classes('text-xs opacity-80')
                ui.label(f'{total_units:,.0f}').classes('text-4xl font-bold')
                ui.label('Units Produced').classes('text-xs opacity-80 mt-2')
            
            total_good = sum(line.get('total_good_units', 0) for line in lines_data)
            quality_rate = (total_good / total_units * 100) if total_units > 0 else 0
            with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-green-600 to-green-700 text-white'):
                ui.label('Quality Rate').classes('text-xs opacity-80')
                ui.label(f'{quality_rate:.1f}%').classes('text-4xl font-bold')
                ui.label('Good Units / Total').classes('text-xs opacity-80 mt-2')
    
    @ui.refreshable
    def lines_table():
        """Interactive production lines table"""
        days = app.storage.user['lines_days_filter']
        sort_by = app.storage.user['lines_sort_by']
        comparison_mode = app.storage.user['comparison_mode']
        selected_lines = app.storage.user['selected_lines_compare']
        
        lines_data = get_production_lines_summary(days)
        
        # Sort data
        if sort_by == 'oee':
            lines_data.sort(key=lambda x: x['avg_oee'], reverse=True)
        elif sort_by == 'line_id':
            lines_data.sort(key=lambda x: x['line_id'])
        elif sort_by == 'units':
            lines_data.sort(key=lambda x: x.get('total_units', 0), reverse=True)
        
        # Table header
        with ui.row().classes('w-full gap-2 pb-3 border-b-2 border-gray-300 dark:border-gray-600 font-bold'):
            if comparison_mode:
                ui.label('Select').classes('w-16 text-sm text-center text-gray-700 dark:text-gray-200')
            ui.label('Status').classes('w-24 text-sm text-center text-gray-700 dark:text-gray-200')
            ui.label('Line ID').classes('flex-[1] text-sm text-gray-700 dark:text-gray-200')
            ui.label('Line Name').classes('flex-[3] text-sm text-gray-700 dark:text-gray-200')
            ui.label('Shifts').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('OEE').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('Avail.').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('Perf.').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('Qual.').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('Units').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            if not comparison_mode:
                ui.label('Actions').classes('flex-[1] text-sm text-center text-gray-700 dark:text-gray-200')
        
        # Table rows
        for line in lines_data:
            oee = line['avg_oee']
            if oee >= 80:
                bg_color = 'bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-800/30'
                oee_color = 'text-green-700 dark:text-green-400 font-bold'
            elif oee >= 75:
                bg_color = 'bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-800/30'
                oee_color = 'text-blue-700 dark:text-blue-400 font-bold'
            else:
                bg_color = 'bg-yellow-50 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-800/30'
                oee_color = 'text-yellow-700 dark:text-yellow-400 font-bold'
            
            # Get real-time status
            line_status = get_line_status(line['line_id'])
            status = line_status['status']
            
            # Status badge styling
            if status == 'running':
                status_icon = '🟢'
                status_text = 'Running'
                status_color = 'text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/30'
            elif status == 'stopped':
                status_icon = '🔴'
                status_text = 'Stopped'
                status_color = 'text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/30'
            elif status == 'warning':
                status_icon = '🟡'
                status_text = 'Warning'
                status_color = 'text-orange-700 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30'
            else:
                status_icon = '⚪'
                status_text = 'Unknown'
                status_color = 'text-gray-700 dark:text-gray-400 bg-gray-100 dark:bg-gray-800'
            
            is_selected = line['line_id'] in selected_lines
            row_border = 'border-l-4 border-blue-500' if is_selected else ''
            
            with ui.row().classes(f'w-full gap-2 py-3 border-b border-gray-200 dark:border-gray-700 {bg_color} {row_border} transition-colors'):
                if comparison_mode:
                    with ui.row().classes('w-16 justify-center'):
                        ui.checkbox(value=is_selected, on_change=lambda e, l=line['line_id']: toggle_line_selection(l))
                
                # Status badge
                with ui.row().classes('w-24 justify-center items-center'):
                    with ui.card().classes(f'px-2 py-1 {status_color} shadow-sm'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label(status_icon).classes('text-xs')
                            ui.label(status_text).classes('text-xs font-bold')
                
                ui.label(line['line_id']).classes('flex-[1] text-sm font-mono font-bold text-gray-900 dark:text-gray-100')
                ui.label(line['line_name']).classes('flex-[3] text-sm text-gray-800 dark:text-gray-200')
                ui.label(f"{line.get('total_shifts', 0):,}").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                ui.label(f"{oee:.1f}%").classes(f'flex-[1] text-sm text-right {oee_color}')
                ui.label(f"{line['avg_availability']:.1f}%").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                ui.label(f"{line['avg_performance']:.1f}%").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                ui.label(f"{line['avg_quality']:.1f}%").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                ui.label(f"{line.get('total_units', 0):,.0f}").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                
                if not comparison_mode:
                    with ui.row().classes('flex-[1] justify-center gap-1'):
                        ui.button(icon='visibility', on_click=lambda l=line['line_id']: view_line_detail(l)).classes('text-xs').props('flat dense')
    
    @ui.refreshable
    def line_detail_display():
        """Detailed view for selected line"""
        line_id = app.storage.user.get('selected_line_detail')
        
        if not line_id:
            return
        
        # Get line data
        days = app.storage.user['lines_days_filter']
        all_lines = get_production_lines_summary(days)
        line_data = next((l for l in all_lines if l['line_id'] == line_id), None)
        
        if not line_data:
            return
        
        # Modal overlay
        with ui.dialog().props('maximized') as dialog:
            dialog.open()
            
            with ui.card().classes('w-full max-w-6xl'):
                # Header with status
                line_status = get_line_status(line_id)
                status = line_status['status']
                
                # Status styling
                if status == 'running':
                    status_badge = '🟢 Running'
                    status_color = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                elif status == 'stopped':
                    status_badge = '🔴 Stopped'
                    status_color = 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                elif status == 'warning':
                    status_badge = '🟡 Warning'
                    status_color = 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                else:
                    status_badge = '⚪ Unknown'
                    status_color = 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400'
                
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    with ui.row().classes('items-center gap-3'):
                        ui.label(f"{line_data['line_id']} - {line_data['line_name']}").classes('text-2xl font-bold')
                        with ui.card().classes(f'px-3 py-1 {status_color}'):
                            ui.label(status_badge).classes('text-sm font-bold')
                    ui.button(icon='close', on_click=lambda: [close_detail(), dialog.close()]).props('flat round')
                
                # Add last updated time
                with ui.row().classes('w-full mb-2'):
                    ui.label(f"Last Updated: {line_status['last_updated']}").classes('text-xs text-gray-500 dark:text-gray-400')
                    if line_status['downtime_events'] > 0:
                        ui.label(f"• {line_status['downtime_events']} downtime event(s) in last hour").classes('text-xs text-red-600 dark:text-red-400 font-bold')
                
                # Metrics
                with ui.row().classes('w-full gap-4 mb-4'):
                    with ui.card().classes('flex-1 bg-teal-50 dark:bg-teal-900/20'):
                        ui.label('OEE').classes('text-xs text-gray-600 dark:text-gray-400')
                        ui.label(f"{line_data['avg_oee']:.1f}%").classes('text-3xl font-bold text-teal-700 dark:text-teal-400')
                    
                    with ui.card().classes('flex-1 bg-green-50 dark:bg-green-900/20'):
                        ui.label('Availability').classes('text-xs text-gray-600 dark:text-gray-400')
                        ui.label(f"{line_data['avg_availability']:.1f}%").classes('text-3xl font-bold text-green-700 dark:text-green-400')
                    
                    with ui.card().classes('flex-1 bg-blue-50 dark:bg-blue-900/20'):
                        ui.label('Performance').classes('text-xs text-gray-600 dark:text-gray-400')
                        ui.label(f"{line_data['avg_performance']:.1f}%").classes('text-3xl font-bold text-blue-700 dark:text-blue-400')
                    
                    with ui.card().classes('flex-1 bg-purple-50 dark:bg-purple-900/20'):
                        ui.label('Quality').classes('text-xs text-gray-600 dark:text-gray-400')
                        ui.label(f"{line_data['avg_quality']:.1f}%").classes('text-3xl font-bold text-purple-700 dark:text-purple-400')
                
                # OEE Trend Chart
                trend_data = get_line_trend(line_id, 7)
                
                with ui.card().classes('w-full mb-4'):
                    ui.label('7-Day OEE Trend').classes('text-lg font-bold mb-2')
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=trend_data['dates'],
                        y=trend_data['oee'],
                        mode='lines+markers',
                        line=dict(color='#0F7C7C', width=3),
                        marker=dict(size=8),
                        fill='tozeroy',
                        fillcolor='rgba(15, 124, 124, 0.1)'
                    ))
                    fig.update_layout(
                        height=250,
                        margin=dict(l=40, r=20, t=20, b=60),
                        xaxis=dict(title='Date & Shift', tickangle=-45),
                        yaxis=dict(title='OEE (%)', range=[0, 100]),
                        showlegend=False
                    )
                    ui.plotly(fig).classes('w-full')
                
                # Recent Issues
                issues = get_line_recent_issues(line_id, 5)
                
                with ui.card().classes('w-full'):
                    ui.label('Recent Issues').classes('text-lg font-bold mb-3')
                    
                    if issues:
                        for issue in issues:
                            with ui.row().classes('w-full items-center gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded mb-2'):
                                ui.icon('warning', size='sm').classes('text-orange-500')
                                ui.label(f"{issue['date']} {issue['shift']}").classes('text-xs w-24 text-gray-600 dark:text-gray-400')
                                ui.label(issue['loss_category']).classes('text-sm font-bold text-red-600 dark:text-red-400 w-32')
                                ui.label(issue['station']).classes('text-sm flex-grow')
                                ui.label(f"{issue['duration_min']:.0f} min").classes('text-sm text-orange-600 dark:text-orange-400 font-bold')
                    else:
                        ui.label('No recent issues').classes('text-sm text-gray-500')
    
    @ui.refreshable
    def comparison_display():
        """Multi-line comparison view"""
        selected_lines = app.storage.user['selected_lines_compare']
        
        if not selected_lines or len(selected_lines) < 2:
            return
        
        days = app.storage.user['lines_days_filter']
        all_lines = get_production_lines_summary(days)
        selected_data = [l for l in all_lines if l['line_id'] in selected_lines]
        
        with ui.card().classes('sf-card w-full'):
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label(f'📊 Comparing {len(selected_lines)} Lines').classes('text-xl font-bold')
                ui.button('Clear Selection', icon='clear', on_click=clear_comparison).classes('sf-btn secondary').props('flat')
            
            # Comparison metrics cards
            with ui.row().classes('w-full gap-4 mb-4'):
                for line in selected_data:
                    with ui.card().classes('flex-1 border-2 border-blue-300 dark:border-blue-700'):
                        ui.label(line['line_id']).classes('text-sm font-mono font-bold text-blue-600 dark:text-blue-400')
                        ui.label(line['line_name']).classes('text-xs text-gray-600 dark:text-gray-400 mb-2')
                        with ui.row().classes('w-full justify-between'):
                            ui.label('OEE:').classes('text-xs')
                            ui.label(f"{line['avg_oee']:.1f}%").classes('text-lg font-bold text-teal-700 dark:text-teal-400')
            
            # Comparative bar chart - OEE Components
            with ui.card().classes('w-full mb-4'):
                ui.label('OEE Components Comparison').classes('text-lg font-bold mb-2')
                
                fig = go.Figure()
                
                metrics = ['avg_oee', 'avg_availability', 'avg_performance', 'avg_quality']
                metric_names = ['OEE', 'Availability', 'Performance', 'Quality']
                colors = ['#0F7C7C', '#10B981', '#3B82F6', '#8B5CF6']
                
                for i, (metric, name, color) in enumerate(zip(metrics, metric_names, colors)):
                    fig.add_trace(go.Bar(
                        name=name,
                        x=[line['line_id'] for line in selected_data],
                        y=[line[metric] for line in selected_data],
                        marker_color=color,
                        text=[f"{line[metric]:.1f}%" for line in selected_data],
                        textposition='auto'
                    ))
                
                fig.update_layout(
                    barmode='group',
                    height=350,
                    margin=dict(l=40, r=20, t=20, b=60),
                    xaxis=dict(title='Production Line'),
                    yaxis=dict(title='Percentage (%)', range=[0, 100]),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                ui.plotly(fig).classes('w-full')
            
            # Trend comparison chart
            with ui.card().classes('w-full mb-4'):
                ui.label('7-Day OEE Trend Comparison').classes('text-lg font-bold mb-2')
                
                fig = go.Figure()
                
                line_colors = ['#0F7C7C', '#F59E0B', '#EF4444', '#8B5CF6']
                
                for idx, line_id in enumerate(selected_lines):
                    trend_data = get_line_trend(line_id, 7)
                    if trend_data['dates']:
                        fig.add_trace(go.Scatter(
                            x=trend_data['dates'],
                            y=trend_data['oee'],
                            mode='lines+markers',
                            name=line_id,
                            line=dict(color=line_colors[idx % len(line_colors)], width=3),
                            marker=dict(size=6)
                        ))
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=40, r=20, t=20, b=60),
                    xaxis=dict(title='Date & Shift', tickangle=-45),
                    yaxis=dict(title='OEE (%)', range=[0, 100]),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    hovermode='x unified'
                )
                ui.plotly(fig).classes('w-full')
            
            # Production comparison
            with ui.card().classes('w-full'):
                ui.label('Production Volume Comparison').classes('text-lg font-bold mb-2')
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=[line['line_id'] for line in selected_data],
                    y=[line.get('total_units', 0) for line in selected_data],
                    marker_color='#3B82F6',
                    text=[f"{line.get('total_units', 0):,.0f}" for line in selected_data],
                    textposition='auto'
                ))
                
                fig.update_layout(
                    height=250,
                    margin=dict(l=40, r=20, t=20, b=60),
                    xaxis=dict(title='Production Line'),
                    yaxis=dict(title='Total Units Produced'),
                    showlegend=False
                )
                ui.plotly(fig).classes('w-full')
    
    # Main Layout
    with ui.column().classes('w-full gap-4').style('background: #0f172a; min-height: 100vh; padding: 20px;'):
        # Header with filters
        with ui.card().classes('sf-card').style('background: #1e293b; border: 1px solid #334155;'):
            with ui.row().classes('w-full items-center justify-between mb-2'):
                ui.label('📊 Production Lines Overview').classes('text-2xl font-bold text-gray-100')
                
                with ui.row().classes('gap-2'):
                    comparison_mode = app.storage.user['comparison_mode']
                    ui.button(
                        'Compare Lines' if not comparison_mode else 'Exit Comparison',
                        icon='compare_arrows' if not comparison_mode else 'close',
                        on_click=toggle_comparison_mode
                    ).classes('sf-btn primary' if not comparison_mode else 'sf-btn secondary')
                    
                    ui.select(
                        {7: 'Last 7 Days', 14: 'Last 14 Days', 30: 'Last 30 Days', 90: 'Last 90 Days'},
                        value=app.storage.user['lines_days_filter'],
                        label='Time Range',
                        on_change=lambda e: update_filter(e.value)
                    ).classes('w-32')
                    
                    ui.select(
                        {'oee': 'Sort by OEE', 'line_id': 'Sort by Line ID', 'units': 'Sort by Units'},
                        value=app.storage.user['lines_sort_by'],
                        label='Sort By',
                        on_change=lambda e: update_sort(e.value)
                    ).classes('w-40')
            
            # Export buttons
            with ui.row().classes('w-full gap-2 mt-2'):
                ui.button('Export CSV', icon='file_download', on_click=export_csv).classes('sf-btn secondary').props('flat')
                ui.button('Export PDF', icon='picture_as_pdf', on_click=export_pdf).classes('sf-btn secondary').props('flat')
        
        # Summary Cards
        summary_cards()
        
        # Comparison display (shows when 2+ lines selected)
        comparison_display()
        
        # Lines Table
        with ui.card().classes('sf-card w-full').style('background: #1e293b; border: 1px solid #334155;'):
            ui.label('Production Lines Matrix').classes('text-lg font-bold mb-4 text-gray-100')
            lines_table()
        
        # Legend
        with ui.card().classes('sf-card w-full').style('background: #1e293b; border: 1px solid #334155;'):
            ui.label('Performance Legend').classes('text-sm font-bold mb-2 text-gray-100')
            with ui.row().classes('gap-4'):
                with ui.row().classes('items-center gap-2'):
                    ui.label('●').classes('text-green-600 dark:text-green-400 text-xl')
                    ui.label('Excellent (≥80%)').classes('text-xs text-gray-300')
                with ui.row().classes('items-center gap-2'):
                    ui.label('●').classes('text-blue-600 dark:text-blue-400 text-xl')
                    ui.label('Good (75-80%)').classes('text-xs text-gray-300')
                with ui.row().classes('items-center gap-2'):
                    ui.label('●').classes('text-yellow-600 dark:text-yellow-400 text-xl')
                    ui.label('Needs Attention (<75%)').classes('text-xs text-gray-300')
            
            ui.label('Real-Time Status').classes('text-sm font-bold mb-2 mt-3 text-gray-100')
            with ui.row().classes('gap-4'):
                with ui.row().classes('items-center gap-2'):
                    ui.label('🟢').classes('text-xl')
                    ui.label('Running (OEE ≥70%, no recent issues)').classes('text-xs text-gray-300')
                with ui.row().classes('items-center gap-2'):
                    ui.label('🟡').classes('text-xl')
                    ui.label('Warning (OEE <70%)').classes('text-xs text-gray-300')
                with ui.row().classes('items-center gap-2'):
                    ui.label('🔴').classes('text-xl')
                    ui.label('Stopped (downtime in last hour)').classes('text-xs text-gray-300')
        
        # Detail view (rendered when line is selected)
        line_detail_display()
