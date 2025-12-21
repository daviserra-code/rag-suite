"""
UI Shell - Shared Layout for Shopfloor Copilot
Provides header, left drawer navigation, and content container
"""

from nicegui import ui
from typing import Optional, Callable


# Macro-categories with routes and icons
MACRO_CATEGORIES = {
    "Operations": {
        "icon": "dashboard",
        "pages": [
            {"name": "Live Monitoring", "route": "/operations/live", "icon": "sensors", "description": "Real-time OEE monitoring"},
            {"name": "Production Lines", "route": "/operations/lines", "icon": "precision_manufacturing", "description": "Line performance overview"},
            {"name": "Plant Overview", "route": "/operations/plant", "icon": "factory", "description": "Multi-line plant view"},
            {"name": "Operations Dashboard", "route": "/operations/dashboard", "icon": "dashboard", "description": "Shift operations control"},
            {"name": "Station Heatmap", "route": "/operations/heatmap", "icon": "grid_view", "description": "Station performance grid"},
        ]
    },
    "Quality": {
        "icon": "verified",
        "pages": [
            {"name": "Root Cause Analysis", "route": "/quality/rca", "icon": "troubleshoot", "description": "Issue analysis and tracking"},
            {"name": "5 Whys Analysis", "route": "/quality/why", "icon": "psychology", "description": "Deep-dive problem solving"},
            {"name": "Comparative Analytics", "route": "/quality/compare", "icon": "compare_arrows", "description": "Line/station comparisons"},
        ]
    },
    "Maintenance": {
        "icon": "build",
        "pages": [
            {"name": "Predictive Maintenance", "route": "/maintenance/predictive", "icon": "build_circle", "description": "Failure prediction"},
            {"name": "AI Diagnostics", "route": "/maintenance/diagnostics", "icon": "psychology_alt", "description": "Sprint 3: Explainable diagnostics"},
            {"name": "Shift Handover", "route": "/maintenance/handover", "icon": "sync_alt", "description": "Shift transition notes"},
        ]
    },
    "Connectivity": {
        "icon": "settings_input_component",
        "pages": [
            {"name": "OPC Studio", "route": "/connectivity/opc", "icon": "settings_input_component", "description": "OPC UA control panel"},
            {"name": "OPC Explorer", "route": "/connectivity/opc-explorer", "icon": "explore", "description": "Sprint 1: UAExpert-like browser"},
            {"name": "Semantic Signals", "route": "/connectivity/mapping", "icon": "transform", "description": "Sprint 2: Kepware-like mapping"},
        ]
    },
    "Intelligence": {
        "icon": "psychology",
        "pages": [
            {"name": "AI Copilot", "route": "/intelligence/copilot", "icon": "psychology", "description": "Advanced RAG Q&A"},
            {"name": "Operator Q&A", "route": "/intelligence/qna", "icon": "question_answer", "description": "Interactive assistant"},
            {"name": "Q&A Filters", "route": "/intelligence/filters", "icon": "filter_list", "description": "Search refinement"},
            {"name": "Answer Citations", "route": "/intelligence/citations", "icon": "book", "description": "Source verification"},
        ]
    },
    "Analytics": {
        "icon": "analytics",
        "pages": [
            {"name": "KPI Dashboard", "route": "/analytics/kpi", "icon": "analytics", "description": "Key performance indicators"},
            {"name": "Reports", "route": "/analytics/reports", "icon": "description", "description": "Scheduled reports"},
            {"name": "Energy Tracking", "route": "/analytics/energy", "icon": "bolt", "description": "Power consumption"},
        ]
    },
    "Advanced": {
        "icon": "account_tree",
        "pages": [
            {"name": "Digital Twin", "route": "/advanced/twin", "icon": "account_tree", "description": "Simulation environment"},
            {"name": "Ticket Insights", "route": "/advanced/tickets", "icon": "confirmation_number", "description": "JIRA integration"},
            {"name": "Mobile Operator", "route": "/advanced/mobile", "icon": "phone_android", "description": "Mobile-optimized view"},
        ]
    },
}


