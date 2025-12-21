"""
Station Heatmap Visualization
Shows all stations across all lines with color-coded performance
"""
from nicegui import ui
from sqlalchemy import text
from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine
from datetime import datetime, timedelta
import plotly.graph_objects as go


def build_station_heatmap():
    """Station heatmap showing performance across all lines and stations"""
    
    ui.label('Station Performance Heatmap').classes('text-2xl font-bold text-white mb-4')
    
    # Time range selector in a styled card
    with ui.card().classes('bg-gray-800 border border-gray-700 p-4 mb-4'):
        with ui.row().classes('items-center gap-4'):
            ui.icon('calendar_today').classes('text-blue-400 text-2xl')
            ui.label('Time Range:').classes('text-white font-semibold')
            time_range = ui.select(
                options={7: 'Last 7 Days', 14: 'Last 14 Days', 30: 'Last 30 Days', 90: 'Last 90 Days'},
                value=7
            ).props('dark outlined dense').classes('text-white').style('min-width: 180px; background-color: #374151; border-color: #4B5563;')
    
    chart_container = ui.column().classes('w-full')
    
    def load_heatmap_data(days: int = 7):
        """Load and display station heatmap"""
        chart_container.clear()
        
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                # Get average OEE per station for the period
                query = text("""
                    SELECT 
                        line_id,
                        line_name,
                        station_id,
                        station_name,
                        AVG(oee) as avg_oee,
                        AVG(availability) as avg_avail,
                        AVG(performance) as avg_perf,
                        AVG(quality) as avg_qual,
                        COUNT(*) as shifts,
                        SUM(CASE WHEN main_issue IS NOT NULL THEN 1 ELSE 0 END) as issue_count
                    FROM oee_station_shift
                    WHERE date >= CURRENT_DATE - INTERVAL ':days days'
                    GROUP BY line_id, line_name, station_id, station_name
                    ORDER BY line_id, station_id
                """)
                # Replace the days parameter in the SQL string
                query_str = str(query).replace(':days', str(days))
                result = conn.execute(text(query_str))
                
                stations = [dict(row._mapping) for row in result]
            
            if not stations:
                with chart_container:
                    ui.label('No station data available').classes('text-gray-400')
                return
            
            # Organize data by line
            lines_data = {}
            for station in stations:
                line_id = station['line_id']
                if line_id not in lines_data:
                    lines_data[line_id] = {
                        'line_name': station['line_name'],
                        'stations': []
                    }
                lines_data[line_id]['stations'].append(station)
            
            with chart_container:
                # Create grid of station cards by line
                for line_id in sorted(lines_data.keys()):
                    line_info = lines_data[line_id]
                    
                    with ui.card().classes('w-full bg-gray-800 border border-gray-700 p-6 mb-4'):
                        ui.label(f"{line_info['line_name']} ({line_id})").classes('text-xl font-bold text-white mb-4')
                        
                        # Station cards in grid
                        with ui.grid(columns='repeat(auto-fill, minmax(200px, 1fr))').classes('gap-4 w-full'):
                            for station in line_info['stations']:
                                oee = station['avg_oee']
                                oee_pct = round(oee * 100, 1)
                                
                                # Color coding based on OEE
                                if oee >= 0.85:
                                    bg_color = 'bg-green-900 border-green-600'
                                    text_color = 'text-green-400'
                                elif oee >= 0.75:
                                    bg_color = 'bg-yellow-900 border-yellow-600'
                                    text_color = 'text-yellow-400'
                                elif oee >= 0.65:
                                    bg_color = 'bg-orange-900 border-orange-600'
                                    text_color = 'text-orange-400'
                                else:
                                    bg_color = 'bg-red-900 border-red-600'
                                    text_color = 'text-red-400'
                                
                                with ui.card().classes(f'{bg_color} border-2 p-4 cursor-pointer hover:scale-105 transition-transform'):
                                    ui.label(station['station_name']).classes('text-sm font-semibold text-white mb-2')
                                    ui.label(station['station_id']).classes('text-xs text-gray-400 mb-3')
                                    
                                    ui.label(f"{oee_pct}%").classes(f'text-3xl font-bold {text_color}')
                                    ui.label('OEE').classes('text-xs text-gray-400')
                                    
                                    ui.separator().classes('my-2 bg-gray-600')
                                    
                                    with ui.row().classes('justify-between w-full text-xs'):
                                        with ui.column().classes('gap-1'):
                                            ui.label(f"A: {round(station['avg_avail']*100)}%").classes('text-gray-300')
                                            ui.label(f"P: {round(station['avg_perf']*100)}%").classes('text-gray-300')
                                        with ui.column().classes('gap-1'):
                                            ui.label(f"Q: {round(station['avg_qual']*100)}%").classes('text-gray-300')
                                            ui.label(f"Issues: {station['issue_count']}").classes('text-gray-300')
                
                # Overall statistics
                with ui.card().classes('w-full bg-gray-800 border border-gray-700 p-6 mt-4'):
                    ui.label('Overall Station Statistics').classes('text-xl font-bold text-white mb-4')
                    
                    total_stations = len(stations)
                    avg_oee = sum(s['avg_oee'] for s in stations) / total_stations
                    
                    # Count stations by performance tier
                    excellent = len([s for s in stations if s['avg_oee'] >= 0.85])
                    good = len([s for s in stations if 0.75 <= s['avg_oee'] < 0.85])
                    fair = len([s for s in stations if 0.65 <= s['avg_oee'] < 0.75])
                    poor = len([s for s in stations if s['avg_oee'] < 0.65])
                    
                    with ui.row().classes('gap-8'):
                        _stat_card('Total Stations', total_stations, 'precision_manufacturing', 'blue')
                        _stat_card('Average OEE', f"{round(avg_oee*100, 1)}%", 'speed', 'teal')
                        _stat_card('Excellent (≥85%)', excellent, 'verified', 'green')
                        _stat_card('Good (75-84%)', good, 'check_circle', 'yellow')
                        _stat_card('Fair (65-74%)', fair, 'warning', 'orange')
                        _stat_card('Poor (<65%)', poor, 'error', 'red')
        
        except Exception as e:
            print(f"Error loading heatmap: {e}")
            with chart_container:
                ui.label(f'Error loading data: {str(e)}').classes('text-red-400')
    
    # Initial load
    load_heatmap_data(7)
    
    # Update on time range change
    time_range.on_value_change(lambda e: load_heatmap_data(e.value))


def _stat_card(label: str, value, icon: str, color: str):
    """Helper to create stat card"""
    color_map = {
        'blue': 'text-blue-400',
        'teal': 'text-teal-400',
        'green': 'text-green-400',
        'yellow': 'text-yellow-400',
        'orange': 'text-orange-400',
        'red': 'text-red-400'
    }
    
    with ui.card().classes('bg-gray-700 p-4'):
        with ui.row().classes('items-center gap-3'):
            ui.icon(icon).classes(f'{color_map.get(color, "text-white")} text-3xl')
            with ui.column().classes('gap-1'):
                ui.label(str(value)).classes(f'text-2xl font-bold {color_map.get(color, "text-white")}')
                ui.label(label).classes('text-xs text-gray-400')


def render_station_heatmap_screen():
    """Render the station heatmap screen"""
    with ui.column().classes('w-full p-6 gap-4'):
        build_station_heatmap()
