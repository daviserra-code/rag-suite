"""
Landing Page - Tile-based navigation with search
"""

from nicegui import ui
from apps.shopfloor_copilot.ui_shell import MACRO_CATEGORIES, get_all_routes
from apps.shopfloor_copilot.theme import apply_shopfloor_theme


@ui.page('/')
def landing_page():
    """Landing page with tile grid and search"""
    
    apply_shopfloor_theme()
    
    # Apply dark industrial background
    ui.query('body').style('background: #0f172a; color: #e2e8f0;')
    
    # Header with logo - darker gradient for control room feel
    with ui.header().classes('text-white').style(
        'background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%); '
        'padding: 0; height: 100px; display: flex; align-items: center; justify-content: space-between; '
        'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);'
    ):
        with ui.row().classes('items-center gap-4 px-4'):
            ui.html('<img src="/static/Gemini_Generated_Image_Logo_in_Blue2.png" style="height: 80px; width: auto; background: #1e3a8a; padding: 4px; border-radius: 4px;" />')
            ui.label('Shopfloor Copilot').classes('text-3xl font-bold')
        
        # Right side buttons
        with ui.row().classes('items-center gap-2 px-4'):
            ui.button('Navigation', icon='menu', on_click=lambda: right_drawer.toggle()).props('flat color=white')
            ui.button('Legacy UI', icon='view_module', on_click=lambda: ui.navigate.to('/legacy')).props('flat color=white')
    
    # Right drawer navigation - industrial dark theme
    with ui.right_drawer(value=False).style(
        'background: #1e293b; '
        'border-left: 1px solid rgba(255, 255, 255, 0.08); '
        'width: 320px;'
    ) as right_drawer:
        # Drawer header
        with ui.row().classes('w-full items-center gap-3 p-4').style(
            'background: #0f172a; '
            'border-bottom: 1px solid rgba(255, 255, 255, 0.08);'
        ):
            ui.icon('dashboard').style('font-size: 28px; color: #3b82f6;')
            ui.label('Navigation').classes('text-xl font-semibold').style('color: #f1f5f9;')
        
        # Categories navigation
        with ui.column().classes('w-full p-2').style('overflow-y: auto;'):
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
                    
                    with ui.expansion(category_name, icon=category_data["icon"]).classes('flex-1').style(
                        f'background: transparent;'
                    ):
                        # Style the expansion header
                        ui.add_head_html(f'''
                            <style>
                            .q-expansion-item__container {{
                                color: #f1f5f9 !important;
                            }}
                            </style>
                        ''')
                        
                        for page in category_data["pages"]:
                            # Page link
                            with ui.row().classes('w-full items-center gap-2 px-3 py-2 cursor-pointer').style(
                                'transition: all 0.2s ease;'
                            ).on('click', lambda p=page: ui.navigate.to(p["route"])):
                                ui.icon(page["icon"]).style(f'font-size: 20px; color: {category_color};')
                                with ui.column().classes('flex-1'):
                                    ui.label(page["name"]).classes('text-sm font-medium').style('color: #f1f5f9;')
                                    ui.label(page["description"]).classes('text-xs').style('color: #94a3b8;')

    
    # Main content
    with ui.column().classes('w-full p-6 max-w-7xl mx-auto'):
        
        # Welcome message - reduced hero emphasis for control room feel
        ui.label('Shopfloor Copilot').classes('text-3xl font-semibold mb-1').style('color: #e2e8f0;')
        ui.label('Manufacturing execution · Real-time OEE monitoring').classes('text-base mb-6').style('color: #64748b;')
        
        # Sprint 4 Banner - NEW!
        with ui.card().classes('w-full mb-6').style(
            'background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); '
            'border: 2px solid #60a5fa; '
            'box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);'
        ).on('click', lambda: ui.navigate.to('/settings/profiles')):
            with ui.row().classes('w-full items-center gap-4 p-4 cursor-pointer'):
                ui.icon('rocket_launch', size='3rem').classes('text-white')
                with ui.column().classes('flex-grow gap-1'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label('🚀 NEW: Sprint 4 — Domain Profiles').classes('text-xl font-bold text-white')
                        ui.badge('LIVE', color='green').classes('text-sm')
                    ui.label('Switch between Aerospace & Defence, Pharma, and Automotive profiles').classes('text-sm text-blue-100')
                    ui.label('Material Intelligence · Reason Taxonomy · Profile-Aware AI').classes('text-xs text-blue-200')
                ui.icon('arrow_forward', size='lg').classes('text-white')
        
        # Search bar - dark themed
        search_input = ui.input(
            placeholder='Search lines, stations, features…',
            on_change=lambda e: filter_tiles(e.value)
        ).props('outlined clearable dark bg-color=grey-9').style(
            'background: #1e293b; border-radius: 8px;'
        ).classes('w-full mb-6')
        search_input.props('prepend-icon=search')
        
        # Tiles container
        tiles_container = ui.column().classes('w-full gap-6')
        
        # Render all categories
        def render_all_tiles():
            """Render all tiles grouped by category"""
            tiles_container.clear()
            with tiles_container:
                for category_name, category_data in MACRO_CATEGORIES.items():
                    # Category header with accent color
                    category_color = get_category_color(category_name)
                    with ui.row().classes('w-full items-center gap-2 mb-3'):
                        ui.icon(category_data["icon"]).style(f'font-size: 28px; color: {category_color};')
                        ui.label(category_name).classes('text-xl font-semibold').style('color: #f1f5f9;')
                    
                    # Tiles grid - denser for control room feel
                    with ui.grid(columns='repeat(auto-fill, minmax(320px, 1fr))').classes('w-full gap-3 mb-5'):
                        for page in category_data["pages"]:
                            render_tile(page, category_name)
        
        # Initial render
        render_all_tiles()
        
        def filter_tiles(search_text: str):
            """Filter tiles based on search text"""
            if not search_text or search_text.strip() == '':
                render_all_tiles()
                return
            
            search_lower = search_text.lower()
            tiles_container.clear()
            
            # Find matching pages
            matching_pages = []
            for category_name, category_data in MACRO_CATEGORIES.items():
                for page in category_data["pages"]:
                    if (search_lower in page["name"].lower() or 
                        search_lower in page["description"].lower() or
                        search_lower in category_name.lower()):
                        matching_pages.append({
                            **page,
                            "category": category_name,
                            "category_icon": category_data["icon"]
                        })
            
            # Render results
            with tiles_container:
                if matching_pages:
                    ui.label(f'Found {len(matching_pages)} results').classes('text-lg font-semibold mb-4').style('color: #f1f5f9;')
                    
                    with ui.grid(columns='repeat(auto-fill, minmax(320px, 1fr))').classes('w-full gap-3'):
                        for page in matching_pages:
                            render_tile(page, page["category"])
                else:
                    ui.label('No results found').classes('text-lg').style('color: #94a3b8;')
                    ui.label('Try searching for: Operations, Quality, Maintenance, OPC, AI Diagnostics').classes('text-sm').style('color: #64748b;')


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
        "Settings": "#ef4444",         # red - Sprint 4
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
        "Settings": "#ef4444",         # red - new/important
    }
    return states.get(category_name, "#6b7280")


