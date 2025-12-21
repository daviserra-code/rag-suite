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
    drawer_content: Optional[Callable] = None,
    theme: str = "dark"
) -> ui.column:
    """
    Create the standard UI shell with header, drawer, and content area.
    Supports theme boundaries to separate dark shell from legacy light pages.
    
    Args:
        title: Page title to display in header
        show_drawer: Whether to show the left navigation drawer
        drawer_content: Optional custom drawer content function
        theme: "dark" for new pages, "legacy" for light-styled legacy pages
    
    Returns:
        ui.column container for page content
    """
    
    # Apply dark background for dark theme pages
    if theme == "dark":
        ui.query('body').style('background: #0f172a; color: #e2e8f0;')
        
        # Inject global dark theme CSS for all cards and containers
        ui.add_head_html('''
        <style>
            /* Dark theme for all cards */
            .nicegui-card, .q-card {
                background: #1e293b !important;
                border: 1px solid #334155 !important;
                color: #e2e8f0 !important;
            }
            
            /* Dark theme for inputs and selects */
            .q-field__control {
                background: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            .q-field__label {
                color: #94a3b8 !important;
            }
            
            /* Dark theme for tables */
            .q-table, .q-table__card {
                background: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            .q-table thead th {
                color: #f1f5f9 !important;
                background: #0f172a !important;
            }
            
            .q-table tbody td {
                color: #e2e8f0 !important;
                border-color: #334155 !important;
            }
            
            /* Dark theme for buttons (non-colored) */
            .q-btn:not(.bg-primary):not(.bg-secondary):not(.bg-positive):not(.bg-negative):not(.bg-warning) {
                background: #334155 !important;
                color: #e2e8f0 !important;
            }
            
            /* Dark theme for dialogs and menus */
            .q-menu, .q-dialog__backdrop {
                background: rgba(15, 23, 42, 0.75) !important;
            }
            
            .q-menu .q-item {
                color: #e2e8f0 !important;
            }
            
            .q-menu .q-item:hover {
                background: #334155 !important;
            }
        </style>
        ''')
    
    # Header with logo and navigation - dark industrial style
    with ui.header().classes('text-white').style(
        'background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%); '
        'padding: 0; height: 100px; display: flex; align-items: center; justify-content: space-between; '
        'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);'
    ):
        with ui.row().classes('items-center gap-4 px-4'):
            # Logo
            ui.html('<img src="/static/Gemini_Generated_Image_Logo_in_Blue2.png" style="height: 80px; width: auto; background: #1e3a8a; padding: 4px; border-radius: 4px;" />')
            
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
        # Dark drawer for dark theme, light for legacy
        drawer_bg = '#1e293b' if theme == "dark" else 'bg-gray-100'
        drawer_border = 'border-right: 1px solid rgba(255, 255, 255, 0.08);' if theme == "dark" else ''
        
        with ui.left_drawer(value=True).style(
            f'width: 280px; background: {drawer_bg}; {drawer_border}'
        ) as drawer:
            
            if drawer_content:
                drawer_content()
            else:
                # Default drawer: macro-categories navigation
                render_default_drawer(theme)
    
    # Content container with theme boundary
    if theme == "legacy":
        # Bridge background: gradient from dark to darker slate
        ui.query('body').style(
            'background: linear-gradient(to bottom, #0f172a 0%, #1e293b 50%, #334155 100%);'
        )
        
        # Outer container with padding (dark gradient background shows through)
        with ui.column().style(
            'width: 100%; '
            'min-height: calc(100vh - 100px); '
            'padding: 24px;'
        ):
            # Inner surface panel: off-white with rounded corners and shadow
            content = ui.column().style(
                'background: #f8fafc; '
                'border: 1px solid rgba(0, 0, 0, 0.08); '
                'border-radius: 12px; '
                'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); '
                'padding: 24px; '
                'width: 100%; '
                'min-height: calc(100vh - 148px);'
            )
    else:
        # Dark theme content - apply dark background and proper padding
        content = ui.column().classes('w-full').style(
            'background: #0f172a; '
            'min-height: calc(100vh - 100px); '
            'padding: 24px; '
            'color: #e2e8f0;'
        )
    
    return content


