from nicegui import ui, app
from apps.shopfloor_copilot.theme import apply_shopfloor_theme
from apps.shopfloor_copilot.screens.production_lines import build_production_lines_overview
from apps.shopfloor_copilot.screens.plant_overview import build_plant_overview
from apps.shopfloor_copilot.screens.operations_dashboard import build_operations_dashboard
from apps.shopfloor_copilot.screens.qna_filters import build_qna_filters
from apps.shopfloor_copilot.screens.answer_citations import build_answer_citations
from apps.shopfloor_copilot.screens.ticket_insights import build_ticket_insights
from apps.shopfloor_copilot.screens.operator_qna_interactive import build_operator_qna
from apps.shopfloor_copilot.screens.kpi_dashboard_interactive import build_kpi_dashboard
from apps.shopfloor_copilot.screens.reports import render_reports_screen

def build_ui():
    """Build the Shopfloor Copilot UI"""
    # Apply custom theme
    apply_shopfloor_theme()

    # Application Title (Global Header)
    with ui.header().classes('bg-blue-600 text-white shadow-md').style('padding: 0; height: 100px; display: flex; align-items: center;'):
        ui.html('<img src="/static/Gemini_Generated_Image_Logo_in_Blue2.png" style="height: 100px; width: auto;" />')

    # Tabs Layout with Enhanced Styling
    with ui.tabs().classes('w-full bg-gray-100') as tabs:
        tab_lines = ui.tab('Production Lines', icon='precision_manufacturing')
        tab_plant = ui.tab('Plant Overview', icon='factory')
        tab_operations = ui.tab('Operations', icon='dashboard')
        tab_qna = ui.tab('Operator Q&A', icon='question_answer')
        tab_kpi = ui.tab('KPI Dashboard', icon='analytics')
        tab_filters = ui.tab('Q&A Filters', icon='filter_list')
        tab_citations = ui.tab('Answer Citations', icon='book')
        tab_tickets = ui.tab('Ticket Insights', icon='confirmation_number')
        tab_reports = ui.tab('Reports', icon='description')

    # Container for operations tab content (for programmatic switching)
    operations_container = ui.tab_panels(tabs, value=tab_lines).classes('w-full p-4 bg-white rounded shadow')

    # Navigation handler for Plant Overview to Operations
    def navigate_to_operations(line_id=None):
        """Switch to Operations Dashboard tab"""
        operations_container.set_value(tab_operations)
        # TODO: Could pass line_id to operations dashboard to pre-select that line

    # Tab Panels with Individual Screen Content
    with operations_container:
        # Production Lines Overview (Tab 1)
        with ui.tab_panel(tab_lines).classes('p-4'):
            build_production_lines_overview()

        # Plant Overview (Tab 2) - with navigation to Operations
        with ui.tab_panel(tab_plant).classes('p-4'):
            build_plant_overview(on_line_click=navigate_to_operations)

        # Operations Dashboard (Tab 3)
        with ui.tab_panel(tab_operations).classes('p-4'):
            build_operations_dashboard()

        # Operator Q&A (Tab 4)
        with ui.tab_panel(tab_qna).classes('p-4'):
            build_operator_qna()

        # KPI Dashboard (Tab 5)
        with ui.tab_panel(tab_kpi).classes('p-4'):
            build_kpi_dashboard()

        # Q&A Filters (Tab 6)
        with ui.tab_panel(tab_filters).classes('p-4'):
            build_qna_filters()

        # Answer Citations (Tab 7)
        with ui.tab_panel(tab_citations).classes('p-4'):
            build_answer_citations()

        # Ticket Insights (Tab 8)
        with ui.tab_panel(tab_tickets).classes('p-4'):
            build_ticket_insights()

        # Reports (Tab 9)
        with ui.tab_panel(tab_reports).classes('p-4'):
            render_reports_screen()
