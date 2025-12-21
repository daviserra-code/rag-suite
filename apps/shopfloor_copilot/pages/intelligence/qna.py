from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.operator_qna_interactive import build_operator_qna

@ui.page('/intelligence/qna')
def operator_qna_page():
    with layout_shell(title="Operator Q&A"):
        create_page_header(
            "Operator Q&A",
            "Interactive operator assistance",
            "question_answer"
        )
        build_operator_qna()