def render_default_drawer(theme: str = "dark"):
    """Render default navigation drawer with macro-categories"""
    
    if theme == "dark":
        # Dark themed drawer
        ui.label('Navigation').classes('text-lg font-bold px-4 pt-4 pb-2').style('color: #f1f5f9;')
        ui.separator().style('background: rgba(255, 255, 255, 0.08);')
        
        for category_name, category_data in MACRO_CATEGORIES.items():
            category_color = get_category_color(category_name)
            state_indicator = get_category_state(category_name)
            
            # Category expansion with state indicator
            with ui.row().classes('w-full items-center gap-2').style(
                f'background: #1e293b; '
                f'border-left: 3px solid {category_color}; '
                f'margin-bottom: 8px; '
                f'border-radius: 6px;'
            ):
                # State indicator dot
                ui.html(f'<div style="width: 8px; height: 8px; border-radius: 50%; background: {state_indicator}; margin-left: 8px;"></div>')
                
                with ui.expansion(category_name, icon=category_data["icon"]).classes('flex-1').style('background: transparent;'):
                    for page in category_data["pages"]:
                        # Page link button
                        with ui.row().classes('w-full items-center gap-2 px-3 py-2 cursor-pointer').style(
                            'transition: background 0.2s ease;'
                        ).on('click', lambda p=page: ui.navigate.to(p["route"])):
                            ui.icon(page["icon"]).style(f'font-size: 20px; color: {category_color};')
                            with ui.column().classes('flex-1'):
                                ui.label(page["name"]).classes('text-sm font-medium').style('color: #f1f5f9;')
                                ui.label(page["description"]).classes('text-xs').style('color: #94a3b8;')
        
        # Legacy link at bottom
        ui.separator().classes('mt-4').style('background: rgba(255, 255, 255, 0.08);')
        with ui.row().classes('w-full items-center gap-2 px-4 py-2 cursor-pointer').on('click', lambda: ui.navigate.to('/legacy')):
            ui.icon('view_module').style('color: #94a3b8;')
            ui.label('Legacy 23-Tab View').classes('text-sm').style('color: #f1f5f9;')
    else:
        # Light themed drawer (legacy)
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


def get_category_color(category_name: str) -> str:
    """Get accent color for each category"""
    colors = {
        "Operations": "#3b82f6",      # blue
        "Quality": "#a855f7",          # purple
        "Maintenance": "#f59e0b",      # amber
        "Connectivity": "#06b6d4",     # cyan
        "Intelligence": "#8b5cf6",     # violet
        "Analytics": "#10b981",        # emerald
        "Advanced": "#6b7280",         # gray
    }
    return colors.get(category_name, "#3b82f6")


def get_category_state(category_name: str) -> str:
    """Get state indicator color for each category (mock logic)"""
    states = {
        "Operations": "#10b981",      # green - live
        "Quality": "#10b981",          # green - ok
        "Maintenance": "#f59e0b",      # amber - alerts
        "Connectivity": "#10b981",     # green - connected
        "Intelligence": "#8b5cf6",     # violet - AI active
        "Analytics": "#10b981",        # green - running
        "Advanced": "#6b7280",         # gray - idle
    }
    return states.get(category_name, "#6b7280")


def create_page_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None, theme: str = "dark"):
    """Create a standard page header with title and optional subtitle
    
    Args:
        title: Page title
        subtitle: Optional subtitle/description
        icon: Optional icon name
        theme: "dark" or "legacy" - adjusts text colors for readability
    """
    # Theme-aware colors
    if theme == "dark":
        title_color = '#f1f5f9'  # slate-100
        subtitle_color = '#94a3b8'  # slate-400
        icon_color = '#3b82f6'  # blue-500
    else:
        title_color = '#0f172a'  # slate-900
        subtitle_color = '#64748b'  # slate-500
        icon_color = '#3b82f6'  # blue-500
    
    with ui.row().classes('w-full items-center gap-4 mb-6'):
        if icon:
            ui.icon(icon).classes('text-4xl').style(f'color: {icon_color};')
        with ui.column().classes('flex-1'):
            ui.label(title).classes('text-3xl font-bold').style(f'color: {title_color};')
            if subtitle:
                ui.label(subtitle).classes('text-lg').style(f'color: {subtitle_color};')
