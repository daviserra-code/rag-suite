"""
Predictive Maintenance Dashboard
Shows alerts, equipment health, and maintenance predictions
"""
from nicegui import ui
from sqlalchemy import text
from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine
from datetime import datetime, timedelta


def build_predictive_maintenance():
    """Predictive maintenance alerts and equipment health dashboard"""
    
    ui.label('Predictive Maintenance Dashboard').classes('text-2xl font-bold text-white mb-4')
    
    # Filter controls
    filter_container = ui.row().classes('mb-4 gap-4')
    alerts_container = ui.column().classes('w-full gap-4')
    
    with filter_container:
        with ui.card().classes('bg-gray-800 border border-gray-700 p-4'):
            with ui.row().classes('items-center gap-4'):
                ui.icon('filter_list').classes('text-blue-400 text-2xl')
                ui.label('Filters:').classes('text-white font-semibold')
                
                severity_filter = ui.select(
                    options={'all': 'All Severities', 'critical': 'Critical', 'high': 'High', 'medium': 'Medium', 'low': 'Low'},
                    value='all'
                ).props('dark outlined dense').classes('text-white').style('min-width: 150px')
                
                status_filter = ui.select(
                    options={'active': 'Active Only', 'all': 'All Statuses', 'acknowledged': 'Acknowledged', 'resolved': 'Resolved'},
                    value='active'
                ).props('dark outlined dense').classes('text-white').style('min-width: 150px')
    
    def load_maintenance_data(severity='all', status='active'):
        """Load and display maintenance alerts and equipment health"""
        alerts_container.clear()
        
        try:
            engine = get_db_engine()
            
            # Build query filters
            severity_clause = "" if severity == 'all' else f"AND severity = '{severity}'"
            status_clause = "AND current_status = 'active'" if status == 'active' else (
                "" if status == 'all' else f"AND current_status = '{status}'"
            )
            
            with engine.connect() as conn:
                # Get active alerts
                alerts_query = f"""
                    SELECT 
                        alert_id, line_id, station_id, equipment_name,
                        alert_type, severity, predicted_failure_date,
                        confidence_score, pattern_detected, recommended_action,
                        current_status, created_at
                    FROM maintenance_alerts
                    WHERE 1=1 {severity_clause} {status_clause}
                    ORDER BY 
                        CASE severity 
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        predicted_failure_date ASC
                    LIMIT 50
                """
                
                result = conn.execute(text(alerts_query))
                alerts = [dict(row._mapping) for row in result]
                
                # Get equipment health scores
                health_result = conn.execute(text("""
                    SELECT 
                        line_id, station_id, equipment_name,
                        health_score, mtbf_hours, failure_probability,
                        last_failure_date, cycles_since_maintenance
                    FROM equipment_health_score
                    WHERE calculated_at >= CURRENT_DATE
                    ORDER BY health_score ASC
                    LIMIT 10
                """))
                
                health_scores = [dict(row._mapping) for row in health_result]
            
            with alerts_container:
                # Summary cards at top
                with ui.row().classes('w-full gap-4 mb-4'):
                    critical_count = len([a for a in alerts if a['severity'] == 'critical'])
                    high_count = len([a for a in alerts if a['severity'] == 'high'])
                    medium_count = len([a for a in alerts if a['severity'] == 'medium'])
                    avg_health = sum(h['health_score'] for h in health_scores) / len(health_scores) if health_scores else 0
                    
                    _summary_card('Critical Alerts', critical_count, 'error', 'red')
                    _summary_card('High Priority', high_count, 'warning', 'orange')
                    _summary_card('Medium Priority', medium_count, 'info', 'yellow')
                    _summary_card('Avg Health Score', f"{avg_health:.1f}%", 'health_and_safety', 'teal')
                
                if not alerts:
                    with ui.card().classes('w-full bg-gray-800 border border-gray-700 p-6'):
                        ui.label('No maintenance alerts found').classes('text-gray-400')
                    return
                
                # Active alerts list
                with ui.card().classes('w-full bg-gray-800 border border-gray-700 p-6 mb-4'):
                    ui.label(f'Active Maintenance Alerts ({len(alerts)})').classes('text-xl font-bold text-white mb-4')
                    
                    for alert in alerts:
                        _render_alert_card(alert)
                
                # Equipment health section
                if health_scores:
                    with ui.card().classes('w-full bg-gray-800 border border-gray-700 p-6'):
                        ui.label('Equipment Health Status (Lowest Scores)').classes('text-xl font-bold text-white mb-4')
                        
                        with ui.column().classes('gap-3 w-full'):
                            for equipment in health_scores:
                                _render_health_item(equipment)
        
        except Exception as e:
            print(f"Error loading maintenance data: {e}")
            with alerts_container:
                ui.label(f'Error loading data: {str(e)}').classes('text-red-400')
    
    # Initial load
    load_maintenance_data()
    
    # Update on filter change
    severity_filter.on_value_change(lambda e: load_maintenance_data(e.value, status_filter.value))
    status_filter.on_value_change(lambda e: load_maintenance_data(severity_filter.value, e.value))


