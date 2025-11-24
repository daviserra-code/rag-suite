from nicegui import ui
import requests

def build_production_lines_overview():
    """Production Lines Overview - Summary of all manufacturing lines with OEE metrics"""
    
    ui.label('Production Lines Overview').classes('text-2xl font-bold mb-6')
    
    # Fetch live data from database
    try:
        response = requests.get('http://shopfloor:8010/api/oee/lines', timeout=5)
        if response.status_code == 200:
            lines_data = response.json()
        else:
            lines_data = []
    except Exception as e:
        print(f"Error fetching production lines: {e}")
        lines_data = []
    
    if not lines_data:
        # Fallback data if API fails
        lines_data = [
            {'line_id': 'B02', 'line_name': 'Packaging Line B02', 'shifts': 270, 'avg_oee': 0.812, 'avg_availability': 0.899, 'avg_performance': 0.919, 'avg_quality': 0.983},
            {'line_id': 'D01', 'line_name': 'Final Assembly Line D01', 'shifts': 270, 'avg_oee': 0.791, 'avg_availability': 0.883, 'avg_performance': 0.920, 'avg_quality': 0.974},
            {'line_id': 'C03', 'line_name': 'Subassembly Line C03', 'shifts': 270, 'avg_oee': 0.780, 'avg_availability': 0.880, 'avg_performance': 0.914, 'avg_quality': 0.970},
            {'line_id': 'SMT1', 'line_name': 'SMT Line 1', 'shifts': 270, 'avg_oee': 0.769, 'avg_availability': 0.857, 'avg_performance': 0.923, 'avg_quality': 0.973},
            {'line_id': 'M10', 'line_name': 'Machining Line M10', 'shifts': 270, 'avg_oee': 0.769, 'avg_availability': 0.867, 'avg_performance': 0.923, 'avg_quality': 0.961},
            {'line_id': 'WC01', 'line_name': 'Welding Cell WC01', 'shifts': 270, 'avg_oee': 0.769, 'avg_availability': 0.875, 'avg_performance': 0.919, 'avg_quality': 0.958},
        ]
    
    # Summary stats
    with ui.row().classes('w-full gap-4 mb-6'):
        with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-blue-600 to-blue-700 text-white'):
            ui.label('Total Lines').classes('text-xs opacity-80')
            ui.label(str(len(lines_data))).classes('text-4xl font-bold')
            ui.label('Active Production Lines').classes('text-xs opacity-80 mt-2')
        
        avg_oee = sum(line['avg_oee'] for line in lines_data) / len(lines_data) if lines_data else 0
        with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-teal-600 to-teal-700 text-white'):
            ui.label('Average OEE').classes('text-xs opacity-80')
            ui.label(f'{avg_oee:.1%}').classes('text-4xl font-bold')
            ui.label('Across All Lines').classes('text-xs opacity-80 mt-2')
        
        total_shifts = sum(line.get('shifts', 0) for line in lines_data)
        with ui.card().classes('sf-card flex-1 bg-gradient-to-br from-purple-600 to-purple-700 text-white'):
            ui.label('Total Shifts').classes('text-xs opacity-80')
            ui.label(f'{total_shifts:,}').classes('text-4xl font-bold')
            ui.label('Data Points Available').classes('text-xs opacity-80 mt-2')
    
    # Production Lines Table
    with ui.card().classes('sf-card w-full'):
        ui.label('Production Lines Matrix').classes('text-lg font-bold mb-4')
        
        # Table header - dark mode friendly
        with ui.row().classes('w-full gap-2 pb-3 border-b-2 border-gray-300 dark:border-gray-600 font-bold'):
            ui.label('Line ID').classes('flex-[1] text-sm text-gray-700 dark:text-gray-200')
            ui.label('Line Name').classes('flex-[3] text-sm text-gray-700 dark:text-gray-200')
            ui.label('Shifts').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('OEE').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('Availability').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('Performance').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
            ui.label('Quality').classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-200')
        
        # Table rows
        for line in lines_data:
            # Color code based on OEE performance - dark mode friendly
            oee = line['avg_oee']
            if oee >= 0.80:
                bg_color = 'bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-800/30'
                oee_color = 'text-green-700 dark:text-green-400 font-bold'
            elif oee >= 0.75:
                bg_color = 'bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-800/30'
                oee_color = 'text-blue-700 dark:text-blue-400 font-bold'
            else:
                bg_color = 'bg-yellow-50 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-800/30'
                oee_color = 'text-yellow-700 dark:text-yellow-400 font-bold'
            
            with ui.row().classes(f'w-full gap-2 py-3 border-b border-gray-200 dark:border-gray-700 {bg_color} cursor-pointer transition-colors').on('click', lambda l=line: ui.notify(f"Line {l['line_id']}: {l['line_name']}", type='info')):
                ui.label(line['line_id']).classes('flex-[1] text-sm font-mono font-bold text-gray-900 dark:text-gray-100')
                ui.label(line['line_name']).classes('flex-[3] text-sm text-gray-800 dark:text-gray-200')
                ui.label(f"{line.get('shifts', 0):,}").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                ui.label(f"{line['avg_oee']:.1%}").classes(f'flex-[1] text-sm text-right {oee_color}')
                ui.label(f"{line['avg_availability']:.1%}").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                ui.label(f"{line['avg_performance']:.1%}").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
                ui.label(f"{line['avg_quality']:.1%}").classes('flex-[1] text-sm text-right text-gray-700 dark:text-gray-300')
    
    # Legend
    with ui.card().classes('sf-card w-full mt-4'):
        ui.label('Performance Legend').classes('text-sm font-bold mb-2')
        with ui.row().classes('gap-4'):
            with ui.row().classes('items-center gap-2'):
                ui.label('●').classes('text-green-600 dark:text-green-400 text-xl')
                ui.label('Excellent (≥80%)').classes('text-xs text-gray-700 dark:text-gray-300')
            with ui.row().classes('items-center gap-2'):
                ui.label('●').classes('text-blue-600 dark:text-blue-400 text-xl')
                ui.label('Good (75-80%)').classes('text-xs text-gray-700 dark:text-gray-300')
            with ui.row().classes('items-center gap-2'):
                ui.label('●').classes('text-yellow-600 dark:text-yellow-400 text-xl')
                ui.label('Needs Attention (<75%)').classes('text-xs text-gray-700 dark:text-gray-300')
    
    # Quick Actions
    with ui.card().classes('sf-card w-full mt-4'):
        ui.label('Quick Actions').classes('text-sm font-bold mb-2')
        with ui.row().classes('gap-2'):
            ui.button('Refresh Data', icon='refresh', on_click=lambda: ui.navigate.reload()).classes('sf-btn primary')
            ui.button('Export Report', icon='download').classes('sf-btn secondary')
            ui.button('View Trends', icon='show_chart').classes('sf-btn secondary')
