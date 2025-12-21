import os
import httpx
from nicegui import ui, app
from datetime import datetime, timedelta
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from typing import Dict, List

# Database connection
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "ragdb")

engine = create_engine(f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def get_oee_component_trends(line_id: str, days: int) -> Dict:
    """Get Availability, Performance, Quality trends from unified view (prefers OPC Studio data)"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    date,
                    shift,
                    AVG(availability) * 100 as availability,
                    AVG(performance) * 100 as performance,
                    AVG(quality) * 100 as quality,
                    AVG(oee) * 100 as oee
                FROM v_runtime_kpi
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY date, shift
                ORDER BY date, shift
            """), {"line_id": line_id})
            
            rows = result.fetchall()
            return {
                'dates': [f"{row[0]} {row[1]}" for row in rows],
                'availability': [float(row[2] or 0) for row in rows],
                'performance': [float(row[3] or 0) for row in rows],
                'quality': [float(row[4] or 0) for row in rows],
                'oee': [float(row[5] or 0) for row in rows]
            }
    except Exception as e:
        print(f"Error fetching OEE components: {e}")
        return {'dates': [], 'availability': [], 'performance': [], 'quality': [], 'oee': []}

def get_downtime_by_category(line_id: str, days: int) -> Dict:
    """Get downtime minutes by loss category from unified events view"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    date,
                    loss_category,
                    SUM(duration_min) as total_minutes
                FROM v_runtime_events
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY date, loss_category
                ORDER BY date, loss_category
            """), {"line_id": line_id})
            
            rows = result.fetchall()
            
            # Organize by category
            categories = {}
            for row in rows:
                date_str = str(row[0])
                category = row[1]
                minutes = float(row[2] or 0)
                
                if category not in categories:
                    categories[category] = {'dates': [], 'values': []}
                categories[category]['dates'].append(date_str)
                categories[category]['values'].append(minutes)
            
            return categories
    except Exception as e:
        print(f"Error fetching downtime by category: {e}")
        return {}

def get_scrap_rate_trend(line_id: str, days: int) -> Dict:
    """Get scrap rate trend from unified view"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    date,
                    shift,
                    CASE 
                        WHEN SUM(total_units_produced) > 0 
                        THEN (SUM(scrap_units)::float / SUM(total_units_produced)::float * 100)
                        ELSE 0 
                    END as scrap_rate_pct
                FROM v_runtime_kpi
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY date, shift
                ORDER BY date, shift
            """), {"line_id": line_id})
            
            rows = result.fetchall()
            return {
                'dates': [f"{row[0]} {row[1]}" for row in rows],
                'scrap_rate': [float(row[2] or 0) for row in rows]
            }
    except Exception as e:
        print(f"Error fetching scrap rate: {e}")
        return {'dates': [], 'scrap_rate': []}

def get_shift_comparison(line_id: str, days: int) -> Dict:
    """Get OEE by shift for heatmap from unified view"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    date,
                    shift,
                    AVG(oee) * 100 as avg_oee
                FROM v_runtime_kpi
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY date, shift
                ORDER BY date, shift
            """), {"line_id": line_id})
            
            rows = result.fetchall()
            
            # Organize by shift
            shifts = {'M': [], 'A': [], 'N': []}
            dates = []
            
            current_date = None
            for row in rows:
                date_str = str(row[0])
                shift = row[1]
                oee = float(row[2] or 0)
                
                if date_str != current_date:
                    dates.append(date_str)
                    current_date = date_str
                
                if shift in shifts:
                    shifts[shift].append(oee)
            
            return {'dates': dates, 'shifts': shifts}
    except Exception as e:
        print(f"Error fetching shift comparison: {e}")
        return {'dates': [], 'shifts': {'M': [], 'A': [], 'N': []}}

