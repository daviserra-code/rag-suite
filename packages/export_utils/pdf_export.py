"""PDF Export Utilities using WeasyPrint"""

from weasyprint import HTML, CSS
from datetime import datetime
from typing import Dict, List, Optional
import io


def generate_pdf_header(title: str, subtitle: str = None) -> str:
    """Generate PDF header HTML"""
    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ''
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    return f"""
    <div class="header">
        <div>
            <h1>{title}</h1>
            {subtitle_html}
        </div>
        <div class="timestamp">
            <p>Generated: {timestamp}</p>
        </div>
    </div>
    """


def generate_pdf_table(data: List[Dict], columns: List[str] = None, title: str = None) -> str:
    """Generate HTML table for PDF"""
    if not data:
        return "<p>No data available</p>"
    
    if not columns:
        columns = list(data[0].keys())
    
    title_html = f'<h2>{title}</h2>' if title else ''
    
    # Build table HTML
    header_row = ''.join([f'<th>{col.replace("_", " ").title()}</th>' for col in columns])
    
    body_rows = []
    for row in data:
        cells = ''.join([f'<td>{row.get(col, "")}</td>' for col in columns])
        body_rows.append(f'<tr>{cells}</tr>')
    
    return f"""
    {title_html}
    <table>
        <thead>
            <tr>{header_row}</tr>
        </thead>
        <tbody>
            {''.join(body_rows)}
        </tbody>
    </table>
    """


def generate_pdf_metric_cards(metrics: List[Dict]) -> str:
    """Generate metric cards for PDF"""
    cards_html = []
    for metric in metrics:
        cards_html.append(f"""
        <div class="metric-card">
            <div class="metric-label">{metric.get('label', '')}</div>
            <div class="metric-value">{metric.get('value', '')}</div>
            <div class="metric-subtitle">{metric.get('subtitle', '')}</div>
        </div>
        """)
    
    return f'<div class="metrics-row">{"".join(cards_html)}</div>'


def generate_pdf_section(title: str, content: str) -> str:
    """Generate a section with title and content"""
    return f"""
    <div class="section">
        <h2>{title}</h2>
        <div class="section-content">
            {content}
        </div>
    </div>
    """


def export_to_pdf(
    title: str,
    content_html: str,
    subtitle: str = None,
    logo_path: str = None,
    filename: str = None
) -> bytes:
    """
    Export HTML content to PDF
    
    Args:
        title: Report title
        content_html: HTML content body
        subtitle: Optional subtitle
        logo_path: Optional path to logo image
        filename: Optional filename (auto-generated if not provided)
    
    Returns:
        PDF content as bytes
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
    
    # Logo HTML if provided
    logo_html = f'<img src="{logo_path}" class="logo" />' if logo_path else ''
    
    # Complete HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
    </head>
    <body>
        {logo_html}
        {generate_pdf_header(title, subtitle)}
        {content_html}
        <div class="footer">
            <p>Shopfloor Copilot - Production Analytics Report</p>
            <p class="page-number">Page <span class="page"></span> of <span class="pages"></span></p>
        </div>
    </body>
    </html>
    """
    
    # CSS styling
    css_content = """
    @page {
        size: A4;
        margin: 2cm;
        @bottom-right {
            content: counter(page) " / " counter(pages);
        }
    }
    
    body {
        font-family: Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.5;
        color: #333;
    }
    
    .logo {
        max-width: 150px;
        margin-bottom: 20px;
    }
    
    .header {
        border-bottom: 3px solid #0F7C7C;
        padding-bottom: 15px;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    
    .header h1 {
        margin: 0;
        font-size: 24pt;
        color: #0F7C7C;
    }
    
    .header .subtitle {
        margin: 5px 0 0 0;
        font-size: 12pt;
        color: #666;
    }
    
    .header .timestamp {
        text-align: right;
        font-size: 9pt;
        color: #888;
    }
    
    .header .timestamp p {
        margin: 0;
    }
    
    h2 {
        font-size: 14pt;
        color: #0F7C7C;
        margin-top: 25px;
        margin-bottom: 15px;
        border-bottom: 1px solid #ccc;
        padding-bottom: 5px;
    }
    
    h3 {
        font-size: 12pt;
        color: #333;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    .metrics-row {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .metric-card {
        flex: 1;
        min-width: 150px;
        padding: 15px;
        background: #f5f5f5;
        border-left: 4px solid #0F7C7C;
        border-radius: 4px;
    }
    
    .metric-label {
        font-size: 9pt;
        color: #666;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    
    .metric-value {
        font-size: 20pt;
        font-weight: bold;
        color: #0F7C7C;
        margin-bottom: 3px;
    }
    
    .metric-subtitle {
        font-size: 8pt;
        color: #888;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 25px;
        font-size: 9pt;
    }
    
    th {
        background: #0F7C7C;
        color: white;
        padding: 10px;
        text-align: left;
        font-weight: bold;
    }
    
    td {
        padding: 8px 10px;
        border-bottom: 1px solid #ddd;
    }
    
    tr:nth-child(even) {
        background: #f9f9f9;
    }
    
    .section {
        margin-bottom: 30px;
        page-break-inside: avoid;
    }
    
    .section-content {
        padding-left: 10px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 8pt;
        font-weight: bold;
    }
    
    .status-running {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-stopped {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    .issue-item {
        padding: 8px;
        background: #fef3c7;
        border-left: 3px solid #f59e0b;
        margin-bottom: 8px;
        font-size: 9pt;
    }
    
    .issue-item strong {
        color: #dc2626;
    }
    
    .footer {
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #ccc;
        font-size: 8pt;
        color: #888;
        text-align: center;
    }
    
    .page-number {
        margin-top: 5px;
    }
    
    ul, ol {
        margin: 10px 0;
        padding-left: 25px;
    }
    
    li {
        margin-bottom: 8px;
        line-height: 1.6;
    }
    
    .citation {
        background: #f0f9ff;
        border-left: 3px solid #0284c7;
        padding: 10px;
        margin: 10px 0;
        font-size: 9pt;
    }
    
    .citation-title {
        font-weight: bold;
        color: #0284c7;
        margin-bottom: 5px;
    }
    
    .citation-content {
        color: #555;
        font-style: italic;
    }
    
    .checklist-item {
        padding: 8px;
        background: white;
        border: 1px solid #ddd;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }
    
    .checklist-checkbox {
        width: 15px;
        height: 15px;
        border: 2px solid #333;
        margin-right: 10px;
        flex-shrink: 0;
    }
    
    .checklist-critical {
        border-left: 3px solid #dc2626;
    }
    """
    
    # Generate PDF
    html = HTML(string=html_content)
    css = CSS(string=css_content)
    
    pdf_bytes = html.write_pdf(stylesheets=[css])
    
    return pdf_bytes
