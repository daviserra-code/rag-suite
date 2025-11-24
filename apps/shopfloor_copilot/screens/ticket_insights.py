from nicegui import ui
import plotly.graph_objects as go

def build_ticket_insights():
    """Ticket Insights screen - Analytics and similar fixes"""
    
    with ui.column().classes('w-full gap-4'):
        # Filters Row
        with ui.card().classes('sf-card'):
            with ui.row().classes('items-center gap-4'):
                ui.label('Filters').classes('font-bold')
                ui.select(['All Lines', 'Line M10', 'Line B02', 'Line C03', 'Line D01', 'Line SMT1', 'Line WC01'], value='All Lines', label='by Line').classes('w-48')
                ui.select(['All', 'Mechanical', 'Electrical'], value='Mechanical', label='Cause').classes('w-48')
                ui.chip('Sinter', icon='close').classes('sf-chip')
                ui.chip('File', icon='close').classes('sf-chip')
        
        # Charts Row
        with ui.row().classes('w-full gap-4'):
            # Cause Chart
            with ui.card().classes('sf-card flex-1'):
                ui.label('By Cause').classes('text-sm font-bold mb-2')
                
                # Simple bar chart data
                fig = go.Figure(data=[
                    go.Bar(name='X0', x=['A01', 'Cause', 'X'], y=[12, 8, 4], marker_color='#0F7C7C')
                ])
                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False
                )
                ui.plotly(fig).classes('w-full')
            
            # Timeline Chart  
            with ui.card().classes('sf-card flex-1'):
                ui.label('Timeline').classes('text-sm font-bold mb-2')
                
                fig = go.Figure(data=[
                    go.Scatter(x=['Tab', 'Apr', 'Mar', 'Apr'], y=[8, 12, 6, 10], 
                              mode='lines+markers', line=dict(color='#0F7C7C'))
                ])
                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False
                )
                ui.plotly(fig).classes('w-full')
        
        # Similar Past Fix
        with ui.card().classes('sf-card'):
            ui.label('Similar past fix').classes('text-lg font-bold mb-2')
            
            with ui.row().classes('items-center gap-4 mb-4'):
                ui.label('Moderate').classes('text-sm')
                ui.label('Confidence').classes('text-xs opacity-70')
                ui.linear_progress(value=0.6).classes('flex-grow')
            
            with ui.column().classes('gap-2'):
                ui.label('Similar past fix  Moderate ⓘ').classes('text-sm font-bold')
                
                with ui.row().classes('items-center gap-2'):
                    ui.label('Reduced tension').classes('text-sm')
                    ui.label('6 months ago').classes('text-xs opacity-70')
                    ui.button(icon='chevron_right').props('flat dense')
                
                ui.label('Fixed similarly 1 mitar    6 month ago    1 year ago').classes('text-xs opacity-70')
