"""
5 Whys Analysis Templates
Structured root cause analysis using the 5 Whys methodology
"""
from nicegui import ui
from datetime import datetime, timedelta
from sqlalchemy import text

from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine


# Common 5 Whys templates for manufacturing issues
ANALYSIS_TEMPLATES = {
    "Equipment Breakdown": {
        "description": "Use this template when analyzing equipment failures",
        "example_whys": [
            "Why did the machine stop? - The circuit breaker tripped",
            "Why did the breaker trip? - Electrical overload detected",
            "Why was there an overload? - Motor was drawing excessive current",
            "Why was the motor drawing too much current? - Bearings were seized",
            "Why did the bearings seize? - Insufficient lubrication maintenance"
        ],
        "root_cause_example": "Inadequate preventive maintenance schedule"
    },
    "Quality Defect": {
        "description": "Use this template when analyzing quality issues",
        "example_whys": [
            "Why are products defective? - Parts are out of specification",
            "Why are parts out of spec? - Cutting tool is worn",
            "Why is the tool worn? - It exceeded its service life",
            "Why did it exceed service life? - Tool change schedule not followed",
            "Why wasn't the schedule followed? - No tracking system in place"
        ],
        "root_cause_example": "Missing tool lifecycle management system"
    },
    "Material Shortage": {
        "description": "Use this template for supply chain issues",
        "example_whys": [
            "Why did we run out of materials? - Reorder came late",
            "Why did the reorder come late? - Order placed after stock depleted",
            "Why wasn't it ordered earlier? - No low stock alert",
            "Why is there no alert? - Inventory system not configured",
            "Why isn't it configured? - System setup incomplete"
        ],
        "root_cause_example": "Incomplete inventory management system setup"
    },
    "Operator Error": {
        "description": "Use this template for human error analysis",
        "example_whys": [
            "Why did the operator make an error? - Incorrect procedure followed",
            "Why was incorrect procedure used? - Operator wasn't trained on new process",
            "Why wasn't operator trained? - Training not scheduled",
            "Why wasn't training scheduled? - No training tracking system",
            "Why is there no system? - Training management not prioritized"
        ],
        "root_cause_example": "Lack of formal training management process"
    },
    "Process Deviation": {
        "description": "Use this template for process control issues",
        "example_whys": [
            "Why did process parameters drift? - Temperature controller malfunctioned",
            "Why did controller malfunction? - Sensor readings inaccurate",
            "Why were readings inaccurate? - Sensor calibration overdue",
            "Why was calibration overdue? - No calibration schedule maintained",
            "Why no schedule? - Calibration tracking not implemented"
        ],
        "root_cause_example": "Missing calibration management system"
    }
}


