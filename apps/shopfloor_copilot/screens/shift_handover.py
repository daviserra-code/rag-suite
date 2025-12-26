"""
Shift Handover Dashboard
View and manage shift handover reports, issues, and notes
"""
from nicegui import ui
from datetime import datetime, timedelta
from sqlalchemy import text
import os

# Get database engine from oee_analytics router
from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine


def shift_handover_screen():
    """Shift handover dashboard with reports, issues, and notes"""
    
    engine = get_db_engine()
    
    with ui.column().classes('w-full p-4 gap-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Shift Handover Reports').classes('text-3xl font-bold')
            
            with ui.row().classes('gap-2'):
                ui.button('New Handover', icon='add', on_click=lambda: create_handover_dialog())
                ui.button('Refresh', icon='refresh', on_click=lambda: load_handovers())
        
        # Filters
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full gap-4 items-end'):
                # Get available lines and latest date
                with engine.connect() as conn:
                    lines = [row[0] for row in conn.execute(
                        text("SELECT DISTINCT line_id FROM shift_handovers ORDER BY line_id")
                    ).fetchall()]
                    
                    # Get the most recent date with data (default to showing recent data)
                    latest_date_result = conn.execute(
                        text("SELECT MAX(shift_date) FROM shift_handovers")
                    ).fetchone()
                    latest_date = latest_date_result[0].strftime('%Y-%m-%d') if latest_date_result[0] else datetime.now().strftime('%Y-%m-%d')
                
                date_input = ui.input('Date (leave empty for all)', value='').classes('w-64 text-gray-900').props('clearable outlined dense bg-color=white')
                
                line_filter = ui.select(
                    ['All'] + lines,
                    label='Production Line',
                    value='All'
                ).classes('w-48').props('outlined dense bg-color=white').style('color: #111827; background: white;')
                
                shift_filter = ui.select(
                    ['All', 'M', 'A', 'N'],
                    label='Shift',
                    value='All'
                ).classes('w-32').props('outlined dense bg-color=white').style('color: #111827; background: white;')
                
                status_filter = ui.select(
                    ['All', 'submitted', 'draft'],
                    label='Status',
                    value='All'
                ).classes('w-32').props('outlined dense bg-color=white').style('color: #111827; background: white;')
                
                ui.button('Apply', icon='filter_list', on_click=lambda: load_handovers())
        
        # Statistics Summary
        stats_container = ui.row().classes('w-full gap-4')
        
        # Handover Reports List
        handover_container = ui.column().classes('w-full gap-4')
        
        def load_handovers():
            """Load and display shift handover reports"""
            handover_container.clear()
            stats_container.clear()
            
            with engine.connect() as conn:
                # Build query with filters for shift_handovers table
                where_clauses = ["1=1"]
                issues_where_clauses = ["1=1"]
                params = {}
                
                if date_input.value:
                    where_clauses.append("shift_date = :date")
                    issues_where_clauses.append("sh.shift_date = :date")
                    params['date'] = date_input.value
                
                if line_filter.value != 'All':
                    where_clauses.append("line_id = :line")
                    issues_where_clauses.append("sh.line_id = :line")
                    params['line'] = line_filter.value
                
                if shift_filter.value != 'All':
                    where_clauses.append("shift = :shift")
                    issues_where_clauses.append("sh.shift = :shift")
                    params['shift'] = shift_filter.value
                
                if status_filter.value != 'All':
                    where_clauses.append("status = :status")
                    issues_where_clauses.append("sh.status = :status")
                    params['status'] = status_filter.value
                
                where_clause = " AND ".join(where_clauses)
                issues_where_clause = " AND ".join(issues_where_clauses)
                
                # Get statistics
                stats = conn.execute(text(f"""
                    SELECT 
                        COUNT(*) as total_handovers,
                        COUNT(CASE WHEN status = 'submitted' THEN 1 END) as submitted_count,
                        COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_count,
                        ROUND(AVG(oee_achieved)::numeric * 100, 1) as avg_oee,
                        SUM(total_production) as total_units
                    FROM shift_handovers
                    WHERE {where_clause}
                """), params).fetchone()
                
                # Get open issues count
                issues_count = conn.execute(text(f"""
                    SELECT COUNT(*)
                    FROM shift_issues si
                    JOIN shift_handovers sh ON si.handover_id = sh.handover_id
                    WHERE {issues_where_clause} AND si.status = 'open'
                """), params).fetchone()[0]
                
                # Display statistics
                with stats_container:
                    with ui.card().classes('p-4'):
                        ui.label(str(stats[0])).classes('text-3xl font-bold text-blue-600')
                        ui.label('Total Reports').classes('text-sm text-gray-200')
                    
                    with ui.card().classes('p-4'):
                        ui.label(str(stats[1])).classes('text-3xl font-bold text-green-600')
                        ui.label('Submitted').classes('text-sm text-gray-200')
                    
                    with ui.card().classes('p-4'):
                        ui.label(str(stats[2])).classes('text-3xl font-bold text-orange-600')
                        ui.label('Draft').classes('text-sm text-gray-200')
                    
                    with ui.card().classes('p-4'):
                        ui.label(f"{stats[3] or 0}%").classes('text-3xl font-bold text-purple-600')
                        ui.label('Avg OEE').classes('text-sm text-gray-200')
                    
                    with ui.card().classes('p-4'):
                        ui.label(str(issues_count)).classes('text-3xl font-bold text-red-600')
                        ui.label('Open Issues').classes('text-sm text-gray-200')
                
                # Get handover reports
                handovers = conn.execute(text(f"""
                    SELECT 
                        handover_id, shift_date, shift, line_id,
                        created_by, summary, total_production, oee_achieved,
                        major_issues, downtime_minutes, status,
                        created_at, submitted_at
                    FROM shift_handovers
                    WHERE {where_clause}
                    ORDER BY shift_date DESC, shift, line_id
                    LIMIT 50
                """), params).fetchall()
                
                if not handovers:
                    with handover_container:
                        with ui.card().classes('w-full p-8 text-center'):
                            ui.icon('info', size='xl').classes('text-gray-300 mb-2')
                            ui.label('No handover reports found for the selected filters.').classes('text-lg text-gray-300 mb-2')
                            ui.label('Try clearing the date filter or selecting different criteria.').classes('text-sm text-gray-300')
                    return
                
                # Display handover reports
                with handover_container:
                    for handover in handovers:
                        (handover_id, shift_date, shift, line_id,
                         created_by, summary, total_prod, oee, 
                         major_issues, downtime, status,
                         created_at, submitted_at) = handover
                        
                        create_handover_card(
                            conn, handover_id, shift_date, shift, line_id,
                            created_by, summary, total_prod, oee,
                            major_issues, downtime, status,
                            created_at, submitted_at
                        )
        
        def create_handover_card(conn, handover_id, shift_date, shift, line_id,
                                created_by, summary, total_prod, oee,
                                major_issues, downtime, status,
                                created_at, submitted_at):
            """Create a handover report card"""
            
            shift_names = {'M': 'Morning', 'A': 'Afternoon', 'N': 'Night'}
            shift_name = shift_names.get(shift, shift)
            
            status_colors = {
                'submitted': 'bg-gray-800 border-green-500',
                'draft': 'bg-gray-800 border-orange-500'
            }
            
            with ui.card().classes(f'w-full border-l-4 {status_colors.get(status, "border-gray-500")}'):
                with ui.row().classes('w-full items-start justify-between'):
                    # Header
                    with ui.column().classes('gap-1'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(f'{line_id} - {shift_name} Shift').classes('text-xl font-bold text-white')
                            ui.badge(status.upper(), color='green' if status == 'submitted' else 'orange')
                        ui.label(f"{shift_date.strftime('%A, %B %d, %Y')}").classes('text-sm text-gray-200')
                        ui.label(f"Created by: {created_by}").classes('text-xs text-gray-300')
                    
                    # Metrics
                    with ui.row().classes('gap-4'):
                        with ui.column().classes('items-center'):
                            ui.label(f"{(oee or 0)*100:.1f}%").classes('text-2xl font-bold text-blue-600')
                            ui.label('OEE').classes('text-xs text-gray-200 font-semibold')
                        
                        with ui.column().classes('items-center'):
                            ui.label(str(total_prod or 0)).classes('text-2xl font-bold text-green-600')
                            ui.label('Units').classes('text-xs text-gray-200 font-semibold')
                        
                        with ui.column().classes('items-center'):
                            ui.label(str(int(downtime or 0))).classes('text-2xl font-bold text-red-600')
                            ui.label('Min Down').classes('text-xs text-gray-200 font-semibold')
                
                # Summary
                with ui.expansion('Summary & Details', icon='description').classes('w-full'):
                    ui.label(summary).classes('text-sm')
                
                # Issues
                issues = conn.execute(text("""
                    SELECT issue_id, issue_type, severity, description, status, resolved_by
                    FROM shift_issues
                    WHERE handover_id = :handover_id
                    ORDER BY severity DESC, reported_at DESC
                """), {'handover_id': handover_id}).fetchall()
                
                if issues:
                    with ui.expansion(f'Issues ({len(issues)})', icon='warning').classes('w-full'):
                        for issue in issues:
                            issue_id, issue_type, severity, description, issue_status, resolved_by = issue
                            
                            severity_colors = {
                                'critical': 'red',
                                'high': 'orange',
                                'medium': 'yellow',
                                'low': 'blue'
                            }
                            
                            with ui.row().classes('w-full items-start gap-2 p-2 border-l-2 border-gray-600'):
                                ui.badge(severity.upper(), color=severity_colors.get(severity, 'gray'))
                                
                                with ui.column().classes('flex-1'):
                                    ui.label(issue_type).classes('font-semibold text-white')
                                    ui.label(description).classes('text-sm text-gray-200')
                                    
                                    if issue_status == 'resolved':
                                        ui.label(f'✓ Resolved by {resolved_by}').classes('text-xs text-green-600')
                                    else:
                                        ui.label('◯ Open').classes('text-xs text-red-600')
                
                # Notes
                notes = conn.execute(text("""
                    SELECT note_type, note_text, created_by, created_at
                    FROM shift_notes
                    WHERE handover_id = :handover_id
                    ORDER BY created_at
                """), {'handover_id': handover_id}).fetchall()
                
                if notes:
                    with ui.expansion(f'Notes ({len(notes)})', icon='note').classes('w-full'):
                        for note in notes:
                            note_type, note_text, note_by, note_time = note
                            
                            note_icons = {
                                'observation': '👁️',
                                'action_taken': '🔧',
                                'follow_up': '📌',
                                'general': '📝'
                            }
                            
                            with ui.row().classes('w-full gap-2 p-2 bg-gray-800 rounded'):
                                ui.label(note_icons.get(note_type, '📝'))
                                with ui.column().classes('flex-1'):
                                    ui.label(note_text).classes('text-sm text-white')
                                    ui.label(f"{note_by} - {note_time.strftime('%H:%M')}").classes('text-xs text-gray-300')
                
                # Actions
                with ui.row().classes('w-full gap-2 mt-2'):
                    if status == 'draft':
                        ui.button('Submit Report', icon='send', 
                                 on_click=lambda: submit_handover(handover_id))
                    ui.button('Add Note', icon='add_comment',
                             on_click=lambda: add_note_dialog(handover_id))
                    ui.button('View Details', icon='open_in_new',
                             on_click=lambda: view_handover_details(handover_id))
        
        def create_handover_dialog():
            """Dialog to create new handover report"""
            with ui.dialog() as dialog, ui.card().classes('w-96'):
                ui.label('Create New Handover Report').classes('text-xl font-bold')
                
                with engine.connect() as conn:
                    lines = [row[0] for row in conn.execute(
                        text("SELECT DISTINCT line_id FROM oee_line_shift ORDER BY line_id")
                    ).fetchall()]
                
                line_input = ui.select(lines, label='Production Line').classes('w-full').style('background: #1f2937; color: #e5e7eb;')
                shift_input = ui.select(['M', 'A', 'N'], label='Shift').classes('w-full').style('background: #1f2937; color: #e5e7eb;')
                date_inp = ui.input('Date', value=datetime.now().strftime('%Y-%m-%d')).classes('w-full')
                summary_input = ui.textarea(label='Summary', placeholder='Shift summary...').classes('w-full')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancel', on_click=dialog.close)
                    ui.button('Create', icon='save', color='primary',
                             on_click=lambda: save_new_handover(dialog, line_input.value, 
                                                                shift_input.value, date_inp.value,
                                                                summary_input.value))
            
            dialog.open()
        
        def save_new_handover(dialog, line, shift, date, summary):
            """Save new handover report"""
            if not all([line, shift, date, summary]):
                ui.notify('Please fill all required fields', type='warning')
                return
            
            handover_id = f"HO{date.replace('-', '')}{shift}{line}"
            
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO shift_handovers (
                        handover_id, shift_date, shift, line_id,
                        created_by, summary, status, created_at
                    ) VALUES (:id, :date, :shift, :line, :by, :summary, 'draft', NOW())
                """), {
                    'id': handover_id,
                    'date': date,
                    'shift': shift,
                    'line': line,
                    'by': 'Current User',
                    'summary': summary
                })
                conn.commit()
            
            ui.notify('Handover report created successfully!', type='positive')
            dialog.close()
            load_handovers()
        
        def submit_handover(handover_id):
            """Submit a draft handover report"""
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE shift_handovers
                    SET status = 'submitted', submitted_at = NOW()
                    WHERE handover_id = :id
                """), {'id': handover_id})
                conn.commit()
            
            ui.notify('Handover report submitted!', type='positive')
            load_handovers()
        
        def add_note_dialog(handover_id):
            """Dialog to add note to handover"""
            with ui.dialog() as dialog, ui.card().classes('w-96'):
                ui.label('Add Shift Note').classes('text-xl font-bold')
                
                note_type = ui.select(
                    ['observation', 'action_taken', 'follow_up', 'general'],
                    label='Note Type',
                    value='general'
                ).classes('w-full').style('background: white;')
                
                note_text = ui.textarea(label='Note', placeholder='Enter note...').classes('w-full')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancel', on_click=dialog.close)
                    ui.button('Add Note', icon='save', color='primary',
                             on_click=lambda: save_note(dialog, handover_id, 
                                                        note_type.value, note_text.value))
            
            dialog.open()
        
        def save_note(dialog, handover_id, note_type, note_text):
            """Save note to handover"""
            if not note_text:
                ui.notify('Please enter note text', type='warning')
                return
            
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO shift_notes (
                        handover_id, note_type, note_text,
                        created_by, created_at
                    ) VALUES (:id, :type, :text, :by, NOW())
                """), {
                    'id': handover_id,
                    'type': note_type,
                    'text': note_text,
                    'by': 'Current User'
                })
                conn.commit()
            
            ui.notify('Note added successfully!', type='positive')
            dialog.close()
            load_handovers()
        
        def view_handover_details(handover_id):
            """View detailed handover report"""
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl'):
                with engine.connect() as conn:
                    # Get handover details
                    handover = conn.execute(text("""
                        SELECT handover_id, shift_date, shift, line_id,
                               created_by, summary, total_production, oee_achieved,
                               major_issues, downtime_minutes, status,
                               created_at, submitted_at
                        FROM shift_handovers
                        WHERE handover_id = :id
                    """), {'id': handover_id}).fetchone()
                    
                    if not handover:
                        ui.label('Handover not found').classes('text-red-500')
                        ui.button('Close', on_click=dialog.close)
                        dialog.open()
                        return
                    
                    (hid, shift_date, shift, line_id, created_by, summary,
                     total_prod, oee, major_issues, downtime, status,
                     created_at, submitted_at) = handover
                    
                    shift_names = {'M': 'Morning', 'A': 'Afternoon', 'N': 'Night'}
                    
                    # Header
                    with ui.row().classes('w-full items-center justify-between mb-4'):
                        with ui.column():
                            ui.label(f'{line_id} - {shift_names.get(shift, shift)} Shift').classes('text-2xl font-bold')
                            ui.label(f"{shift_date.strftime('%A, %B %d, %Y')}").classes('text-gray-600')
                        ui.badge(status.upper(), color='green' if status == 'submitted' else 'orange')
                    
                    # Metrics
                    with ui.row().classes('w-full gap-4 mb-4'):
                        with ui.card().classes('flex-1 p-4'):
                            ui.label(f"{oee*100:.1f}%").classes('text-3xl font-bold text-blue-600')
                            ui.label('OEE Achieved').classes('text-sm text-gray-600')
                        
                        with ui.card().classes('flex-1 p-4'):
                            ui.label(str(total_prod)).classes('text-3xl font-bold text-green-600')
                            ui.label('Units Produced').classes('text-sm text-gray-600')
                        
                        with ui.card().classes('flex-1 p-4'):
                            ui.label(str(int(downtime))).classes('text-3xl font-bold text-red-600')
                            ui.label('Downtime (min)').classes('text-sm text-gray-600')
                        
                        with ui.card().classes('flex-1 p-4'):
                            ui.label(str(major_issues)).classes('text-3xl font-bold text-orange-600')
                            ui.label('Issues').classes('text-sm text-gray-600')
                    
                    # Summary
                    with ui.card().classes('w-full p-4 mb-4'):
                        ui.label('Shift Summary').classes('text-lg font-bold mb-2')
                        ui.label(summary).classes('text-sm')
                    
                    # Issues
                    issues = conn.execute(text("""
                        SELECT issue_id, issue_type, severity, description,
                               root_cause, resolution, status,
                               reported_by, resolved_by, reported_at, resolved_at
                        FROM shift_issues
                        WHERE handover_id = :handover_id
                        ORDER BY severity DESC, reported_at DESC
                    """), {'handover_id': handover_id}).fetchall()
                    
                    if issues:
                        with ui.card().classes('w-full p-4 mb-4'):
                            ui.label(f'Issues ({len(issues)})').classes('text-lg font-bold mb-2')
                            for issue in issues:
                                (issue_id, issue_type, severity, description,
                                 root_cause, resolution, issue_status,
                                 reported_by, resolved_by, reported_at, resolved_at) = issue
                                
                                severity_colors = {
                                    'critical': 'border-red-500',
                                    'high': 'border-orange-500',
                                    'medium': 'border-yellow-500',
                                    'low': 'border-blue-500'
                                }
                                
                                with ui.card().classes(f'w-full p-3 border-l-4 {severity_colors.get(severity, "border-gray-500")} mb-2'):
                                    with ui.row().classes('w-full items-start justify-between mb-2'):
                                        with ui.column():
                                            ui.label(issue_type).classes('font-bold')
                                            ui.badge(severity.upper(), color=severity)
                                        ui.label(issue_status.upper()).classes(
                                            'text-xs px-2 py-1 rounded ' + 
                                            ('bg-green-100 text-green-800' if issue_status == 'resolved' else 'bg-red-100 text-red-800')
                                        )
                                    
                                    ui.label(description).classes('text-sm mb-2')
                                    
                                    if root_cause:
                                        ui.label(f'Root Cause: {root_cause}').classes('text-xs text-gray-600 mb-1')
                                    
                                    if resolution:
                                        ui.label(f'Resolution: {resolution}').classes('text-xs text-green-700 mb-1')
                                        ui.label(f'Resolved by: {resolved_by} at {resolved_at.strftime("%H:%M")}').classes('text-xs text-gray-500')
                                    else:
                                        ui.label(f'Reported by: {reported_by} at {reported_at.strftime("%H:%M")}').classes('text-xs text-gray-500')
                    
                    # Notes
                    notes = conn.execute(text("""
                        SELECT note_type, note_text, created_by, created_at
                        FROM shift_notes
                        WHERE handover_id = :handover_id
                        ORDER BY created_at
                    """), {'handover_id': handover_id}).fetchall()
                    
                    if notes:
                        with ui.card().classes('w-full p-4 mb-4'):
                            ui.label(f'Shift Notes ({len(notes)})').classes('text-lg font-bold mb-2')
                            for note in notes:
                                note_type, note_text, note_by, note_time = note
                                
                                note_icons = {
                                    'observation': '👁️',
                                    'action_taken': '🔧',
                                    'follow_up': '📌',
                                    'general': '📝'
                                }
                                
                                with ui.row().classes('w-full gap-2 p-2 bg-gray-800 rounded mb-2'):
                                    ui.label(note_icons.get(note_type, '📝')).classes('text-xl')
                                    with ui.column().classes('flex-1'):
                                        ui.label(note_text).classes('text-sm text-white')
                                        ui.label(f"{note_by} - {note_time.strftime('%H:%M')}").classes('text-xs text-gray-300')
                    
                    # Metadata
                    with ui.card().classes('w-full p-4 bg-gray-800'):
                        ui.label('Metadata').classes('text-sm font-bold text-white mb-2')
                        ui.label(f'Handover ID: {hid}').classes('text-xs text-gray-300')
                        ui.label(f'Created by: {created_by}').classes('text-xs text-gray-300')
                        ui.label(f'Created at: {created_at.strftime("%Y-%m-%d %H:%M:%S")}').classes('text-xs text-gray-300')
                        if submitted_at:
                            ui.label(f'Submitted at: {submitted_at.strftime("%Y-%m-%d %H:%M:%S")}').classes('text-xs text-gray-300')
                    
                    # Close button
                    with ui.row().classes('w-full justify-end mt-4'):
                        ui.button('Close', icon='close', on_click=dialog.close)
            
            dialog.open()
        
        # Initial load
        load_handovers()
