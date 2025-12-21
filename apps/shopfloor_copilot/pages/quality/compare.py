from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.comparative_analytics import comparative_analytics_screen

@ui.page('/quality/compare')
def comparative_analytics_page():
    with layout_shell(title="Comparative Analytics"):
        create_page_header(
            "Comparative Analytics",
            "Line and station performance comparisons",
            "compare_arrows"
        )
        comparative_analytics_screen()