def get_kpi_summary(line_id: str, days: int) -> Dict:
    """Get KPI summary values for cards"""
    try:
        with engine.connect() as conn:
            # Get average OEE and latest shift info from unified view
            oee_result = conn.execute(text(f"""
                SELECT 
                    AVG(oee) * 100 as avg_oee
                FROM v_runtime_kpi
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
            """), {"line_id": line_id}).fetchone()
            
            # Get latest shift separately
            latest_result = conn.execute(text("""
                SELECT date, shift
                FROM v_runtime_kpi
                WHERE line_id = :line_id
                ORDER BY date DESC, shift DESC
                LIMIT 1
            """), {"line_id": line_id}).fetchone()
            
            # Get average downtime (as proxy for MTTR) from unified events
            mttr_result = conn.execute(text(f"""
                SELECT 
                    AVG(duration_min) as avg_mttr,
                    COUNT(*) as failure_count
                FROM v_runtime_events
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
                  AND loss_category = 'Equipment Failure'
            """), {"line_id": line_id}).fetchone()
            
            # Get quality rate (proxy for FPY) from unified view
            quality_result = conn.execute(text(f"""
                SELECT 
                    AVG(quality) * 100 as avg_quality,
                    SUM(scrap_units) as total_scrap
                FROM v_runtime_kpi
                WHERE line_id = :line_id
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
            """), {"line_id": line_id}).fetchone()
            
            return {
                'avg_oee': float(oee_result[0] or 0) if oee_result else 0,
                'latest_date': str(latest_result[0]) if latest_result and latest_result[0] else 'N/A',
                'latest_shift': latest_result[1] if latest_result and latest_result[1] else 'N/A',
                'avg_mttr': float(mttr_result[0] or 0) if mttr_result else 0,
                'failure_count': int(mttr_result[1] or 0) if mttr_result else 0,
                'avg_quality': float(quality_result[0] or 0) if quality_result else 0,
                'total_scrap': int(quality_result[1] or 0) if quality_result else 0
            }
    except Exception as e:
        print(f"Error fetching KPI summary: {e}")
        return {
            'avg_oee': 0, 'latest_date': 'N/A', 'latest_shift': 'N/A',
            'avg_mttr': 0, 'failure_count': 0,
            'avg_quality': 0, 'total_scrap': 0
        }

