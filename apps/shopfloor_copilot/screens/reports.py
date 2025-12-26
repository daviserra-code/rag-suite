"""
Reporting Screen
Scheduled and on-demand report generation
"""
from nicegui import ui
from datetime import datetime, timedelta
import asyncio
import os
import sys

# Add root directory to path to import generate_report
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from generate_report import generate_executive_report


class ReportsScreen:
    """Reports management and generation interface"""
    
    def __init__(self):
        self.report_type = 'weekly'
        self.custom_days = 7
        self.generating = False
        self.last_report = None
        
    def render(self):
        """Render the reports screen"""
        
        with ui.column().classes('w-full gap-6 p-4'):
            # Header with better styling
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('📊 Executive Reports').classes('text-3xl font-bold text-gray-900')
                
                with ui.row().classes('gap-3'):
                    ui.button('📥 Download Last', 
                             on_click=self.download_last_report).classes('bg-teal-600 text-white hover:bg-teal-700').props('no-caps')
                    ui.button('🔄 Refresh', 
                             on_click=self.refresh_data).classes('bg-blue-600 text-white hover:bg-blue-700').props('no-caps')
            
            # Report Configuration Card with improved styling
            with ui.card().classes('w-full p-6 bg-gradient-to-br from-teal-50 to-cyan-50 border-2 border-teal-200'):
                ui.label('Report Configuration').classes('text-xl font-bold text-gray-900 mb-4')
                
                with ui.row().classes('w-full gap-6 items-start'):
                    # Report Type Selection with better text
                    with ui.column().classes('flex-1 gap-4'):
                        ui.label('Report Type').classes('text-base font-semibold text-gray-900')
                        
                        with ui.column().classes('gap-2'):
                            ui.radio(
                                ['daily', 'weekly', 'monthly', 'quarterly', 'annual', 'custom'],
                                value='weekly',
                                on_change=lambda e: self.update_report_type(e.value)
                            ).props('inline')
                            
                            # Custom days input (shown when custom is selected)
                            self.custom_days_input = ui.number(
                                label='Custom Days',
                                value=7,
                                min=1,
                                max=365,
                                on_change=lambda e: setattr(self, 'custom_days', int(e.value or 7))
                            ).classes('w-48').style('display: none;')
                    
                    # Quick Actions
                    with ui.column().classes('flex-1 gap-4'):
                        ui.label('Quick Actions').classes('text-sm font-medium text-gray-600')
                        
                        with ui.row().classes('gap-2 flex-wrap'):
                            ui.button('Yesterday', 
                                     on_click=lambda: self.generate_quick_report(1),
                                     color='teal').props('outline').classes('text-sm')
                            ui.button('Last 7 Days', 
                                     on_click=lambda: self.generate_quick_report(7),
                                     color='teal').props('outline').classes('text-sm')
                            ui.button('Last 30 Days', 
                                     on_click=lambda: self.generate_quick_report(30),
                                     color='teal').props('outline').classes('text-sm')
                            ui.button('Last 90 Days', 
                                     on_click=lambda: self.generate_quick_report(90),
                                     color='teal').props('outline').classes('text-sm')
                
                # Generate Button
                with ui.row().classes('w-full justify-center mt-6'):
                    self.generate_btn = ui.button(
                        '🎯 Generate Report',
                        on_click=self.generate_report,
                        color='teal'
                    ).props('size=lg').classes('px-12')
                    
                # Progress indicator
                self.progress_container = ui.row().classes('w-full justify-center mt-4').style('display: none;')
                with self.progress_container:
                    ui.spinner(size='lg', color='teal')
                    ui.label('Generating report...').classes('ml-4 text-gray-900 font-semibold')
            
            # Scheduled Reports Card with improved styling
            with ui.card().classes('w-full p-6 bg-gray-800 border-2 border-gray-600'):
                ui.label('Scheduled Reports').classes('text-xl font-bold text-white mb-4')
                
                with ui.column().classes('w-full gap-4'):
                    # Email Configuration
                    with ui.row().classes('w-full gap-4 items-center'):
                        ui.label('Email Recipients:').classes('text-base font-semibold text-gray-900 w-32')
                        self.email_input = ui.input(
                            placeholder='manager@company.com, director@company.com',
                            value=os.getenv('REPORT_EMAILS', '')
                        ).classes('flex-1')
                        ui.button('💾 Save', 
                                 on_click=self.save_email_config,
                                 color='teal').props('flat')
                    
                    # Schedule Configuration with better text
                    ui.label('Report Schedules').classes('text-base font-semibold text-gray-900 mt-4')
                    
                    schedules = [
                        {'type': 'Daily', 'time': '06:00', 'enabled': True, 'recipients': 3},
                        {'type': 'Weekly', 'time': 'Monday 08:00', 'enabled': True, 'recipients': 5},
                        {'type': 'Monthly', 'time': '1st day 09:00', 'enabled': True, 'recipients': 8},
                        {'type': 'Quarterly', 'time': '1st day 09:00', 'enabled': False, 'recipients': 12}
                    ]
                    
                    with ui.column().classes('w-full gap-3 mt-3'):
                        for schedule in schedules:
                            with ui.row().classes('w-full items-center p-4 bg-gray-900 rounded-lg gap-4 border border-gray-600'):
                                ui.switch(value=schedule['enabled']).props('color=teal')
                                
                                with ui.column().classes('flex-1 gap-1'):
                                    ui.label(f"{schedule['type']} Report").classes('font-semibold text-base text-gray-900')
                                    ui.label(f"⏰ {schedule['time']}").classes('text-sm text-gray-800')
                                
                                ui.label(f"👥 {schedule['recipients']} recipients").classes('text-sm text-gray-900 font-medium')
                                
                                ui.button(icon='settings', on_click=lambda: ui.notify('Schedule editor coming soon!')).props('flat dense')
            
            # Recent Reports Card
            with ui.card().classes('w-full p-6'):
                ui.label('Recent Reports').classes('text-lg font-semibold mb-4')
                
                # Mock recent reports
                recent = [
                    {'date': '2025-11-27 06:00', 'type': 'Daily', 'period': 'Nov 26', 'size': '847 KB'},
                    {'date': '2025-11-26 06:00', 'type': 'Daily', 'period': 'Nov 25', 'size': '831 KB'},
                    {'date': '2025-11-25 08:00', 'type': 'Weekly', 'period': 'Nov 18-24', 'size': '1.2 MB'},
                    {'date': '2025-11-25 06:00', 'type': 'Daily', 'period': 'Nov 24', 'size': '856 KB'},
                    {'date': '2025-11-24 06:00', 'type': 'Daily', 'period': 'Nov 23', 'size': '842 KB'}
                ]
                
                with ui.column().classes('w-full gap-1'):
                    for report in recent:
                        with ui.row().classes('w-full items-center p-3 hover:bg-gray-800 rounded cursor-pointer'):
                            # Icon based on type
                            icon_map = {
                                'Daily': '📄',
                                'Weekly': '📊',
                                'Monthly': '📈',
                                'Quarterly': '📉'
                            }
                            ui.label(icon_map.get(report['type'], '📄')).classes('text-2xl')
                            
                            with ui.column().classes('flex-1 gap-0 ml-3'):
                                ui.label(f"{report['type']} Report - {report['period']}").classes('font-medium text-sm')
                                ui.label(f"Generated: {report['date']}").classes('text-xs text-gray-500')
                            
                            ui.label(report['size']).classes('text-sm text-gray-600 mr-4')
                            
                            ui.button(icon='download', on_click=lambda: ui.notify('Downloading...')).props('flat dense color=teal')
            
            # Report Preview Card
            with ui.card().classes('w-full p-6').style('display: none;') as self.preview_card:
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    ui.label('Report Preview').classes('text-lg font-semibold')
                    ui.button('✖', on_click=lambda: self.preview_card.style('display: none;')).props('flat dense')
                
                self.preview_container = ui.column().classes('w-full')
    
    def update_report_type(self, report_type: str):
        """Update selected report type"""
        self.report_type = report_type
        
        # Show/hide custom days input
        if report_type == 'custom':
            self.custom_days_input.style('display: block;')
        else:
            self.custom_days_input.style('display: none;')
    
    async def generate_report(self):
        """Generate report with selected configuration"""
        if self.generating:
            ui.notify('Report generation already in progress', type='warning')
            return
        
        self.generating = True
        self.generate_btn.props('disable')
        self.progress_container.style('display: flex;')
        
        try:
            # Calculate date range
            end_date = datetime.now()
            
            if self.report_type == 'custom':
                days = self.custom_days
                report_type = f"{days}-day"
            else:
                type_days = {
                    'daily': 1,
                    'weekly': 7,
                    'monthly': 30,
                    'quarterly': 90,
                    'annual': 365
                }
                days = type_days[self.report_type]
                report_type = self.report_type
            
            start_date = end_date - timedelta(days=days)
            
            ui.notify(f'Generating {report_type} report ({start_date.date()} to {end_date.date()})...', 
                     type='info')
            
            # Generate report in background
            pdf_bytes = await asyncio.to_thread(
                generate_executive_report,
                start_date,
                end_date,
                report_type
            )
            
            self.last_report = pdf_bytes
            
            # Auto-download
            filename = f"operations_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            ui.download(pdf_bytes, filename)
            
            ui.notify(f'✅ Report generated successfully! ({len(pdf_bytes) / 1024:.1f} KB)', 
                     type='positive')
            
        except Exception as e:
            ui.notify(f'Error generating report: {str(e)}', type='negative')
            print(f"Report generation error: {e}")
        
        finally:
            self.generating = False
            self.generate_btn.props(remove='disable')
            self.progress_container.style('display: none;')
    
    async def generate_quick_report(self, days: int):
        """Generate a quick report for specified days"""
        self.custom_days = days
        self.report_type = 'custom'
        await self.generate_report()
    
    def download_last_report(self):
        """Download the last generated report"""
        if self.last_report:
            filename = f"operations_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            ui.download(self.last_report, filename)
            ui.notify('Downloading last report...', type='positive')
        else:
            ui.notify('No report available. Generate one first!', type='warning')
    
    def save_email_config(self):
        """Save email configuration"""
        # In production, this would save to database or config file
        ui.notify('Email configuration saved!', type='positive')
    
    def refresh_data(self):
        """Refresh report data"""
        ui.notify('Refreshing reports list...', type='info')


def render_reports_screen():
    """Render the reports screen"""
    screen = ReportsScreen()
    screen.render()