def why_analysis_screen():
    """5 Whys analysis tool with templates"""
    
    engine = get_db_engine()
    
    with ui.column().classes('w-full p-4 gap-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('5 Whys Root Cause Analysis').classes('text-3xl font-bold')
            with ui.row().classes('gap-2'):
                ui.button('View Templates', icon='library_books', on_click=lambda: show_templates_dialog())
                ui.button('Analysis History', icon='history', on_click=lambda: show_history())
        
        # Introduction card
        with ui.card().classes('w-full p-4 bg-blue-50 border-l-4 border-blue-500'):
            ui.label('📘 What is 5 Whys Analysis?').classes('text-lg font-bold mb-2')
            ui.label('The 5 Whys is an iterative interrogative technique used to explore cause-and-effect relationships. By asking "Why?" repeatedly (typically 5 times), you can drill down to the root cause of a problem.').classes('text-sm text-gray-900 mb-2')
            ui.label('💡 Tip: The number 5 is not fixed - continue asking why until you reach the root cause.').classes('text-xs text-blue-700')
        
        # Two-column layout
        with ui.row().classes('w-full gap-4'):
            # Left column: New Analysis
            with ui.column().classes('flex-1 gap-4'):
                ui.label('Start New Analysis').classes('text-2xl font-bold')
                
                with ui.card().classes('w-full p-4'):
                    ui.label('Select Issue Source').classes('text-lg font-semibold mb-2')
                    
                    source_type = ui.select(
                        ['Recent Downtime Events', 'Shift Issues', 'Custom Issue'],
                        label='Issue Source',
                        value='Recent Downtime Events'
                    ).classes('w-full mb-4').style('background: white;')
                    
                    issue_selector = ui.column().classes('w-full')
                    
                    def update_issue_selector():
                        """Update issue selector based on source type"""
                        issue_selector.clear()
                        
                        with issue_selector:
                            if source_type.value == 'Recent Downtime Events':
                                with engine.connect() as conn:
                                    recent_issues = conn.execute(text("""
                                        SELECT 
                                            event_id,
                                            line_id || ' - ' || TO_CHAR(start_timestamp, 'MM/DD HH24:MI') || 
                                            ' - ' || COALESCE(loss_category, 'Unclassified') || 
                                            ' (' || duration_min || ' min)' as display_text,
                                            loss_category,
                                            description,
                                            duration_min,
                                            line_id
                                        FROM oee_downtime_events
                                        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                                        ORDER BY start_timestamp DESC
                                        LIMIT 30
                                    """)).fetchall()
                                    
                                    if recent_issues:
                                        options = {row[1]: row for row in recent_issues}
                                        selected_issue = ui.select(
                                            list(options.keys()),
                                            label='Select Downtime Event',
                                            value=list(options.keys())[0] if options else None
                                        ).classes('w-full').style('background: white;')
                                        
                                        ui.button('Analyze This Issue', icon='psychology', 
                                                on_click=lambda: start_analysis(
                                                    options[selected_issue.value][2],  # loss_category
                                                    options[selected_issue.value][3],  # description
                                                    options[selected_issue.value][5]   # line_id
                                                )).classes('w-full mt-2')
                                    else:
                                        ui.label('No recent downtime events found').classes('text-gray-300')
                            
                            elif source_type.value == 'Shift Issues':
                                with engine.connect() as conn:
                                    shift_issues_data = conn.execute(text("""
                                        SELECT 
                                            si.issue_id,
                                            sh.line_id || ' - ' || TO_CHAR(sh.shift_date, 'MM/DD') || 
                                            ' - ' || si.issue_type || ' (' || si.severity || ')' as display_text,
                                            si.issue_type,
                                            si.description,
                                            sh.line_id,
                                            si.severity
                                        FROM shift_issues si
                                        JOIN shift_handovers sh ON si.handover_id = sh.handover_id
                                        WHERE sh.shift_date >= CURRENT_DATE - INTERVAL '7 days'
                                            AND si.status = 'open'
                                        ORDER BY sh.shift_date DESC, si.severity DESC
                                        LIMIT 30
                                    """)).fetchall()
                                    
                                    if shift_issues_data:
                                        options = {row[1]: row for row in shift_issues_data}
                                        selected_issue = ui.select(
                                            list(options.keys()),
                                            label='Select Shift Issue',
                                            value=list(options.keys())[0] if options else None
                                        ).classes('w-full').style('background: white;')
                                        
                                        ui.button('Analyze This Issue', icon='psychology',
                                                on_click=lambda: start_analysis(
                                                    options[selected_issue.value][2],  # issue_type
                                                    options[selected_issue.value][3],  # description
                                                    options[selected_issue.value][4]   # line_id
                                                )).classes('w-full mt-2')
                                    else:
                                        ui.label('No open shift issues found').classes('text-gray-300')
                            
                            else:  # Custom Issue
                                custom_line = ui.input('Production Line', placeholder='e.g., M10').classes('w-full')
                                custom_category = ui.input('Issue Category', placeholder='e.g., Equipment Failure').classes('w-full')
                                custom_description = ui.textarea('Issue Description', 
                                                                placeholder='Describe the problem...').classes('w-full')
                                
                                ui.button('Analyze This Issue', icon='psychology',
                                        on_click=lambda: start_analysis(
                                            custom_category.value,
                                            custom_description.value,
                                            custom_line.value
                                        )).classes('w-full mt-2')
                    
                    source_type.on('change', update_issue_selector)
                    update_issue_selector()
            
            # Right column: Analysis Workspace
            analysis_workspace = ui.column().classes('flex-1 gap-4')
        
        def start_analysis(issue_category, issue_description, line_id):
            """Start a new 5 Whys analysis"""
            analysis_workspace.clear()
            
            with analysis_workspace:
                ui.label('Active Analysis').classes('text-2xl font-bold')
                
                with ui.card().classes('w-full p-4 border-l-4 border-purple-500'):
                    ui.label('Problem Statement').classes('text-lg font-bold mb-2')
                    with ui.row().classes('w-full gap-2 items-center mb-2'):
                        ui.icon('factory', size='sm').classes('text-purple-600')
                        ui.label(f'Line: {line_id}').classes('font-semibold')
                    with ui.row().classes('w-full gap-2 items-center mb-2'):
                        ui.icon('category', size='sm').classes('text-purple-600')
                        ui.label(f'Category: {issue_category}').classes('font-semibold')
                    ui.label(issue_description or 'No description provided').classes('text-sm text-gray-200')
                
                # 5 Whys Form
                whys_data = []
                
                with ui.card().classes('w-full p-4'):
                    ui.label('5 Whys Analysis').classes('text-lg font-bold mb-4')
                    
                    for i in range(5):
                        with ui.card().classes('w-full p-3 mb-3 bg-gray-800'):
                            with ui.row().classes('w-full items-start gap-2'):
                                ui.label(f'{i+1}.').classes('text-2xl font-bold text-purple-600 w-8')
                                with ui.column().classes('flex-1 gap-2'):
                                    ui.label(f'Why #{i+1}').classes('font-semibold')
                                    why_input = ui.textarea(
                                        f'Why did this happen?',
                                        placeholder=f'Enter the cause at level {i+1}...'
                                    ).classes('w-full')
                                    whys_data.append(why_input)
                    
                    # Root Cause
                    with ui.card().classes('w-full p-4 bg-green-900 border-l-4 border-green-500'):
                        ui.label('🎯 Root Cause Identified').classes('text-lg font-bold mb-2')
                        root_cause_input = ui.textarea(
                            'Root Cause',
                            placeholder='Based on the analysis above, what is the fundamental root cause?'
                        ).classes('w-full mb-2')
                        
                        ui.label('Corrective Action').classes('font-semibold mb-1')
                        corrective_action_input = ui.textarea(
                            'Corrective Action',
                            placeholder='What action will be taken to prevent this from happening again?'
                        ).classes('w-full mb-2')
                        
                        ui.label('Responsible Person').classes('font-semibold mb-1')
                        responsible_input = ui.input('Responsible Person').classes('w-full mb-2')
                        
                        ui.label('Target Completion Date').classes('font-semibold mb-1')
                        target_date_input = ui.input('Target Date', value=datetime.now().strftime('%Y-%m-%d')).classes('w-full')
                    
                    # Action Buttons
                    with ui.row().classes('w-full gap-2 mt-4'):
                        ui.button('Save Analysis', icon='save', color='primary',
                                on_click=lambda: save_analysis(
                                    line_id, issue_category, issue_description,
                                    [w.value for w in whys_data],
                                    root_cause_input.value,
                                    corrective_action_input.value,
                                    responsible_input.value,
                                    target_date_input.value
                                ))
                        ui.button('Export PDF', icon='picture_as_pdf',
                                on_click=lambda: ui.notify('PDF export coming soon', type='info'))
                        ui.button('Clear', icon='clear',
                                on_click=lambda: analysis_workspace.clear())
        
        def save_analysis(line_id, category, description, whys, root_cause, corrective_action, responsible, target_date):
            """Save the 5 Whys analysis to database"""
            if not root_cause:
                ui.notify('Please identify the root cause before saving', type='warning')
                return
            
            with engine.connect() as conn:
                # Create analysis record
                result = conn.execute(text("""
                    INSERT INTO why_analysis (
                        line_id, issue_category, issue_description,
                        why1, why2, why3, why4, why5,
                        root_cause, corrective_action, responsible_person,
                        target_date, created_at, created_by, status
                    ) VALUES (
                        :line_id, :category, :description,
                        :why1, :why2, :why3, :why4, :why5,
                        :root_cause, :corrective_action, :responsible,
                        :target_date, NOW(), :created_by, 'open'
                    ) RETURNING analysis_id
                """), {
                    'line_id': line_id,
                    'category': category,
                    'description': description,
                    'why1': whys[0] if len(whys) > 0 else None,
                    'why2': whys[1] if len(whys) > 1 else None,
                    'why3': whys[2] if len(whys) > 2 else None,
                    'why4': whys[3] if len(whys) > 3 else None,
                    'why5': whys[4] if len(whys) > 4 else None,
                    'root_cause': root_cause,
                    'corrective_action': corrective_action,
                    'responsible': responsible,
                    'target_date': target_date,
                    'created_by': 'Current User'
                })
                analysis_id = result.fetchone()[0]
                conn.commit()
            
            ui.notify(f'Analysis saved! ID: {analysis_id}', type='positive')
            analysis_workspace.clear()
            show_history()
        
        def show_templates_dialog():
            """Show template library"""
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl max-h-screen overflow-auto'):
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    ui.label('5 Whys Templates').classes('text-2xl font-bold')
                    ui.button(icon='close', on_click=dialog.close).props('flat round')
                
                for template_name, template_data in ANALYSIS_TEMPLATES.items():
                    with ui.card().classes('w-full p-4 mb-3'):
                        with ui.expansion(template_name, icon='lightbulb').classes('w-full'):
                            with ui.column().classes('w-full gap-3 pt-2'):
                                ui.label(template_data['description']).classes('text-sm text-gray-200 mb-2')
                                
                                ui.label('Example Analysis:').classes('font-semibold text-sm mb-2')
                                for idx, why in enumerate(template_data['example_whys']):
                                    with ui.row().classes('w-full gap-2 mb-1'):
                                        ui.label(f'{idx+1}.').classes('font-bold text-purple-600 w-6')
                                        ui.label(why).classes('text-sm flex-1')
                                
                                with ui.card().classes('w-full p-3 bg-green-900 mt-2'):
                                    ui.label('🎯 Example Root Cause:').classes('font-semibold text-sm mb-1')
                                    ui.label(template_data['root_cause_example']).classes('text-sm text-gray-200')
            
            dialog.open()
        
        def show_history():
            """Show analysis history"""
            analysis_workspace.clear()
            
            with analysis_workspace:
                ui.label('Analysis History').classes('text-2xl font-bold mb-4')
                
                with engine.connect() as conn:
                    analyses = conn.execute(text("""
                        SELECT 
                            analysis_id, line_id, issue_category,
                            issue_description, root_cause, corrective_action,
                            responsible_person, target_date, created_at,
                            created_by, status
                        FROM why_analysis
                        ORDER BY created_at DESC
                        LIMIT 20
                    """)).fetchall()
                    
                    if not analyses:
                        with ui.card().classes('w-full p-8 text-center'):
                            ui.icon('history', size='xl').classes('text-gray-300 mb-2')
                            ui.label('No analysis history yet').classes('text-gray-300')
                            ui.label('Start your first 5 Whys analysis to see it here').classes('text-sm text-gray-300')
                        return
                    
                    for analysis in analyses:
                        (analysis_id, line_id, category, description, root_cause,
                         corrective_action, responsible, target_date, created_at,
                         created_by, status) = analysis
                        
                        status_colors = {
                            'open': 'border-orange-500 bg-orange-50',
                            'completed': 'border-green-500 bg-green-50',
                            'cancelled': 'border-gray-500 bg-gray-50'
                        }
                        
                        with ui.card().classes(f'w-full p-4 border-l-4 {status_colors.get(status, "border-blue-500")} mb-3'):
                            with ui.row().classes('w-full items-start justify-between mb-2'):
                                with ui.column():
                                    with ui.row().classes('items-center gap-2 mb-1'):
                                        ui.label(f'Analysis #{analysis_id}').classes('text-lg font-bold')
                                        ui.badge(status.upper(), color='orange' if status == 'open' else 'green')
                                    ui.label(f'{line_id} • {category}').classes('text-sm text-gray-600')
                                ui.label(created_at.strftime('%Y-%m-%d')).classes('text-sm text-gray-500')
                            
                            ui.label(description or 'No description').classes('text-sm mb-2')
                            
                            with ui.expansion('View Analysis', icon='visibility').classes('w-full'):
                                with ui.column().classes('w-full gap-2'):
                                    ui.label('🎯 Root Cause:').classes('font-semibold text-sm')
                                    ui.label(root_cause).classes('text-sm mb-2')
                                    
                                    if corrective_action:
                                        ui.label('🔧 Corrective Action:').classes('font-semibold text-sm')
                                        ui.label(corrective_action).classes('text-sm mb-2')
                                    
                                    if responsible:
                                        ui.label(f'👤 Responsible: {responsible}').classes('text-xs text-gray-600')
                                    
                                    if target_date:
                                        ui.label(f'📅 Target: {target_date}').classes('text-xs text-gray-600')
        
        # Initial state
        with analysis_workspace:
            with ui.card().classes('w-full p-8 text-center'):
                ui.icon('psychology', size='xl').classes('text-purple-600 mb-4')
                ui.label('Select an issue to begin analysis').classes('text-xl text-gray-600 mb-2')
                ui.label('Choose from recent downtime events, shift issues, or enter a custom problem').classes('text-sm text-gray-400')