def is_primary_tile(page_name: str) -> bool:
    """Determine if a tile is primary (high operational priority)"""
    primary_tiles = [
        "Live Monitoring",
        "AI Diagnostics",
        "AI Copilot",
        "Operations Dashboard",
    ]
    return page_name in primary_tiles


def render_tile(page: dict, category_name: str):
    """Render a single feature tile with industrial dark theme"""
    
    def navigate():
        ui.navigate.to(page["route"])
    
    accent_color = get_category_color(category_name)
    is_primary = is_primary_tile(page["name"])
    
    # Primary tiles have stronger border and slightly different styling
    border_width = '5px' if is_primary else '4px'
    border_opacity = '0.12' if is_primary else '0.08'
    
    # Dark card with left accent bar and hover effect
    card = ui.card().classes('cursor-pointer').style(
        f'background: #1e293b; '
        f'border: 1px solid rgba(255, 255, 255, {border_opacity}); '
        f'border-left: {border_width} solid {accent_color}; '
        f'border-radius: 8px; '
        f'padding: 16px; '
        f'transition: all 0.2s ease; '
    ).on('click', navigate)
    
    # Hover effect
    card.on('mouseenter', lambda: card.style(
        f'background: #1e293b; '
        f'border: 1px solid rgba(255, 255, 255, 0.16); '
        f'border-left: {border_width} solid {accent_color}; '
        f'border-radius: 8px; '
        f'padding: 16px; '
        f'box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2); '
        f'transform: translateY(-2px); '
        f'transition: all 0.2s ease; '
    ))
    card.on('mouseleave', lambda: card.style(
        f'background: #1e293b; '
        f'border: 1px solid rgba(255, 255, 255, {border_opacity}); '
        f'border-left: {border_width} solid {accent_color}; '
        f'border-radius: 8px; '
        f'padding: 16px; '
        f'transition: all 0.2s ease; '
    ))
    
    with card:
        # Icon and title with badge for primary tiles
        with ui.row().classes('w-full items-center gap-2 mb-2'):
            ui.icon(page["icon"]).style(f'font-size: 26px; color: {accent_color};')
            ui.label(page["name"]).classes('text-base font-semibold').style('color: #f1f5f9;')
            
            # Badge for primary tiles
            if is_primary:
                badge_text = 'LIVE' if 'Monitoring' in page["name"] or 'Dashboard' in page["name"] else 'AI'
                ui.label(badge_text).classes('text-xs font-bold px-2 py-0.5').style(
                    f'background: {accent_color}; color: #0f172a; border-radius: 4px;'
                )
        
        # Description
        ui.label(page["description"]).classes('text-sm mb-3').style('color: #94a3b8; line-height: 1.4;')
        
        # Open button
        ui.button('Open', icon='arrow_forward', on_click=navigate).props('flat').style(
            f'color: {accent_color}; width: 100%;'
        )
