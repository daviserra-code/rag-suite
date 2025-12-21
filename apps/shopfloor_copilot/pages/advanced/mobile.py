from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.mobile_operator import render_mobile_operator

@ui.page('/advanced/mobile')
def mobile_operator_page():
    with layout_shell(title="Mobile Operator"):
        create_page_header(
            "Mobile Operator",
            "Mobile-optimized operator interface",
            "phone_android"
        )
        render_mobile_operator()
