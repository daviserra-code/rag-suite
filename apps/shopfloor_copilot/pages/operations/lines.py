from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.production_lines import build_production_lines_overview

@ui.page('/operations/lines')
def production_lines_page():
    with layout_shell(title="Production Lines"):
        create_page_header(
            "Production Lines",
            "Line performance overview and comparison",
            "precision_manufacturing"
        )
        build_production_lines_overview()