def build_kpi_dashboard():
    """Interactive KPI Dashboard with OEE/FPY/MTTR metrics and AI chat"""
    
    # State - validate line selection
    valid_lines = ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01']
    if 'kpi_line' not in app.storage.user or app.storage.user['kpi_line'] not in valid_lines:
        app.storage.user['kpi_line'] = 'M10'
    if 'kpi_days' not in app.storage.user:
        app.storage.user['kpi_days'] = 7
    if 'kpi_data' not in app.storage.user:
        app.storage.user['kpi_data'] = None
    
    async def load_kpi_data():
        """Refresh KPI data display"""
        try:
            # Refresh UI components
            kpi_cards.refresh()
            charts_container.refresh()
        except Exception as e:
            ui.notify(f'Error loading KPI data: {str(e)}', type='negative')
    
    def update_line(new_line: str):
        """Update selected line"""
        app.storage.user['kpi_line'] = new_line
        kpi_cards.refresh()
        charts_container.refresh()
    
    def update_days(new_days: int):
        """Update time range"""
        app.storage.user['kpi_days'] = new_days
        kpi_cards.refresh()
        charts_container.refresh()
    
    @ui.refreshable
    def kpi_cards():
        """KPI summary cards"""
        line = app.storage.user['kpi_line']
        days = app.storage.user['kpi_days']
        
        data = get_kpi_summary(line, days)
        
        with ui.row().classes('w-full gap-4'):
            # OEE Card
            with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-teal-600 to-teal-700 text-white'):
                ui.label('OEE').classes('text-xs opacity-80')
                ui.label(f"{data['avg_oee']:.1f}%").classes('text-4xl font-bold')
                ui.label(f"Last: {data['latest_date']} {data['latest_shift']}").classes('text-xs opacity-70')
            
            # Quality (FPY proxy) Card
            with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-blue-600 to-blue-700 text-white'):
                ui.label('Quality Rate').classes('text-xs opacity-80')
                ui.label(f"{data['avg_quality']:.1f}%").classes('text-4xl font-bold')
                ui.label(f"Scrap: {data['total_scrap']} units").classes('text-xs opacity-70')
            
            # MTTR Card
            with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-orange-600 to-orange-700 text-white'):
                ui.label('Avg Downtime (MTTR)').classes('text-xs opacity-80')
                ui.label(f"{data['avg_mttr']:.1f}min").classes('text-4xl font-bold')
                ui.label(f"Failures: {data['failure_count']}").classes('text-xs opacity-70')
    
    @ui.refreshable
    def charts_container():
        """Plotly charts for trends"""
        line = app.storage.user['kpi_line']
        days = app.storage.user['kpi_days']
        
        # Row 1: OEE Components (Availability, Performance, Quality)
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('sf-card flex-1'):
                ui.label('OEE Components Trend').classes('text-sm font-bold mb-2')
                
                components_data = get_oee_component_trends(line, days)
                
                fig_components = go.Figure()
                fig_components.add_trace(go.Scatter(
                    x=components_data['dates'],
                    y=components_data['availability'],
                    mode='lines+markers',
                    name='Availability',
                    line=dict(color='#10B981', width=2),
                    marker=dict(size=6)
                ))
                fig_components.add_trace(go.Scatter(
                    x=components_data['dates'],
                    y=components_data['performance'],
                    mode='lines+markers',
                    name='Performance',
                    line=dict(color='#3B82F6', width=2),
                    marker=dict(size=6)
                ))
                fig_components.add_trace(go.Scatter(
                    x=components_data['dates'],
                    y=components_data['quality'],
                    mode='lines+markers',
                    name='Quality',
                    line=dict(color='#F59E0B', width=2),
                    marker=dict(size=6)
                ))
                fig_components.add_trace(go.Scatter(
                    x=components_data['dates'],
                    y=components_data['oee'],
                    mode='lines+markers',
                    name='OEE',
                    line=dict(color='#0F7C7C', width=3),
                    marker=dict(size=8)
                ))
                fig_components.update_layout(
                    height=300,
                    margin=dict(l=40, r=20, t=20, b=80),
                    xaxis=dict(title='Date & Shift', tickangle=-45),
                    yaxis=dict(title='Percentage (%)', range=[0, 100]),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    hovermode='x unified'
                )
                ui.plotly(fig_components).classes('w-full')
        
        # Row 2: Downtime by Category (Stacked) + Scrap Rate
        with ui.row().classes('w-full gap-4'):
            # Downtime by Loss Category
            with ui.card().classes('sf-card flex-1'):
                ui.label('Downtime by Loss Category').classes('text-sm font-bold mb-2')
                
                downtime_data = get_downtime_by_category(line, days)
                
                fig_downtime = go.Figure()
                colors = {
                    'Equipment Failure': '#EF4444',
                    'Changeover': '#F59E0B',
                    'Minor Stop': '#FCD34D',
                    'Reduced Speed': '#3B82F6',
                    'Quality Rework': '#8B5CF6',
                    'Material Shortage': '#EC4899',
                    'Planned Maintenance': '#10B981'
                }
                
                for category, data in downtime_data.items():
                    fig_downtime.add_trace(go.Bar(
                        x=data['dates'],
                        y=data['values'],
                        name=category,
                        marker_color=colors.get(category, '#6B7280')
                    ))
                
                fig_downtime.update_layout(
                    height=300,
                    margin=dict(l=40, r=20, t=20, b=80),
                    xaxis=dict(title='Date', tickangle=-45),
                    yaxis=dict(title='Downtime (minutes)'),
                    barmode='stack',
                    legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.02),
                    hovermode='x unified'
                )
                ui.plotly(fig_downtime).classes('w-full')
            
            # Scrap Rate Trend
            with ui.card().classes('sf-card flex-1'):
                ui.label('Scrap Rate Trend').classes('text-sm font-bold mb-2')
                
                scrap_data = get_scrap_rate_trend(line, days)
                
                fig_scrap = go.Figure()
                fig_scrap.add_trace(go.Scatter(
                    x=scrap_data['dates'],
                    y=scrap_data['scrap_rate'],
                    mode='lines+markers',
                    name='Scrap Rate',
                    line=dict(color='#DC2626', width=3),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(220, 38, 38, 0.1)'
                ))
                fig_scrap.update_layout(
                    height=300,
                    margin=dict(l=40, r=20, t=20, b=80),
                    xaxis=dict(title='Date & Shift', tickangle=-45),
                    yaxis=dict(title='Scrap Rate (%)'),
                    showlegend=False,
                    hovermode='x unified'
                )
                ui.plotly(fig_scrap).classes('w-full')
        
        # Row 3: Shift Comparison Heatmap
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('sf-card w-full'):
                ui.label('OEE by Shift (Heatmap)').classes('text-sm font-bold mb-2')
                
                shift_data = get_shift_comparison(line, days)
                
                fig_shifts = go.Figure()
                
                # Create heatmap data
                z_data = [
                    shift_data['shifts'].get('M', []),
                    shift_data['shifts'].get('A', []),
                    shift_data['shifts'].get('N', [])
                ]
                
                fig_shifts.add_trace(go.Heatmap(
                    z=z_data,
                    x=shift_data['dates'],
                    y=['Morning', 'Afternoon', 'Night'],
                    colorscale='RdYlGn',
                    zmid=75,
                    zmin=0,
                    zmax=100,
                    text=[[f"{val:.1f}%" for val in row] for row in z_data],
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    colorbar=dict(title="OEE %")
                ))
                
                fig_shifts.update_layout(
                    height=250,
                    margin=dict(l=80, r=20, t=20, b=80),
                    xaxis=dict(title='Date', tickangle=-45),
                    yaxis=dict(title='Shift')
                )
                ui.plotly(fig_shifts).classes('w-full')
    
    # Main layout
    with ui.column().classes('w-full gap-4'):
        # Filters
        with ui.card().classes('sf-card'):
            with ui.row().classes('w-full items-center gap-4'):
                ui.label('📊 KPI Dashboard').classes('text-lg font-bold')
                
                ui.select(
                    ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01'],
                    value=app.storage.user['kpi_line'],
                    label='Line',
                    on_change=lambda e: update_line(e.value)
                ).classes('w-32')
                
                ui.select(
                    [7, 14, 30],
                    value=app.storage.user['kpi_days'],
                    label='Days',
                    on_change=lambda e: update_days(e.value)
                ).classes('w-32')
                
                ui.button('Refresh', icon='refresh', on_click=load_kpi_data).classes('sf-btn')
        
        # KPI Cards
        kpi_cards()
        
        # Charts
        charts_container()
        
        # Recent Downtimes
        with ui.card().classes('sf-card'):
            ui.label('Recent Downtimes').classes('text-sm font-bold mb-3')
            
            # Mock downtime data
            downtimes = [
                {'time': '2h ago', 'station': 'S110', 'duration': '32 min', 'reason': 'Conveyor belt misalignment'},
                {'time': '5h ago', 'station': 'S120', 'duration': '12 min', 'reason': 'Scheduled tool replacement'},
                {'time': '1d ago', 'station': 'S110', 'duration': '28 min', 'reason': 'Material shortage'},
            ]
            
            for dt in downtimes:
                with ui.row().classes('w-full items-center gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded mb-2'):
                    ui.label(dt['time']).classes('text-xs w-16 opacity-70')
                    ui.label(dt['station']).classes('text-xs w-12 font-bold')
                    ui.label(dt['duration']).classes('text-xs w-16 text-orange-600 dark:text-orange-400 font-bold')
                    ui.label(dt['reason']).classes('text-xs flex-grow')
    
    # Load initial data
    ui.timer(0.1, load_kpi_data, once=True)