def get_all_routes():
    """Get flat list of all routes for search"""
    routes = []
    for category_name, category_data in MACRO_CATEGORIES.items():
        for page in category_data["pages"]:
            routes.append({
                "name": page["name"],
                "route": page["route"],
                "icon": page["icon"],
                "description": page["description"],
                "category": category_name,
                "category_icon": category_data["icon"]
            })
    return routes


def layout_shell(
    title: str,
    show_drawer: bool = True,
    drawer_content: Optional[Callable] = None
) -> ui.column:
    """
    Create the standard UI shell with header, drawer, and content area.
    
    Args:
        title: Page title to display in header
        show_drawer: Whether to show the left navigation drawer
        drawer_content: Optional custom drawer content function
    
    Returns:
        ui.column container for page content
    """
    
    # Header with logo and navigation
    with ui.header().classes('bg-blue-600 text-white shadow-md').style(
        'padding: 0; height: 100px; display: flex; align-items: center; justify-content: space-between;'
    ):
        with ui.row().classes('items-center gap-4 px-4'):
            # Logo
            ui.html('<img src="/static/Gemini_Generated_Image_Logo_in_Blue2.png" style="height: 80px; width: auto;" />')
            
            # Title
            ui.label(title).classes('text-2xl font-bold')
        
        # Right side navigation
        with ui.row().classes('items-center gap-2 px-4'):
            # Home button
            ui.button('Home', icon='home', on_click=lambda: ui.navigate.to('/')).props('flat color=white')
            
            # Legacy tabs link
            ui.button('Legacy UI', icon='view_module', on_click=lambda: ui.navigate.to('/legacy')).props('flat color=white')
    
    # Main layout with drawer + content
    if show_drawer:
        with ui.left_drawer(value=True).classes('bg-gray-100') as drawer:
            drawer.style('width: 280px')
            
            if drawer_content:
                drawer_content()
            else:
                # Default drawer: macro-categories navigation
                render_default_drawer()
    
    # Content container
    content = ui.column().classes('w-full p-6')
    
    return content


def render_default_drawer():
    """Render default navigation drawer with macro-categories"""
    
    ui.label('Navigation').classes('text-lg font-bold px-4 pt-4 pb-2')
    ui.separator()
    
    for category_name, category_data in MACRO_CATEGORIES.items():
        # Category expansion
        with ui.expansion(category_name, icon=category_data["icon"]).classes('w-full'):
            for page in category_data["pages"]:
                # Page link button
                with ui.row().classes('w-full items-center gap-2 px-2 py-1 hover:bg-gray-200 cursor-pointer').on('click', lambda p=page: ui.navigate.to(p["route"])):
                    ui.icon(page["icon"]).classes('text-gray-600')
                    with ui.column().classes('flex-1'):
                        ui.label(page["name"]).classes('text-sm font-medium')
                        ui.label(page["description"]).classes('text-xs text-gray-500')
    
    # Legacy link at bottom
    ui.separator().classes('mt-4')
    with ui.row().classes('w-full items-center gap-2 px-4 py-2 hover:bg-gray-200 cursor-pointer').on('click', lambda: ui.navigate.to('/legacy')):
        ui.icon('view_module').classes('text-gray-600')
        ui.label('Legacy 23-Tab View').classes('text-sm')


def create_page_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
    """Create a standard page header with title and optional subtitle"""
    with ui.row().classes('w-full items-center gap-4 mb-6'):
        if icon:
            ui.icon(icon).classes('text-4xl text-blue-600')
        with ui.column().classes('flex-1'):
            ui.label(title).classes('text-3xl font-bold')
            if subtitle:
                ui.label(subtitle).classes('text-lg text-gray-600')
