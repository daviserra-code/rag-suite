from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.qna_filters import build_qna_filters

@ui.page('/intelligence/filters')
def qna_filters_page():
    with layout_shell(title="Q&A Filters", theme="dark"):
        create_page_header(
            "Q&A Filters",
            "Advanced search refinement and filtering",
            "filter_list",
            theme="dark"
        )
        build_qna_filters()
