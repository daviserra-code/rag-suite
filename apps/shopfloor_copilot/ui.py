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
from apps.shopfloor_copilot.screens.station_heatmap import render_station_heatmap_screen
from apps.shopfloor_copilot.screens.predictive_maintenance import render_predictive_maintenance_screen
from apps.shopfloor_copilot.screens.live_monitoring import render_live_monitoring_screen
from apps.shopfloor_copilot.screens.shift_handover import shift_handover_screen
from apps.shopfloor_copilot.screens.root_cause_analysis import root_cause_analysis_screen
from apps.shopfloor_copilot.screens.why_analysis import why_analysis_screen
from apps.shopfloor_copilot.screens.comparative_analytics import comparative_analytics_screen
from apps.shopfloor_copilot.screens.mobile_operator import render_mobile_operator
from apps.shopfloor_copilot.screens.advanced_rag import advanced_rag_screen
from apps.shopfloor_copilot.screens.energy_tracking import energy_tracking_screen
from apps.shopfloor_copilot.screens.digital_twin import digital_twin_screen
from apps.shopfloor_copilot.screens.opc_studio import opc_studio_screen
from apps.shopfloor_copilot.screens.opc_explorer import render_opc_explorer
from apps.shopfloor_copilot.screens.semantic_signals import render_semantic_signals
from apps.shopfloor_copilot.screens.diagnostics_explainer import render_diagnostics_explainer
from apps.shopfloor_copilot.screens.violations_management import render_violations_management

def build_ui():
    """Build the Shopfloor Copilot UI"""
    # Apply custom theme
    apply_shopfloor_theme()

    # Application Title (Global Header)
    with ui.header().classes('bg-blue-600 text-white shadow-md').style('padding: 0; height: 100px; display: flex; align-items: center;'):
        ui.html('<img src="/static/Gemini_Generated_Image_Logo_in_Blue2.png" style="height: 100px; width: auto;" />')

    # Tabs Layout with Enhanced Styling
    with ui.tabs().classes('w-full bg-gray-100') as tabs:
        tab_live = ui.tab('Live Monitoring', icon='sensors')
        tab_lines = ui.tab('Production Lines', icon='precision_manufacturing')
        tab_plant = ui.tab('Plant Overview', icon='factory')
        tab_operations = ui.tab('Operations', icon='dashboard')
        tab_stations = ui.tab('Station Heatmap', icon='grid_view')
        tab_maintenance = ui.tab('Predictive Maintenance', icon='build_circle')
        tab_handover = ui.tab('Shift Handover', icon='sync_alt')
        tab_rca = ui.tab('Root Cause Analysis', icon='troubleshoot')
        tab_why = ui.tab('5 Whys Analysis', icon='psychology')
        tab_compare = ui.tab('Comparative Analytics', icon='compare_arrows')
        tab_mobile = ui.tab('Mobile Operator', icon='phone_android')
        tab_ai_rag = ui.tab('AI Copilot', icon='psychology')
        tab_energy = ui.tab('Energy Tracking', icon='bolt')
        tab_twin = ui.tab('Digital Twin', icon='account_tree')
        tab_opc = ui.tab('OPC Studio', icon='settings_input_component')
        tab_opc_explorer = ui.tab('OPC Explorer', icon='explore')
        tab_semantic = ui.tab('Semantic Signals', icon='transform')
        tab_diagnostics = ui.tab('AI Diagnostics', icon='psychology_alt')
        tab_violations = ui.tab('Violations', icon='warning')
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
        # Live Monitoring (Tab 1)
        with ui.tab_panel(tab_live).classes('p-4'):
            render_live_monitoring_screen()

        # Production Lines Overview (Tab 2)
        with ui.tab_panel(tab_lines).classes('p-4'):
            build_production_lines_overview()

        # Plant Overview (Tab 2) - with navigation to Operations
        with ui.tab_panel(tab_plant).classes('p-4'):
            build_plant_overview(on_line_click=navigate_to_operations)

        # Operations Dashboard (Tab 3)
        with ui.tab_panel(tab_operations).classes('p-4'):
            build_operations_dashboard()

        # Station Heatmap (Tab 4)
        with ui.tab_panel(tab_stations).classes('p-4'):
            render_station_heatmap_screen()

        # Predictive Maintenance (Tab 5)
        with ui.tab_panel(tab_maintenance).classes('p-4'):
            render_predictive_maintenance_screen()

        # Shift Handover (Tab 6)
        with ui.tab_panel(tab_handover).classes('p-4'):
            shift_handover_screen()

        # Root Cause Analysis (Tab 7)
        with ui.tab_panel(tab_rca).classes('p-4'):
            root_cause_analysis_screen()

        # 5 Whys Analysis (Tab 8)
        with ui.tab_panel(tab_why).classes('p-4'):
            why_analysis_screen()

        # Comparative Analytics (Tab 9)
        with ui.tab_panel(tab_compare).classes('p-4'):
            comparative_analytics_screen()

        # Mobile Operator (Tab 10)
        with ui.tab_panel(tab_mobile).classes('p-4'):
            render_mobile_operator()

        # Advanced RAG / AI Copilot (Tab 11)
        with ui.tab_panel(tab_ai_rag).classes('p-4'):
            advanced_rag_screen()

        # Energy Tracking (Tab 12)
        with ui.tab_panel(tab_energy).classes('p-4'):
            energy_tracking_screen()

        # Digital Twin Simulation (Tab 13)
        with ui.tab_panel(tab_twin).classes('p-4'):
            digital_twin_screen()

        # OPC Studio Control Panel (Tab 14) - Phase B
        with ui.tab_panel(tab_opc).classes('p-4'):
            opc_studio_screen()

        # OPC Explorer (Tab 15) - Sprint 1
        with ui.tab_panel(tab_opc_explorer).classes('p-4'):
            render_opc_explorer()

        # Semantic Signals (Tab 16) - Sprint 2
        with ui.tab_panel(tab_semantic).classes('p-4'):
            render_semantic_signals()

        # AI Diagnostics (Tab 17) - Sprint 3
        with ui.tab_panel(tab_diagnostics).classes('p-4'):
            render_diagnostics_explainer()

        # Violations Management (Tab 18) - Sprint 4
        with ui.tab_panel(tab_violations).classes('p-4'):
            render_violations_management()

        # Operator Q&A (Tab 19)
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
