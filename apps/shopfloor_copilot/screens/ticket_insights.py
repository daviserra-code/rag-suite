"""
Ticket Insights Screen
Real-time Jira integration for issue tracking, sprint analytics, and AI-powered insights
"""
import os
from nicegui import ui, app
from typing import Dict, List
import asyncio
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/app')

from packages.jira_integration.jira_client import get_jira_client
from packages.jira_integration.mock_data import get_mock_sprint_data, get_mock_ai_insights
from sqlalchemy import create_engine, text
from packages.export_utils.pdf_export import export_to_pdf, generate_pdf_section
from packages.export_utils.csv_export import export_to_csv, create_csv_download


def build_ticket_insights():
    """Build the Ticket Insights dashboard with Jira MCP integration"""
    
    # Initialize Jira client
    jira_client = get_jira_client()
    
    # Database connection
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@postgres:5432/ragdb")
    engine = create_engine(db_url)
    
    # Storage initialization
    if 'ticket_project' not in app.storage.user:
        app.storage.user['ticket_project'] = 'SHOP'  # Default project key
    if 'ticket_view' not in app.storage.user:
        app.storage.user['ticket_view'] = 'sprint'
    if 'ticket_board_id' not in app.storage.user:
        app.storage.user['ticket_board_id'] = None
    if 'ticket_use_mock' not in app.storage.user:
        # Auto-detect: use mock data if Jira not configured
        jira_host = os.getenv('ATLASSIAN_HOST', '')
        use_mock = not jira_host or 'your-company' in jira_host
        app.storage.user['ticket_use_mock'] = use_mock
    
    async def load_sprint_data():
        """Load current sprint data from Jira or mock data"""
        # Check if using mock data
        if app.storage.user.get('ticket_use_mock', False):
            return get_mock_sprint_data()
        
        try:
            project_key = app.storage.user.get('ticket_project', 'SHOP')
            
            # Get active sprint
            sprint_result = await jira_client.get_active_sprint(project_key=project_key)
            
            if 'error' in sprint_result or not sprint_result:
                return {
                    'sprint': None,
                    'issues': [],
                    'stats': {
                        'total': 0,
                        'todo': 0,
                        'in_progress': 0,
                        'done': 0,
                        'blocked': 0
                    }
                }
            
            sprint = sprint_result.get('sprint', {})
            sprint_id = sprint.get('id')
            
            # Get sprint issues
            jql = f"sprint = {sprint_id}" if sprint_id else f"project = {project_key} AND sprint in openSprints()"
            issues_result = await jira_client.search_issues(
                jql=jql,
                fields=["summary", "status", "assignee", "priority", "issuetype", "created", "updated"],
                max_results=100
            )
            
            issues = issues_result.get('issues', [])
            
            # Calculate stats
            stats = {
                'total': len(issues),
                'todo': 0,
                'in_progress': 0,
                'done': 0,
                'blocked': 0
            }
            
            for issue in issues:
                status = issue.get('fields', {}).get('status', {}).get('name', '').lower()
                if 'done' in status or 'closed' in status:
                    stats['done'] += 1
                elif 'progress' in status or 'review' in status:
                    stats['in_progress'] += 1
                elif 'blocked' in status:
                    stats['blocked'] += 1
                else:
                    stats['todo'] += 1
            
            return {
                'sprint': sprint,
                'issues': issues,
                'stats': stats
            }
            
        except Exception as e:
            print(f"Error loading sprint data: {e}")
            return {
                'sprint': None,
                'issues': [],
                'stats': {'total': 0, 'todo': 0, 'in_progress': 0, 'done': 0, 'blocked': 0}
            }
    
    async def load_issue_details(issue_key: str):
        """Load detailed information for a specific issue"""
        try:
            issue = await jira_client.get_issue(issue_key)
            dev_info = await jira_client.get_development_info(issue_key)
            comments = await jira_client.get_comments(issue_key)
            
            return {
                'issue': issue,
                'dev_info': dev_info,
                'comments': comments
            }
        except Exception as e:
            print(f"Error loading issue details: {e}")
            return None
    
    async def load_ai_insights():
        """Generate AI-powered insights from ticket patterns"""
        # Check if using mock data
        if app.storage.user.get('ticket_use_mock', False):
            return get_mock_ai_insights()
        
        try:
            project_key = app.storage.user.get('ticket_project', 'SHOP')
            
            # Get recent issues (last 30 days)
            jql = f"project = {project_key} AND created >= -30d ORDER BY created DESC"
            result = await jira_client.search_issues(jql=jql, max_results=100)
            issues = result.get('issues', [])
            
            if not issues:
                return {
                    'patterns': [],
                    'blockers': [],
                    'predictions': []
                }
            
            # Analyze patterns
            issue_types = {}
            priorities = {}
            blockers = []
            
            for issue in issues:
                fields = issue.get('fields', {})
                
                # Count by type
                issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                
                # Count by priority
                priority = fields.get('priority', {}).get('name', 'Unknown')
                priorities[priority] = priorities.get(priority, 0) + 1
                
                # Track blockers
                status = fields.get('status', {}).get('name', '').lower()
                if 'blocked' in status:
                    blockers.append({
                        'key': issue.get('key'),
                        'summary': fields.get('summary', ''),
                        'age_days': (datetime.now() - datetime.fromisoformat(
                            fields.get('created', '').replace('Z', '+00:00')
                        )).days
                    })
            
            # Generate insights
            patterns = []
            if issue_types:
                most_common = max(issue_types.items(), key=lambda x: x[1])
                patterns.append({
                    'type': 'Issue Type Trend',
                    'insight': f"{most_common[0]} issues are most common ({most_common[1]} in last 30 days)",
                    'severity': 'info'
                })
            
            if priorities.get('High', 0) + priorities.get('Highest', 0) > len(issues) * 0.3:
                patterns.append({
                    'type': 'Priority Alert',
                    'insight': f"High priority issues make up {((priorities.get('High', 0) + priorities.get('Highest', 0)) / len(issues) * 100):.0f}% of recent tickets",
                    'severity': 'warning'
                })
            
            if len(blockers) > 0:
                patterns.append({
                    'type': 'Blocker Alert',
                    'insight': f"{len(blockers)} blocked issues requiring attention",
                    'severity': 'error'
                })
            
            return {
                'patterns': patterns,
                'blockers': blockers[:5],  # Top 5
                'issue_types': issue_types,
                'priorities': priorities
            }
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return {
                'patterns': [],
                'blockers': [],
                'issue_types': {},
                'priorities': {}
            }
    
    def export_tickets_pdf():
        """Export ticket insights to PDF"""
        try:
            data = app.storage.user.get('sprint_data', {})
            sprint = data.get('sprint', {})
            issues = data.get('issues', [])
            stats = data.get('stats', {})
            
            # Generate HTML content
            html_parts = []
            
            # Sprint info
            sprint_name = sprint.get('name', 'Current Sprint')
            html_parts.append(f"<h1>Ticket Insights Report</h1>")
            html_parts.append(f"<h2>{sprint_name}</h2>")
            html_parts.append(f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>")
            
            # Stats cards
            html_parts.append("""
            <div style='display: flex; gap: 20px; margin: 30px 0;'>
                <div style='flex: 1; padding: 20px; background: #0d9488; color: white; border-radius: 8px;'>
                    <div style='font-size: 32px; font-weight: bold;'>{}</div>
                    <div>Total Issues</div>
                </div>
                <div style='flex: 1; padding: 20px; background: #3b82f6; color: white; border-radius: 8px;'>
                    <div style='font-size: 32px; font-weight: bold;'>{}</div>
                    <div>In Progress</div>
                </div>
                <div style='flex: 1; padding: 20px; background: #10b981; color: white; border-radius: 8px;'>
                    <div style='font-size: 32px; font-weight: bold;'>{}</div>
                    <div>Done</div>
                </div>
                <div style='flex: 1; padding: 20px; background: #ef4444; color: white; border-radius: 8px;'>
                    <div style='font-size: 32px; font-weight: bold;'>{}</div>
                    <div>Blocked</div>
                </div>
            </div>
            """.format(stats.get('total', 0), stats.get('in_progress', 0), stats.get('done', 0), stats.get('blocked', 0)))
            
            # Issues table
            html_parts.append("<h3>Sprint Issues</h3>")
            html_parts.append("<table style='width: 100%; border-collapse: collapse;'>")
            html_parts.append("<thead><tr>")
            html_parts.append("<th style='border: 1px solid #ddd; padding: 8px; background: #f3f4f6;'>Key</th>")
            html_parts.append("<th style='border: 1px solid #ddd; padding: 8px; background: #f3f4f6;'>Summary</th>")
            html_parts.append("<th style='border: 1px solid #ddd; padding: 8px; background: #f3f4f6;'>Status</th>")
            html_parts.append("<th style='border: 1px solid #ddd; padding: 8px; background: #f3f4f6;'>Priority</th>")
            html_parts.append("</tr></thead><tbody>")
            
            for issue in issues[:20]:  # Top 20 issues
                fields = issue.get('fields', {})
                html_parts.append("<tr>")
                html_parts.append(f"<td style='border: 1px solid #ddd; padding: 8px;'>{issue.get('key', '')}</td>")
                html_parts.append(f"<td style='border: 1px solid #ddd; padding: 8px;'>{fields.get('summary', '')}</td>")
                html_parts.append(f"<td style='border: 1px solid #ddd; padding: 8px;'>{fields.get('status', {}).get('name', '')}</td>")
                html_parts.append(f"<td style='border: 1px solid #ddd; padding: 8px;'>{fields.get('priority', {}).get('name', '')}</td>")
                html_parts.append("</tr>")
            
            html_parts.append("</tbody></table>")
            
            html_content = ''.join(html_parts)
            
            pdf_bytes = export_to_pdf(
                title="Ticket Insights Report",
                content=html_content
            )
            
            ui.download(pdf_bytes, f"ticket_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            ui.notify('PDF exported successfully', type='positive')
            
        except Exception as e:
            print(f"Error exporting PDF: {e}")
            ui.notify(f'Export failed: {str(e)}', type='negative')
    
    def export_tickets_csv():
        """Export ticket list to CSV"""
        try:
            data = app.storage.user.get('sprint_data', {})
            issues = data.get('issues', [])
            
            csv_data = []
            for issue in issues:
                fields = issue.get('fields', {})
                csv_data.append({
                    'Key': issue.get('key', ''),
                    'Summary': fields.get('summary', ''),
                    'Status': fields.get('status', {}).get('name', ''),
                    'Priority': fields.get('priority', {}).get('name', ''),
                    'Type': fields.get('issuetype', {}).get('name', ''),
                    'Assignee': fields.get('assignee', {}).get('displayName', 'Unassigned'),
                    'Created': fields.get('created', ''),
                    'Updated': fields.get('updated', '')
                })
            
            csv_bytes = create_csv_download(csv_data)
            ui.download(csv_bytes, f"sprint_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            ui.notify('CSV exported successfully', type='positive')
            
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            ui.notify(f'Export failed: {str(e)}', type='negative')
    
    @ui.refreshable
    def sprint_overview():
        """Display sprint overview"""
        data = app.storage.user.get('sprint_data', {})
        sprint = data.get('sprint')
        stats = data.get('stats', {})
        
        if not sprint:
            with ui.column().classes('w-full items-center justify-center p-8'):
                ui.icon('inbox', size='xl').classes('text-gray-400 mb-4')
                ui.label('No active sprint found').classes('text-xl font-semibold text-gray-900')
                ui.label('Configure Jira connection or create a sprint').classes('text-base text-gray-800')
            return
        
        # Sprint header with better styling
        with ui.card().classes('w-full p-6 bg-gradient-to-r from-teal-50 to-cyan-50 border-2 border-teal-200 mb-4'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label(f"🎯 {sprint.get('name', 'Current Sprint')}").classes('text-2xl font-bold text-gray-900')
                
                # Sprint dates
                start_date = sprint.get('startDate', '')
                end_date = sprint.get('endDate', '')
                if start_date and end_date:
                    ui.label(f"{start_date[:10]} → {end_date[:10]}").classes('text-base font-semibold text-gray-800')
        
        # Stats cards with better contrast
        with ui.row().classes('w-full gap-4 mb-6'):
            # Total
            with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-teal-600 to-teal-700 border-2 border-teal-800'):
                ui.label(str(stats.get('total', 0))).classes('text-5xl font-bold text-white')
                ui.label('Total Issues').classes('text-base font-medium text-white opacity-95')
            
            # To Do
            with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-gray-600 to-gray-700 border-2 border-gray-800'):
                ui.label(str(stats.get('todo', 0))).classes('text-5xl font-bold text-white')
                ui.label('To Do').classes('text-base font-medium text-white opacity-95')
            
            # In Progress
            with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-blue-600 to-blue-700 border-2 border-blue-800'):
                ui.label(str(stats.get('in_progress', 0))).classes('text-5xl font-bold text-white')
                ui.label('In Progress').classes('text-base font-medium text-white opacity-95')
            
            # Done
            with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-green-600 to-green-700 border-2 border-green-800'):
                ui.label(str(stats.get('done', 0))).classes('text-5xl font-bold text-white')
                ui.label('Done').classes('text-base font-medium text-white opacity-95')
            
            # Blocked
            with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-red-600 to-red-700 border-2 border-red-800'):
                ui.label(str(stats.get('blocked', 0))).classes('text-5xl font-bold text-white')
                ui.label('Blocked').classes('text-base font-medium text-white opacity-95')
        
        # Progress bar with better styling
        total = stats.get('total', 1)
        done_pct = (stats.get('done', 0) / total * 100) if total > 0 else 0
        in_progress_pct = (stats.get('in_progress', 0) / total * 100) if total > 0 else 0
        
        with ui.card().classes('w-full p-6 border-2 border-gray-200'):
            ui.label('Sprint Progress').classes('text-xl font-bold text-gray-900 mb-4')
            with ui.row().classes('w-full h-10 bg-gray-200 rounded-lg overflow-hidden shadow-inner'):
                ui.element('div').classes('h-full bg-green-500').style(f'width: {done_pct}%')
                ui.element('div').classes('h-full bg-blue-500').style(f'width: {in_progress_pct}%')
            with ui.row().classes('w-full justify-between mt-3'):
                ui.label(f'{done_pct:.0f}% Complete').classes('text-base font-semibold text-gray-900')
                ui.label(f'{in_progress_pct:.0f}% In Progress').classes('text-base font-semibold text-gray-900')
    
    @ui.refreshable
    def issues_list():
        """Display issues in a list"""
        data = app.storage.user.get('sprint_data', {})
        issues = data.get('issues', [])
        
        if not issues:
            with ui.column().classes('w-full items-center justify-center p-8'):
                ui.icon('task', size='lg').classes('text-gray-400')
                ui.label('No issues found').classes('text-base font-semibold text-gray-900')
            return
        
        ui.label(f'📋 {len(issues)} Sprint Issues').classes('text-xl font-bold text-gray-900 mb-4')
        
        for issue in issues[:15]:  # Show first 15
            fields = issue.get('fields', {})
            key = issue.get('key', '')
            summary = fields.get('summary', '')
            status = fields.get('status', {}).get('name', '')
            priority = fields.get('priority', {}).get('name', '')
            issue_type = fields.get('issuetype', {}).get('name', '')
            
            # Status color
            status_color = 'gray'
            if 'done' in status.lower():
                status_color = 'green'
            elif 'progress' in status.lower():
                status_color = 'blue'
            elif 'blocked' in status.lower():
                status_color = 'red'
            
            with ui.card().classes('sf-card hover:shadow-lg transition-shadow cursor-pointer'):
                with ui.row().classes('w-full items-start gap-3'):
                    # Issue type icon
                    icon = 'bug_report' if issue_type == 'Bug' else 'task' if issue_type == 'Task' else 'lightbulb'
                    ui.icon(icon).classes('text-2xl text-teal-600')
                    
                    # Content
                    with ui.column().classes('flex-grow gap-1'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(key).classes('text-sm font-bold text-teal-600')
                            ui.badge(status).classes(f'bg-{status_color}-100 text-{status_color}-800 text-xs')
                            ui.badge(priority).classes('bg-orange-100 text-orange-800 text-xs')
                        
                        ui.label(summary).classes('text-sm font-medium text-gray-900')
                        
                        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')
                        ui.label(f'👤 {assignee}').classes('text-sm text-gray-800 font-medium')
    
    @ui.refreshable
    def ai_insights_panel():
        """Display AI-powered insights"""
        insights = app.storage.user.get('ai_insights', {})
        patterns = insights.get('patterns', [])
        blockers = insights.get('blockers', [])
        
        if not patterns and not blockers:
            with ui.column().classes('w-full items-center justify-center p-8'):
                ui.icon('psychology', size='lg').classes('text-gray-400')
                ui.label('Analyzing ticket patterns...').classes('text-base font-semibold text-gray-900')
            return
        
        # Patterns
        if patterns:
            ui.label('🧠 AI Insights').classes('text-xl font-bold text-gray-900 mb-4')
            
            for pattern in patterns:
                severity = pattern.get('severity', 'info')
                bg_color = 'blue' if severity == 'info' else 'orange' if severity == 'warning' else 'red'
                
                with ui.card().classes(f'p-4 bg-{bg_color}-50 border-l-4 border-{bg_color}-500'):
                    ui.label(pattern.get('type', '')).classes('text-sm font-bold text-gray-900 mb-2')
                    ui.label(pattern.get('insight', '')).classes('text-base text-gray-900')
        
        # Blockers
        if blockers:
            ui.label('🚫 Blocked Issues').classes('text-xl font-bold text-gray-900 mb-4 mt-6')
            
            for blocker in blockers:
                with ui.card().classes('p-4 bg-red-50 border-l-4 border-red-500'):
                    with ui.row().classes('w-full items-center justify-between'):
                        ui.label(blocker.get('key', '')).classes('text-base font-bold text-red-700')
                        ui.label(f"{blocker.get('age_days', 0)} days").classes('text-sm text-gray-900 font-medium')
                    ui.label(blocker.get('summary', '')).classes('text-base text-gray-900 mt-2')
    
    async def refresh_data():
        """Refresh all dashboard data"""
        # Load sprint data
        sprint_data = await load_sprint_data()
        app.storage.user['sprint_data'] = sprint_data
        
        # Load AI insights
        ai_insights = await load_ai_insights()
        app.storage.user['ai_insights'] = ai_insights
        
        # Refresh displays
        sprint_overview.refresh()
        issues_list.refresh()
        ai_insights_panel.refresh()
    
    async def refresh_with_notify():
        """Refresh data with UI notifications"""
        ui.notify('Loading ticket data...', type='info')
        await refresh_data()
        ui.notify('Data refreshed', type='positive')
    
    def update_project(e):
        """Update selected project"""
        app.storage.user['ticket_project'] = e.value
        sprint_overview.refresh()
        issues_list.refresh()
        ai_insights_panel.refresh()
    
    def toggle_mock_data(e):
        """Toggle between mock and real Jira data"""
        app.storage.user['ticket_use_mock'] = e.value
        sprint_overview.refresh()
        issues_list.refresh()
        ai_insights_panel.refresh()
    
    # Main layout
    with ui.column().classes('w-full gap-4'):
        # Header with controls
        with ui.card().classes('sf-card'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('🎫 Ticket Insights').classes('text-xl font-bold')
                
                with ui.row().classes('gap-2'):
                    # Mock data toggle
                    with ui.row().classes('items-center gap-2'):
                        ui.switch(
                            'Demo Mode',
                            value=app.storage.user.get('ticket_use_mock', False),
                            on_change=toggle_mock_data
                        ).classes('text-sm').tooltip('Use mock data when Jira is not configured')
                    
                    ui.input(
                        label='Project Key',
                        value=app.storage.user.get('ticket_project', 'SHOP'),
                        on_change=update_project
                    ).classes('w-32').props('disable' if app.storage.user.get('ticket_use_mock', False) else '')
                    
                    ui.button('Refresh', icon='refresh', on_click=refresh_with_notify).classes('sf-btn')
                    ui.button('Export CSV', icon='download', on_click=export_tickets_csv).classes('sf-btn secondary')
                    ui.button('Export PDF', icon='picture_as_pdf', on_click=export_tickets_pdf).classes('sf-btn secondary')
        
        # Content area
        with ui.row().classes('w-full gap-4'):
            # Left column: Sprint overview and issues
            with ui.column().classes('flex-grow gap-4'):
                sprint_overview()
                issues_list()
            
            # Right column: AI insights
            with ui.column().classes('w-80 gap-4'):
                ai_insights_panel()
        
        # Connection status with better styling
        with ui.card().classes('w-full p-6 bg-blue-50 border-2 border-blue-200'):
            mode = 'Demo Mode' if app.storage.user.get('ticket_use_mock', False) else 'Live Jira Connection'
            icon = '🎭' if app.storage.user.get('ticket_use_mock', False) else '🔗'
            ui.label(f'{icon} {mode}').classes('text-xl font-bold text-gray-900 mb-3')
            
            if app.storage.user.get('ticket_use_mock', False):
                ui.label('Using sample data for demonstration. Toggle "Demo Mode" off and configure Jira credentials to connect to your real instance.').classes('text-base text-gray-900')
            else:
                ui.label('Set ATLASSIAN_HOST, ATLASSIAN_EMAIL, and ATLASSIAN_TOKEN in your .env file').classes('text-base text-gray-900')
    
    # Initial data load - run synchronously on first render
    ui.timer(0.1, lambda: asyncio.create_task(refresh_data()), once=True)
