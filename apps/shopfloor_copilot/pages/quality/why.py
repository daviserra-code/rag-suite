from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.why_analysis import why_analysis_screen

@ui.page('/quality/why')
def why_analysis_page():
    with layout_shell(title="5 Whys Analysis"):
        create_page_header(
            "5 Whys Analysis",
            "Deep-dive problem solving methodology",
            "psychology"
        )
        why_analysis_screen()
