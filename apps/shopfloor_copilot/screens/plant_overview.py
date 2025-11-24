from nicegui import ui, app
from sqlalchemy import text
from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine
from datetime import datetime, timedelta

def build_plant_overview(on_line_click=None):
    """Build the graphical Plant Overview page with traffic lights and live alarms"""
    
    # Fetch latest OEE data directly from database
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    line_id,
                    line_name,
                    COUNT(*) as shifts,
                    MIN(date) as start_date,
                    MAX(date) as end_date,
                    AVG(oee) as avg_oee,
                    AVG(availability) as avg_availability,
                    AVG(performance) as avg_performance,
                    AVG(quality) as avg_quality
                FROM oee_line_shift
                GROUP BY line_id, line_name
                ORDER BY avg_oee DESC
            """))
            lines_data = [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error fetching OEE data from database: {e}")
        lines_data = []
    
    # Calculate overall KPIs
    if lines_data:
        overall_oee = sum(line.get('avg_oee', 0) for line in lines_data) / len(lines_data)
        overall_avail = sum(line.get('avg_availability', 0) for line in lines_data) / len(lines_data)
        overall_perf = sum(line.get('avg_performance', 0) for line in lines_data) / len(lines_data)
        overall_qual = sum(line.get('avg_quality', 0) for line in lines_data) / len(lines_data)
    else:
        overall_oee = overall_avail = overall_perf = overall_qual = 0
    
    # Fetch recent downtime events for live alarms
    active_alarms = []
    try:
        with engine.connect() as conn:
            # Get most recent downtime events from the last 2 hours
            result = conn.execute(text("""
                SELECT 
                    e.line_id,
                    e.description as station_id,
                    e.loss_category,
                    e.start_timestamp,
                    e.start_timestamp + (e.duration_min || ' minutes')::interval as end_timestamp,
                    e.duration_min as duration_minutes,
                    l.line_name
                FROM oee_downtime_events e
                LEFT JOIN oee_line_shift l ON e.line_id = l.line_id AND e.date = l.date
                WHERE e.date >= CURRENT_DATE - INTERVAL '1 day'
                ORDER BY e.start_timestamp DESC
                LIMIT 10
            """))
            
            for row in result:
                row_dict = dict(row._mapping)
                line_id = row_dict.get('line_id', '')
                station_id = row_dict.get('station_id', '')
                category = row_dict.get('loss_category', 'Unknown')
                duration_min = row_dict.get('duration_minutes', 0)
                
                # Determine severity based on category
                if category in ['Equipment Failure', 'Material Shortage']:
                    severity = 'critical'
                elif category in ['Changeover', 'Reduced Speed', 'Quality Rework']:
                    severity = 'warning'
                else:
                    severity = 'info'
                
                # Format time since
                if duration_min < 60:
                    since = f'{int(duration_min)} min'
                else:
                    hours = int(duration_min / 60)
                    since = f'{hours}h {int(duration_min % 60)}m'
                
                active_alarms.append({
                    'line': line_id,
                    'station': station_id,
                    'severity': severity,
                    'category': category,
                    'since': since,
                    'duration_min': duration_min
                })
    except Exception as e:
        print(f"Error fetching alarms from database: {e}")
        # Fallback to empty list if query fails
        active_alarms = []
    
    with ui.column().classes('w-full h-full gap-0 bg-gray-950'):
        # Top bar - Global snapshot
        with ui.row().classes('w-full p-4 bg-gray-900 border-b border-gray-800 items-center justify-between'):
            with ui.column().classes('gap-1'):
                ui.label('Plant Overview – Digital Twin').classes('text-2xl font-semibold text-white')
                ui.label('Live OEE & alarms across all production lines').classes('text-sm text-gray-400')
            
            # Overall KPIs
            with ui.row().classes('gap-4'):
                _kpi_tile('OEE', overall_oee)
                _kpi_tile('Availability', overall_avail)
                _kpi_tile('Performance', overall_perf)
                _kpi_tile('Quality', overall_qual)
        
        # Main content area
        with ui.row().classes('flex-1 w-full overflow-hidden bg-gray-950'):
            # Left: Plant flow map
            with ui.column().classes('flex-1 p-6 overflow-auto'):
                ui.label('Plant Flow').classes('text-lg font-semibold text-white mb-3')
                
                # Grid of line cards
                with ui.grid(columns=3).classes('w-full gap-4'):
                    for line in lines_data:
                        line_id = line.get('line_id', '')
                        line_name = line.get('line_name', line_id)
                        oee = line.get('avg_oee', 0)
                        
                        # Determine status based on OEE
                        if oee >= 0.85:
                            status = 'green'
                            status_label = 'Running'
                        elif oee >= 0.75:
                            status = 'yellow'
                            status_label = 'Attention'
                        else:
                            status = 'red'
                            status_label = 'Alarm'
                        
                        # Get main loss category
                        main_loss = _get_main_loss_for_line(line_id)
                        
                        _line_card(line_id, line_name, oee, main_loss, status, status_label, on_click=on_line_click)
            
            # Right: Live alarms panel
            with ui.column().classes('w-96 border-l border-gray-800 p-6 bg-gray-900'):
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    ui.label('Live Alarms').classes('text-lg font-semibold text-white')
                    ui.label(f'{len(active_alarms)} active').classes('text-sm text-gray-400')
                
                with ui.column().classes('gap-3 overflow-auto flex-1'):
                    for alarm in active_alarms:
                        _alarm_row(alarm)


def _kpi_tile(label: str, value: float):
    """Render a KPI tile in the top bar"""
    pct = round(value * 100)
    with ui.column().classes('bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 gap-0'):
        ui.label(label).classes('text-xs uppercase tracking-wide text-gray-400')
        ui.label(f'{pct}%').classes('text-xl font-semibold text-white')


def _line_card(line_id: str, line_name: str, oee: float, main_loss: str, status: str, status_label: str, on_click=None):
    """Render a production line card with traffic light indicator"""
    pct = round(oee * 100)
    
    # Status color mapping
    status_colors = {
        'green': 'bg-green-500',
        'yellow': 'bg-yellow-400',
        'red': 'bg-red-500'
    }
    bar_color = status_colors.get(status, 'bg-gray-500')
    
    card = ui.card().classes('bg-gray-800 border border-gray-700 hover:border-gray-600 transition-colors cursor-pointer shadow-sm')
    
    if on_click:
        card.on('click', lambda: on_click(line_id))
    
    with card:
        with ui.column().classes('gap-3 p-2'):
            # Header with traffic light
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column().classes('gap-0'):
                    ui.label(line_name).classes('font-semibold text-sm text-white')
                    with ui.row().classes('items-center gap-1'):
                        ui.label('Status:').classes('text-xs text-gray-400')
                        ui.label(status_label).classes('text-xs font-medium text-white')
                
                # Traffic light (vertical)
                with ui.column().classes('gap-1 items-center'):
                    _traffic_light_circle(status == 'red', 'bg-red-500')
                    _traffic_light_circle(status == 'yellow', 'bg-yellow-400')
                    _traffic_light_circle(status == 'green', 'bg-green-500')
            
            # OEE bar
            with ui.column().classes('w-full gap-1'):
                with ui.row().classes('w-full justify-between'):
                    ui.label('OEE').classes('text-xs text-gray-400')
                    ui.label(f'{pct}%').classes('text-xs text-gray-400')
                
                # Progress bar
                with ui.element('div').classes('w-full h-2 bg-gray-600 rounded-full overflow-hidden'):
                    ui.element('div').classes(f'{bar_color} h-2 rounded-full transition-all').style(f'width: {pct}%')
            
            # Main loss
            with ui.row().classes('items-center gap-1'):
                ui.label('Main loss:').classes('text-xs text-gray-400')
                ui.label(main_loss).classes('text-xs text-white')


def _traffic_light_circle(active: bool, color_class: str):
    """Render a single traffic light circle"""
    if active:
        # Active: colored with glow and pulse
        ui.element('div').classes(f'h-3 w-3 rounded-full {color_class} shadow-lg animate-pulse')
    else:
        # Inactive: gray
        ui.element('div').classes('h-3 w-3 rounded-full bg-gray-600 dark:bg-gray-700')


def _alarm_row(alarm: dict):
    """Render an alarm row in the live alarms panel"""
    severity = alarm.get('severity', 'info')
    line = alarm.get('line', '')
    station = alarm.get('station', '')
    category = alarm.get('category', '')
    since = alarm.get('since', '')
    
    # Severity color mapping
    severity_colors = {
        'critical': 'bg-red-500',
        'warning': 'bg-yellow-400',
        'info': 'bg-blue-400'
    }
    dot_color = severity_colors.get(severity, 'bg-gray-500')
    
    with ui.card().classes('bg-gray-800 border border-gray-700 p-3 shadow-sm'):
        with ui.row().classes('gap-3 items-start'):
            # Severity indicator dot
            ui.element('div').classes(f'h-2 w-2 rounded-full {dot_color} animate-pulse mt-1')
            
            # Alarm details
            with ui.column().classes('flex-1 gap-0'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label(f'{line} – {station}').classes('text-xs font-semibold text-white')
                    ui.label(f'{since} ago').classes('text-xs text-gray-400')
                ui.label(category).classes('text-xs text-gray-300')


def _get_main_loss_for_line(line_id: str) -> str:
    """Get the main loss category for a line from recent downtime events"""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            # Get most frequent loss category from last 7 days
            result = conn.execute(text("""
                SELECT loss_category, COUNT(*) as count
                FROM oee_downtime_events
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY loss_category
                ORDER BY count DESC
                LIMIT 1
            """), {"line_id": line_id})
            
            row = result.fetchone()
            if row:
                return row[0]
    except Exception as e:
        print(f"Error fetching main loss for line {line_id}: {e}")
    
    return 'Minor Stop'  # Fallback