def _summary_card(label: str, value, icon: str, color: str):
    """Summary stat card"""
    color_map = {
        'red': ('bg-red-900', 'border-red-600', 'text-red-400'),
        'orange': ('bg-orange-900', 'border-orange-600', 'text-orange-400'),
        'yellow': ('bg-yellow-900', 'border-yellow-600', 'text-yellow-400'),
        'teal': ('bg-teal-900', 'border-teal-600', 'text-teal-400'),
    }
    
    bg, border, text = color_map.get(color, ('bg-gray-800', 'border-gray-600', 'text-white'))
    
    with ui.card().classes(f'{bg} border-2 {border} p-4 flex-1'):
        with ui.row().classes('items-center gap-3'):
            ui.icon(icon).classes(f'{text} text-3xl')
            with ui.column().classes('gap-1'):
                ui.label(str(value)).classes(f'text-2xl font-bold {text}')
                ui.label(label).classes('text-xs text-gray-400')


def _render_alert_card(alert):
    """Render individual alert card"""
    severity = alert['severity']
    
    severity_colors = {
        'critical': ('bg-red-900', 'border-red-600', 'text-red-400', 'error'),
        'high': ('bg-orange-900', 'border-orange-600', 'text-orange-400', 'warning'),
        'medium': ('bg-yellow-900', 'border-yellow-600', 'text-yellow-400', 'info'),
        'low': ('bg-blue-900', 'border-blue-600', 'text-blue-400', 'notifications'),
    }
    
    bg, border, text, icon = severity_colors.get(severity, ('bg-gray-800', 'border-gray-600', 'text-white', 'info'))
    
    days_until = (alert['predicted_failure_date'] - datetime.now().date()).days if alert['predicted_failure_date'] else None
    
    with ui.card().classes(f'{bg} border-2 {border} p-4 mb-3'):
        with ui.row().classes('items-start justify-between w-full'):
            with ui.column().classes('gap-2 flex-1'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon(icon).classes(f'{text} text-2xl')
                    ui.label(f"{alert['alert_id']} - {severity.upper()}").classes(f'text-lg font-bold {text}')
                    if days_until is not None:
                        ui.badge(f"{days_until}d", color='white').classes('ml-2')
                
                ui.label(f"🏭 {alert['line_id']} / {alert['station_id'] or 'Line Level'}").classes('text-white font-semibold')
                ui.label(f"⚙️  {alert['equipment_name']}").classes('text-white')
                
                ui.separator().classes('my-2 bg-gray-600')
                
                ui.label(f"📊 Pattern: {alert['pattern_detected']}").classes('text-sm text-gray-300')
                ui.label(f"💡 Action: {alert['recommended_action']}").classes('text-sm text-gray-200 font-semibold mt-1')
            
            with ui.column().classes('gap-1 items-end'):
                ui.label(f"{alert['confidence_score']:.0f}%").classes(f'text-xl font-bold {text}')
                ui.label('Confidence').classes('text-xs text-gray-400')
                
                if alert['predicted_failure_date']:
                    ui.label(str(alert['predicted_failure_date'])).classes('text-xs text-gray-300 mt-2')


def _render_health_item(equipment):
    """Render equipment health item"""
    health = equipment['health_score']
    
    if health >= 75:
        bar_color = 'bg-green-500'
        text_color = 'text-green-400'
    elif health >= 50:
        bar_color = 'bg-yellow-500'
        text_color = 'text-yellow-400'
    elif health >= 25:
        bar_color = 'bg-orange-500'
        text_color = 'text-orange-400'
    else:
        bar_color = 'bg-red-500'
        text_color = 'text-red-400'
    
    with ui.row().classes('items-center gap-3 w-full'):
        with ui.column().classes('gap-0 w-64'):
            ui.label(f"{equipment['line_id']}/{equipment['station_id']}").classes('text-sm text-white font-semibold')
            ui.label(equipment['equipment_name']).classes('text-xs text-gray-400')
        
        with ui.element('div').classes('flex-1 h-6 bg-gray-700 rounded-full overflow-hidden'):
            with ui.element('div').classes(f'{bar_color} h-6 rounded-full transition-all flex items-center justify-end pr-2').style(f'width: {health}%'):
                if health > 15:
                    ui.label(f'{health:.1f}%').classes('text-xs font-semibold text-white')
        
        if health <= 15:
            ui.label(f'{health:.1f}%').classes(f'text-xs {text_color} w-12')
        
        ui.label(f"MTBF: {equipment['mtbf_hours']:.0f}h").classes('text-xs text-gray-400 w-24')


def render_predictive_maintenance_screen():
    """Render the predictive maintenance screen"""
    with ui.column().classes('w-full p-6 gap-4'):
        build_predictive_maintenance()
