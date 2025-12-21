"""
Live Monitoring Screen
Real-time production metrics and alerts
"""
from nicegui import ui
import asyncio


def build_live_monitoring():
    """Live monitoring dashboard with real-time updates"""
    
    ui.label('Live Production Monitoring').classes('text-2xl font-bold text-white mb-4')
    
    # Status indicator
    status_container = ui.row().classes('mb-4 items-center gap-4')
    metrics_container = ui.row().classes('w-full gap-4 mb-4')
    lines_container = ui.column().classes('w-full gap-3')
    
    with status_container:
        with ui.card().classes('bg-gray-800 border border-gray-700 p-4'):
            with ui.row().classes('items-center gap-3'):
                status_icon = ui.icon('wifi').classes('text-green-400 text-2xl animate-pulse')
                status_label = ui.label('Connected to live stream').classes('text-white font-semibold')
                last_update = ui.label('Last update: --:--:--').classes('text-gray-400 text-sm ml-4')
    
    # Summary metrics
    with metrics_container:
        total_lines_card = _create_metric_card('Total Lines', '0', 'factory', 'blue')
        avg_oee_card = _create_metric_card('Avg OEE', '0%', 'speed', 'teal')
        alerts_card = _create_metric_card('Active Alerts', '0', 'warning', 'orange')
    
    # Live data update function
    def update_live_data():
        """Update live data - called by timer"""
        from sqlalchemy import text
        from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine
        from datetime import datetime
        
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                # Get most recent data (latest available, looking back 7 days)
                result = conn.execute(text("""
                    SELECT 
                        line_id, line_name,
                        oee, availability, performance, quality,
                        total_units_produced, good_units,
                        date, shift
                    FROM oee_line_shift
                    WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY date DESC, shift DESC, line_id
                    LIMIT 6
                """))
                
                lines_data = [dict(row._mapping) for row in result]
                
                # Get alerts
                alerts_result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM maintenance_alerts
                    WHERE current_status = 'active'
                """))
                
                alert_count = alerts_result.fetchone()[0]
            
            # Update summary metrics
            total_lines_card['value'].set_text(str(len(lines_data)))
            avg_oee = sum(l['oee'] for l in lines_data) / len(lines_data) if lines_data else 0
            avg_oee_card['value'].set_text(f"{avg_oee*100:.1f}%")
            alerts_card['value'].set_text(str(alert_count))
            
            # Update timestamp
            last_update.set_text(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            
            # Update lines display
            lines_container.clear()
            with lines_container:
                if not lines_data:
                    ui.label('No production data available').classes('text-gray-400')
                else:
                    for line in lines_data:
                        _render_live_line_card(line)
            
            # Make icon pulse
            status_icon.classes('text-green-400 text-2xl animate-pulse', remove='text-red-400')
            status_label.set_text('Connected to live stream')
            
        except Exception as e:
            print(f"Error updating live data: {e}")
            import traceback
            traceback.print_exc()
            status_icon.classes('text-red-400 text-2xl', remove='text-green-400 animate-pulse')
            status_label.set_text('Connection error')
    
    # Create timer for updates every 5 seconds
    ui.timer(5.0, update_live_data)
    
    # Trigger first update immediately
    update_live_data()


def _create_metric_card(label: str, initial_value: str, icon: str, color: str):
    """Create a metric card with updatable value"""
    color_map = {
        'blue': 'text-blue-400',
        'teal': 'text-teal-400',
        'orange': 'text-orange-400',
        'green': 'text-green-400',
    }
    
    text_color = color_map.get(color, 'text-white')
    
    with ui.card().classes('bg-gray-800 border border-gray-700 p-4 flex-1'):
        with ui.row().classes('items-center gap-3'):
            ui.icon(icon).classes(f'{text_color} text-3xl')
            with ui.column().classes('gap-1'):
                value_label = ui.label(initial_value).classes(f'text-2xl font-bold {text_color}')
                ui.label(label).classes('text-xs text-gray-400')
    
    return {'value': value_label, 'label': label}


def _render_live_line_card(line_data):
    """Render a live updating line card"""
    oee = line_data['oee']
    oee_pct = oee * 100
    
    # Color based on OEE
    if oee >= 0.85:
        border_color = 'border-green-600'
        oee_color = 'text-green-400'
    elif oee >= 0.75:
        border_color = 'border-yellow-600'
        oee_color = 'text-yellow-400'
    elif oee >= 0.65:
        border_color = 'border-orange-600'
        oee_color = 'text-orange-400'
    else:
        border_color = 'border-red-600'
        oee_color = 'text-red-400'
    
    with ui.card().classes(f'bg-gray-800 border-2 {border_color} p-4 w-full'):
        with ui.row().classes('items-center justify-between w-full'):
            # Line info
            with ui.column().classes('gap-1'):
                ui.label(f"{line_data['line_id']} - {line_data['line_name']}").classes('text-white font-bold')
                ui.label(f"📦 Units: {line_data['total_units_produced']} | ✅ Good: {line_data['good_units']}").classes('text-sm text-gray-300')
            
            # OEE metrics
            with ui.row().classes('gap-4'):
                with ui.column().classes('items-center'):
                    ui.label(f"{oee_pct:.1f}%").classes(f'text-2xl font-bold {oee_color}')
                    ui.label('OEE').classes('text-xs text-gray-400')
                
                with ui.column().classes('items-center'):
                    ui.label(f"{line_data['availability']*100:.1f}%").classes('text-lg text-blue-400')
                    ui.label('Avail').classes('text-xs text-gray-400')
                
                with ui.column().classes('items-center'):
                    ui.label(f"{line_data['performance']*100:.1f}%").classes('text-lg text-green-400')
                    ui.label('Perf').classes('text-xs text-gray-400')
                
                with ui.column().classes('items-center'):
                    ui.label(f"{line_data['quality']*100:.1f}%").classes('text-lg text-purple-400')
                    ui.label('Qual').classes('text-xs text-gray-400')


def render_live_monitoring_screen():
    """Render the live monitoring screen"""
    with ui.column().classes('w-full p-6 gap-4'):
        build_live_monitoring()
