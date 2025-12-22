from nicegui import ui
from sqlalchemy import text
from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine
from datetime import datetime, timedelta

# Import export utilities
import sys
sys.path.insert(0, '/app')
from packages.export_utils.csv_export import create_csv_download
from packages.export_utils.pdf_export import export_to_pdf, generate_pdf_metric_cards, generate_pdf_table

def build_operations_dashboard(selected_line: str = None):
    """Operations Dashboard screen with line selector and detailed metrics"""
    
    # Fetch all lines for selector
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT DISTINCT line_id, line_name
                FROM oee_line_shift
                ORDER BY line_id
            """))
            all_lines = [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error fetching lines: {e}")
        all_lines = []
    
    # Default to first line if none selected
    if not selected_line and all_lines:
        selected_line = all_lines[0]['line_id']
    
    # Create containers for dynamic content
    line_selector_container = ui.row().classes('w-full gap-2 mb-4')
    
    @ui.refreshable
    def content_container():
        """Refreshable content container for line data"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Select a production line to view details').classes('text-gray-400')
    
    def load_line_data(line_id: str):
        """Load and display data for selected line"""
        
        # Fetch line data
        try:
            with engine.connect() as conn:
                # Get current shift data (most recent date)
                line_data = conn.execute(text("""
                    SELECT 
                        line_id, line_name,
                        oee, availability, performance, quality,
                        date, shift
                    FROM oee_line_shift
                    WHERE line_id = :line_id
                    ORDER BY date DESC, shift DESC
                    LIMIT 1
                """), {"line_id": line_id}).fetchone()
                
            # Get station performance in separate connection (table may not exist)
            station_data = []
            try:
                with engine.connect() as conn:
                    station_data = conn.execute(text("""
                        SELECT 
                            station_id,
                            AVG(oee) as avg_oee,
                            AVG(availability) as avg_avail,
                            COUNT(*) as shifts
                        FROM oee_station_shift
                        WHERE line_id = :line_id
                          AND date >= CURRENT_DATE - INTERVAL '7 days'
                        GROUP BY station_id
                        ORDER BY avg_oee DESC
                    """), {"line_id": line_id}).fetchall()
            except:
                pass  # Station data is optional
            
            with engine.connect() as conn:
                # Get top losses
                loss_data = conn.execute(text("""
                    SELECT 
                        loss_category,
                        SUM(duration_min) as total_minutes,
                        COUNT(*) as occurrences
                    FROM oee_downtime_events
                    WHERE line_id = :line_id
                      AND date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY loss_category
                    ORDER BY total_minutes DESC
                    LIMIT 5
                """), {"line_id": line_id}).fetchall()
                
                # Get recent issues
                recent_issues = conn.execute(text("""
                    SELECT 
                        description as station_id, loss_category,
                        duration_min as duration_minutes, start_timestamp
                    FROM oee_downtime_events
                    WHERE line_id = :line_id
                      AND date >= CURRENT_DATE - INTERVAL '1 day'
                    ORDER BY start_timestamp DESC
                    LIMIT 10
                """), {"line_id": line_id}).fetchall()
                
        except Exception as e:
            print(f"Error loading line data: {e}")
            line_data = None
            station_data = []
            loss_data = []
            recent_issues = []
        
        # Rebuild the content container with new data
        @content_container
        def display_line_content():
            with ui.column().classes('w-full gap-4'):
                if not line_data:
                    ui.label('No data available for this line').classes('text-gray-400')
                    return
                
                line_dict = dict(line_data._mapping)
                line_name = line_dict.get('line_name', line_id)
                
                # Top section: Real-time status and KPIs
                with ui.row().classes('w-full gap-4'):
                    # Current shift KPIs
                    with ui.card().classes('flex-1 bg-gray-800 border border-gray-700 p-6'):
                        ui.label(f'{line_name} - Current Shift Performance').classes('text-lg font-semibold text-white mb-4')
                        
                        with ui.grid(columns=4).classes('w-full gap-4'):
                            _kpi_card('OEE', line_dict.get('oee', 0), 'speed', 'teal')
                            _kpi_card('Availability', line_dict.get('availability', 0), 'bolt', 'blue')
                            _kpi_card('Performance', line_dict.get('performance', 0), 'trending_up', 'green')
                            _kpi_card('Quality', line_dict.get('quality', 0), 'verified', 'purple')
                
                # Quick stats
                with ui.card().classes('w-80 bg-gray-800 border border-gray-700 p-6'):
                    ui.label('Quick Stats').classes('text-lg font-semibold text-white mb-4')
                    
                    with ui.column().classes('gap-3'):
                        with ui.row().classes('justify-between'):
                            ui.label('Active Issues').classes('text-sm text-gray-400')
                            ui.label(str(len([i for i in recent_issues if i[3]]))).classes('text-xl font-bold text-red-400')
                        
                        with ui.row().classes('justify-between'):
                            ui.label('Stations').classes('text-sm text-gray-400')
                            ui.label(str(len(station_data))).classes('text-xl font-bold text-white')
                        
                        with ui.row().classes('justify-between'):
                            ui.label('Last 7 Days').classes('text-sm text-gray-400')
                            ui.label(f"{line_dict.get('date', 'N/A')}").classes('text-sm text-gray-300')
                
                # Middle section: Station performance and Top losses
                with ui.row().classes('w-full gap-4'):
                    # Station Performance
                    with ui.card().classes('flex-1 bg-gray-800 border border-gray-700 p-6'):
                        ui.label('Station Performance (7-day avg)').classes('text-lg font-semibold text-white mb-4')
                        
                        if station_data:
                            with ui.column().classes('gap-3 w-full'):
                                for station in station_data:
                                    station_dict = dict(station._mapping)
                                    station_id = station_dict.get('station_id', '')
                                    oee = station_dict.get('avg_oee', 0)
                                    pct = round(oee * 100)
                                
                                    # Color based on performance
                                    if oee >= 0.85:
                                        bar_color = 'bg-green-500'
                                    elif oee >= 0.75:
                                        bar_color = 'bg-yellow-400'
                                    else:
                                        bar_color = 'bg-red-500'
                                    
                                    with ui.row().classes('items-center gap-3 w-full'):
                                        ui.label(station_id).classes('text-sm text-white w-24')
                                        with ui.element('div').classes('flex-1 h-6 bg-gray-700 rounded-full overflow-hidden'):
                                            with ui.element('div').classes(f'{bar_color} h-6 rounded-full transition-all flex items-center justify-end pr-2').style(f'width: {pct}%'):
                                                if pct > 20:
                                                    ui.label(f'{pct}%').classes('text-xs font-semibold text-white')
                                        if pct <= 20:
                                            ui.label(f'{pct}%').classes('text-xs text-gray-400 w-12')
                        else:
                            ui.label('No station data available').classes('text-sm text-gray-400')
                    
                    # Top Losses
                    with ui.card().classes('flex-1 bg-gray-800 border border-gray-700 p-6'):
                        ui.label('Top Losses (Last 7 Days)').classes('text-lg font-semibold text-white mb-4')
                    
                    if loss_data:
                        total_loss_time = sum(dict(loss._mapping).get('total_minutes', 0) for loss in loss_data)
                        
                        with ui.column().classes('gap-3 w-full'):
                            for loss in loss_data:
                                loss_dict = dict(loss._mapping)
                                category = loss_dict.get('loss_category', 'Unknown')
                                minutes = loss_dict.get('total_minutes', 0)
                                count = loss_dict.get('occurrences', 0)
                                
                                pct = round((minutes / total_loss_time * 100) if total_loss_time > 0 else 0)
                                hours = minutes / 60
                                
                                with ui.column().classes('gap-1 w-full'):
                                    with ui.row().classes('justify-between items-center'):
                                        ui.label(category).classes('text-sm text-white')
                                        ui.label(f'{hours:.1f}h ({count}x)').classes('text-xs text-gray-400')
                                    
                                    with ui.element('div').classes('w-full h-2 bg-gray-700 rounded-full overflow-hidden'):
                                        ui.element('div').classes('bg-red-500 h-2 rounded-full').style(f'width: {pct}%')
                        ui.label('No loss data available').classes('text-sm text-gray-400')
                
                # Bottom section: Recent issues and Quick actions
                with ui.row().classes('w-full gap-4'):
                    # Recent Issues
                    with ui.card().classes('flex-1 bg-gray-800 border border-gray-700 p-6'):
                        ui.label('Recent Issues (Last 24h)').classes('text-lg font-semibold text-white mb-4')
                        
                        if recent_issues:
                            with ui.column().classes('gap-2 max-h-96 overflow-auto'):
                                for issue in recent_issues:
                                    issue_dict = dict(issue._mapping) if hasattr(issue, '_mapping') else dict(zip(['station_id', 'loss_category', 'duration_minutes', 'start_timestamp'], issue))
                                    station = issue_dict.get('station_id', '')
                                    category = issue_dict.get('loss_category', '')
                                    duration = issue_dict.get('duration_minutes', 0)
                                    
                                    # Severity color
                                    if category in ['Equipment Failure', 'Material Shortage']:
                                        severity_color = 'bg-red-500'
                                    elif category in ['Changeover', 'Reduced Speed']:
                                        severity_color = 'bg-yellow-400'
                                    else:
                                        severity_color = 'bg-blue-400'
                                    
                                    with ui.card().classes('bg-gray-900 border border-gray-700 p-3'):
                                        with ui.row().classes('items-center gap-3 w-full'):
                                            ui.element('div').classes(f'h-3 w-3 rounded-full {severity_color}')
                                            
                                            with ui.column().classes('flex-1 gap-0'):
                                                ui.label(f'{station} - {category}').classes('text-sm font-semibold text-white')
                                                ui.label(f'{duration:.0f} minutes').classes('text-xs text-gray-400')
                        else:
                            ui.label('No recent issues').classes('text-sm text-gray-400')
                    
                    # Quick Actions
                    with ui.card().classes('w-80 bg-gray-800 border border-gray-700 p-6'):
                        ui.label('Quick Actions').classes('text-lg font-semibold text-white mb-4')
                    
                    def export_line_report():
                        """Export current line data to CSV"""
                        if not line_data or not station_data:
                            ui.notify('No data to export', type='warning')
                            return
                        
                        # Prepare CSV data
                        csv_data = []
                        for station in station_data:
                            csv_data.append({
                                'Station': station[0],
                                'OEE (%)': round(station[1] * 100, 2),
                                'Availability (%)': round(station[2] * 100, 2),
                                'Performance (%)': round(station[3] * 100, 2),
                                'Quality (%)': round(station[4] * 100, 2),
                                'Units Produced': station[5],
                                'Good Units': station[6]
                            })
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"line_{line_id}_report_{timestamp}.csv"
                        csv_content = create_csv_download(csv_data, filename)
                        
                        ui.download(csv_content, filename)
                        ui.notify(f'Line {line_id} report exported', type='positive')
                    
                    with ui.column().classes('gap-3 w-full'):
                        ui.button('Report Issue', icon='report_problem').classes('w-full bg-red-600 hover:bg-red-700 text-white').props('no-caps')
                        ui.button('Request Maintenance', icon='build').classes('w-full bg-yellow-600 hover:bg-yellow-700 text-white').props('no-caps')
                        ui.button('View Detailed Analytics', icon='analytics').classes('w-full bg-teal-600 hover:bg-teal-700 text-white').props('no-caps')
                        ui.button('Export Report', icon='download', on_click=export_line_report).classes('w-full bg-gray-700 hover:bg-gray-600 text-white').props('no-caps')
        
        # Refresh the content container
        display_line_content.refresh()
    
    # Build line selector buttons
    with line_selector_container:
        ui.label('Select Production Line:').classes('text-sm font-semibold text-white self-center')
        
        for line in all_lines:
            line_id = line['line_id']
            line_name = line.get('line_name', line_id)
            
            is_selected = line_id == selected_line
            btn_classes = 'bg-teal-600 text-white' if is_selected else 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            
            ui.button(
                line_name,
                on_click=lambda lid=line_id: load_line_data(lid)
            ).classes(f'{btn_classes} px-4 py-2').props('no-caps')
    
    # Initialize the content container
    content_container()
    
    # Load initial data
    load_line_data(selected_line)


def _kpi_card(label: str, value: float, icon: str, color: str):
    """Render a KPI card with icon"""
    pct = round(value * 100)
    
    color_map = {
        'teal': 'text-teal-400',
        'blue': 'text-blue-400',
        'green': 'text-green-400',
        'purple': 'text-purple-400'
    }
    icon_color = color_map.get(color, 'text-gray-400')
    
    with ui.column().classes('items-center gap-2'):
        ui.icon(icon).classes(f'text-4xl {icon_color}')
        ui.label(f'{pct}%').classes('text-3xl font-bold text-white')
        ui.label(label).classes('text-xs uppercase text-gray-400')
