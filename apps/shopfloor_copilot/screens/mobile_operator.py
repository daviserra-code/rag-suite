from nicegui import ui
from sqlalchemy import text
from datetime import datetime

from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine

def render_mobile_operator():
    """Mobile operator interface for floor workers."""
    
    # Database connection
    engine = get_db_engine()
    
    # Helper functions (defined first to avoid UnboundLocalError)
    def scan_equipment(equipment_input, equipment_info):
        """Simulate QR code scanning."""
        with engine.connect() as conn:
            # Get random equipment from station data
            equipment = conn.execute(text("""
                SELECT DISTINCT equipment_id, station_name 
                FROM oee_station_shift 
                WHERE equipment_id IS NOT NULL 
                ORDER BY RANDOM() 
                LIMIT 1
            """)).fetchone()
            
            if equipment:
                equipment_input.set_value(equipment.equipment_id)
                display_equipment_info(equipment.equipment_id, equipment.station_name, equipment_info)
                ui.notify(f'Scanned: {equipment.equipment_id}', type='positive')
            else:
                ui.notify('No equipment found', type='warning')
    
    def display_equipment_info(equipment_id, station_name, container):
        """Display equipment information."""
        container.clear()
        with container:
            with ui.card().classes('w-full bg-blue-50'):
                with ui.row().classes('w-full items-center gap-2'):
                    ui.icon('precision_manufacturing', size='lg').classes('text-blue')
                    with ui.column().classes('gap-0'):
                        ui.label(f'Equipment: {equipment_id}').classes('text-lg font-bold')
                        ui.label(f'Station: {station_name}').classes('text-sm text-grey-7')
    
    def submit_issue_report(line_id, category, description, severity, equipment_id, status_label, line_select, category_select, description_input, equipment_input, recent_reports):
        """Submit issue report to database."""
        if not line_id or not category:
            ui.notify('Please select line and issue type', type='warning')
            return
        
        if not description or len(description.strip()) < 10:
            ui.notify('Please provide a detailed description (at least 10 characters)', type='warning')
            return
        
        try:
            with engine.connect() as conn:
                # Insert into shift_issues table
                # Generate unique issue_id
                result = conn.execute(text("""
                    INSERT INTO shift_issues 
                    (issue_id, line_id, issue_type, description, severity, reported_by, reported_at, status)
                    VALUES 
                    ('ISS-' || TO_CHAR(NOW(), 'YYYYMMDD-HH24MISS') || '-' || LPAD(FLOOR(RANDOM() * 1000)::TEXT, 3, '0'), 
                     :line_id, :category, :description, :severity, 'Mobile Operator', NOW(), 'open')
                    RETURNING issue_id
                """), {
                    'line_id': line_id,
                    'category': category,
                    'description': description,
                    'severity': severity
                })
                conn.commit()
            
            status_label.text = '✅ Issue reported successfully!'
            status_label.classes('text-green font-bold')
            ui.notify('Issue reported successfully!', type='positive')
            
            # Clear form
            line_select.set_value(None)
            category_select.set_value(None)
            description_input.set_value('')
            equipment_input.set_value('')
            
            # Refresh recent reports
            load_recent_reports(recent_reports)
            
        except Exception as e:
            status_label.text = f'❌ Error: {str(e)}'
            status_label.classes('text-red font-bold')
            ui.notify(f'Error submitting report: {str(e)}', type='negative')
    
    def load_recent_reports(container):
        """Load recent reports from today."""
        container.clear()
        
        with engine.connect() as conn:
            reports = conn.execute(text("""
                SELECT 
                    si.issue_id,
                    ls.line_name,
                    si.issue_type,
                    si.description,
                    si.severity,
                    si.reported_at,
                    si.status
                FROM shift_issues si
                JOIN (SELECT DISTINCT line_id, line_name FROM oee_line_shift) ls ON si.line_id = ls.line_id
                WHERE DATE(si.reported_at) = CURRENT_DATE
                ORDER BY si.reported_at DESC
                LIMIT 5
            """)).fetchall()
        
        with container:
            if not reports:
                ui.label('No reports today').classes('text-grey-6 italic')
            else:
                for report in reports:
                    severity_colors = {
                        'Low': 'blue',
                        'Medium': 'orange',
                        'High': 'deep-orange',
                        'Critical': 'red'
                    }
                    color = severity_colors.get(report.severity, 'grey')
                    
                    with ui.card().classes(f'w-full border-l-4 border-{color}'):
                        with ui.row().classes('w-full items-start gap-2'):
                            ui.icon('report', size='md').classes(f'text-{color}')
                            with ui.column().classes('gap-1 flex-1'):
                                with ui.row().classes('w-full items-center gap-2'):
                                    ui.label(report.issue_type).classes('font-bold')
                                    ui.badge(report.severity, color=color)
                                    ui.badge(report.status, color='grey' if report.status == 'open' else 'green')
                                ui.label(report.line_name).classes('text-sm text-grey-7')
                                ui.label(report.description[:100] + ('...' if len(report.description) > 100 else '')).classes('text-sm')
                                ui.label(report.reported_at.strftime('%H:%M')).classes('text-xs text-grey-6')
    
    def show_my_reports():
        """Show operator's reports."""
        ui.notify('My Reports view - Coming soon', type='info')
    
    def show_shift_notes():
        """Show shift notes."""
        ui.notify('Shift Notes view - Coming soon', type='info')
    
    def show_procedures():
        """Show procedures and SOPs."""
        ui.notify('Procedures library - Coming soon', type='info')
    
    def show_contacts():
        """Show emergency contacts."""
        ui.notify('Contact list - Coming soon', type='info')
    
    # Mobile-optimized container
    with ui.column().classes('w-full max-w-2xl mx-auto p-4 gap-4'):
        
        # Header
        with ui.card().classes('w-full bg-primary text-white'):
            ui.label('Operator Interface').classes('text-2xl font-bold')
            ui.label('Quick Access for Floor Workers').classes('text-sm opacity-80')
        
        # QR Code Scanner Section
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center gap-2'):
                ui.icon('qr_code_scanner', size='lg').classes('text-primary')
                ui.label('Equipment Scanner').classes('text-xl font-bold')
            
            ui.separator()
            
            # Equipment ID input (simulated QR scan)
            equipment_input = ui.input('Equipment ID', placeholder='Scan or enter equipment ID').classes('w-full')
            equipment_input.props('size=lg')
            
            # Quick scan buttons
            with ui.row().classes('w-full gap-2 flex-wrap'):
                ui.button('📷 Scan QR Code', on_click=lambda: scan_equipment(equipment_input, equipment_info)).classes('flex-1 min-w-[150px]').props('size=lg')
                ui.button('⌨️ Manual Entry', on_click=lambda: equipment_input.set_value('')).classes('flex-1 min-w-[150px]').props('size=lg outline')
            
            # Equipment info display
            equipment_info = ui.column().classes('w-full')
        
        # Quick Issue Reporting Section
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center gap-2'):
                ui.icon('report_problem', size='lg').classes('text-orange')
                ui.label('Report Issue').classes('text-xl font-bold')
            
            ui.separator()
            
            # Line selection
            with engine.connect() as conn:
                lines = conn.execute(text("SELECT DISTINCT line_id, line_name FROM oee_line_shift ORDER BY line_name")).fetchall()
            
            line_select = ui.select(
                {row.line_id: row.line_name for row in lines},
                label='Production Line',
                with_input=True
            ).classes('w-full').props('size=lg')
            
            # Issue category
            issue_categories = {
                'Equipment Breakdown': '🔧 Equipment Breakdown',
                'Quality Issue': '❌ Quality Issue',
                'Material Shortage': '📦 Material Shortage',
                'Safety Concern': '⚠️ Safety Concern',
                'Process Problem': '⚙️ Process Problem',
                'Tooling Issue': '🔨 Tooling Issue',
                'Other': '📝 Other'
            }
            
            category_select = ui.select(
                issue_categories,
                label='Issue Type',
                with_input=True
            ).classes('w-full').props('size=lg')
            
            # Quick description
            description_input = ui.textarea('Description', placeholder='Briefly describe the issue...').classes('w-full')
            description_input.props('rows=4 size=lg')
            
            # Severity
            severity_select = ui.select(
                ['Low', 'Medium', 'High', 'Critical'],
                label='Severity',
                value='Medium'
            ).classes('w-full').props('size=lg')
            
            # Photo attachment placeholder
            with ui.row().classes('w-full gap-2'):
                ui.icon('photo_camera', size='lg').classes('text-grey')
                ui.label('Attach Photo (optional)').classes('text-base')
            ui.button('📸 Take Photo', on_click=lambda: ui.notify('Photo capture coming soon', type='info')).classes('w-full').props('size=lg outline')
            
            # Status message
            issue_status = ui.label('').classes('w-full text-center')
            
            # Submit button (defined after recent_reports)
            submit_button = ui.button(
                'Submit Issue Report',
                on_click=lambda: None
            ).classes('w-full bg-orange text-white').props('size=xl')
        
        # Quick Actions Section
        with ui.card().classes('w-full'):
            ui.label('Quick Actions').classes('text-xl font-bold')
            ui.separator()
            
            with ui.grid(columns=2).classes('w-full gap-3'):
                with ui.button(on_click=lambda: show_my_reports()).classes('h-24 flex-col gap-2').props('size=lg'):
                    ui.icon('list_alt', size='lg')
                    ui.label('My Reports')
                
                with ui.button(on_click=lambda: show_shift_notes()).classes('h-24 flex-col gap-2').props('size=lg'):
                    ui.icon('note', size='lg')
                    ui.label('Shift Notes')
                
                with ui.button(on_click=lambda: show_procedures()).classes('h-24 flex-col gap-2').props('size=lg'):
                    ui.icon('menu_book', size='lg')
                    ui.label('Procedures')
                
                with ui.button(on_click=lambda: show_contacts()).classes('h-24 flex-col gap-2').props('size=lg'):
                    ui.icon('contacts', size='lg')
                    ui.label('Contacts')
        
        # Recent Reports Section
        with ui.card().classes('w-full'):
            ui.label('Recent Reports (Today)').classes('text-xl font-bold')
            ui.separator()
            
            recent_reports = ui.column().classes('w-full gap-2')
            load_recent_reports(recent_reports)
        
        # Wire up submit button after recent_reports is defined
        submit_button.on_click(lambda: submit_issue_report(
            line_select.value,
            category_select.value,
            description_input.value,
            severity_select.value,
            equipment_input.value,
            issue_status,
            line_select,
            category_select,
            description_input,
            equipment_input,
            recent_reports
        ))
