import os
import httpx
from nicegui import ui, app
from typing import List, Dict
import re
from datetime import datetime

# Import export utilities
import sys
sys.path.insert(0, '/app')
from packages.export_utils.pdf_export import export_to_pdf, generate_pdf_section

async def ask_with_citations(question: str, collection: str = "shopfloor_docs") -> Dict:
    """Ask a question and get answer with citations from RAG"""
    try:
        api_base = os.getenv("API_BASE", "http://core-api:8000")
        
        print(f"Asking RAG API: {question}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_base}/ask",
                json={
                    "app": collection,
                    "query": question,
                    "filters": {}
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"DEBUG: Full API response: {result}")
                
                answer = result.get('answer', 'No answer provided')
                citations = result.get('citations', [])
                
                print(f"DEBUG: Found {len(citations)} citations")
                print(f"DEBUG: Citations: {citations}")
                
                # Convert citations to sources format for compatibility
                sources = []
                for citation in citations:
                    sources.append({
                        'metadata': {
                            'source': citation.get('doc_id', 'Unknown'),
                            'page': citation.get('pages', 'N/A'),
                            'type': 'document',
                            'url': citation.get('url', '')
                        },
                        'content': '',  # Not provided by this API
                        'score': citation.get('score', 0)
                    })
                
                print(f"Got answer with {len(sources)} sources")
                
                # Parse answer into steps if it's a procedure
                steps = parse_answer_into_steps(answer)
                
                return {
                    'answer': answer,
                    'steps': steps,
                    'sources': sources,
                    'success': True
                }
            else:
                print(f"RAG API error: {response.status_code}")
                return {
                    'answer': 'Error retrieving answer',
                    'steps': [],
                    'sources': [],
                    'success': False
                }
                
    except Exception as e:
        print(f"Error asking RAG: {e}")
        return {
            'answer': f'Service unavailable: {str(e)}',
            'steps': [],
            'sources': [],
            'success': False
        }

def parse_answer_into_steps(answer: str) -> List[str]:
    """Parse answer text into numbered steps"""
    steps = []
    
    # Split by lines
    lines = answer.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with number, bullet, or step indicator
        if re.match(r'^(\d+[\.\):]|\*|-|•|Step \d+)', line):
            # Remove the numbering/bullet
            cleaned = re.sub(r'^(\d+[\.\):]|\*|-|•|Step \d+[:.]?)\s*', '', line)
            if cleaned:
                steps.append(cleaned)
        elif line and not steps:
            # First non-empty line without numbering might be a step
            steps.append(line)
    
    # If no steps found, return the whole answer as one step
    if not steps:
        steps = [answer]
    
    return steps

def build_answer_citations():
    """Answer with Citations screen - AI Q&A with source references"""
    
    # State
    if 'citation_question' not in app.storage.user:
        app.storage.user['citation_question'] = ''
    if 'citation_result' not in app.storage.user:
        app.storage.user['citation_result'] = None
    if 'citation_collection' not in app.storage.user:
        app.storage.user['citation_collection'] = 'technical_docs'
    
    def export_answer_pdf():
        """Export Q&A answer with citations to PDF"""
        result = app.storage.user.get('citation_result')
        question = app.storage.user.get('citation_question')
        
        if not result or not result.get('success'):
            ui.notify('No answer to export', type='warning')
            return
        
        answer = result.get('answer', '')
        steps = result.get('steps', [])
        sources = result.get('sources', [])
        
        # Build content
        content_html = f'<h2>Question</h2><p style="font-size: 11pt; font-style: italic; color: #0F7C7C; padding: 10px; background: #f0f9ff; border-left: 3px solid #0F7C7C;">{question}</p>'
        
        content_html += f'<h2>Answer</h2><div style="padding: 10px; line-height: 1.8;">{answer.replace(chr(10), "<br>")}</div>'
        
        # Parse steps if available
        if steps and len(steps) > 1:
            content_html += '<h2>Step-by-Step Guide</h2><ol style="padding-left: 25px;">'
            for step in steps:
                content_html += f'<li style="margin-bottom: 12px; line-height: 1.6;">{step}</li>'
            content_html += '</ol>'
        
        # Add citations
        if sources:
            content_html += '<h2>Source Citations</h2>'
            for idx, source in enumerate(sources, 1):
                metadata = source.get('metadata', {})
                content = source.get('content', '')[:300]
                score = source.get('score', 0)
                
                content_html += f'''
                <div class="citation">
                    <div class="citation-title">[{idx}] {metadata.get('source', 'Unknown Source')}</div>
                    <div style="font-size: 8pt; color: #888; margin: 5px 0;">
                        Relevance Score: {score:.3f} | 
                        Type: {metadata.get('type', 'N/A')} | 
                        Page: {metadata.get('page', 'N/A')}
                    </div>
                    <div class="citation-content">"{content}..."</div>
                </div>
                '''
        
        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qa_answer_{timestamp}.pdf"
        
        pdf_bytes = export_to_pdf(
            title='Q&A Answer with Citations',
            subtitle='Shopfloor Copilot Knowledge Base',
            content_html=content_html,
            filename=filename
        )
        
        ui.download(pdf_bytes, filename)
        ui.notify('Answer exported to PDF successfully', type='positive')
    
    async def submit_question():
        """Submit question to RAG and get answer with citations"""
        question = app.storage.user.get('citation_question', '').strip()
        
        if not question:
            ui.notify('Please enter a question', type='warning')
            return
        
        ui.notify('Searching knowledge base...', type='info')
        
        collection = app.storage.user.get('citation_collection', 'shopfloor_docs')
        result = await ask_with_citations(question, collection)
        
        app.storage.user['citation_result'] = result
        
        if result['success']:
            ui.notify(f"Answer found with {len(result['sources'])} sources", type='positive')
        else:
            ui.notify('Failed to get answer', type='negative')
        
        answer_display.refresh()
        citations_display.refresh()
    
    def update_question(e):
        """Update question in storage"""
        app.storage.user['citation_question'] = e.value
    
    def clear_results():
        """Clear current results"""
        app.storage.user['citation_result'] = None
        app.storage.user['citation_question'] = ''
        answer_display.refresh()
        citations_display.refresh()
    
    @ui.refreshable
    def answer_display():
        """Display the answer and steps"""
        result = app.storage.user.get('citation_result')
        
        if not result:
            with ui.column().classes('w-full items-center justify-center p-8'):
                ui.icon('question_answer', size='xl').classes('text-gray-300 mb-4')
                ui.label('Ask a question to get started').classes('text-lg text-gray-500')
                ui.label('Example: "How do I perform a line changeover?" or "What are the safety procedures for Line M10?"').classes('text-sm text-gray-400 text-center')
            return
        
        answer = result.get('answer', '')
        steps = result.get('steps', [])
        
        with ui.column().classes('w-full gap-4'):
            # Full Answer Card
            with ui.card().classes('sf-card'):
                ui.label('📝 Answer').classes('text-lg font-bold mb-3')
                ui.label(answer).classes('text-sm whitespace-pre-wrap')
            
            # Steps Card (if steps were parsed)
            if len(steps) > 1:
                with ui.card().classes('sf-card'):
                    ui.label('📋 Step-by-Step Guide').classes('text-lg font-bold mb-3')
                    
                    for idx, step in enumerate(steps, 1):
                        with ui.row().classes('items-start gap-3 mb-3'):
                            ui.label(str(idx)).classes(
                                'w-8 h-8 flex items-center justify-center '
                                'bg-teal-600 text-white rounded-full text-sm font-bold shrink-0'
                            )
                            ui.label(step).classes('text-sm flex-grow')
            
            # Actions
            with ui.row().classes('gap-2 mt-2'):
                ui.button('New Question', icon='refresh', on_click=clear_results).classes('sf-btn secondary')
                ui.button('Export PDF', icon='picture_as_pdf', on_click=export_answer_pdf).classes('sf-btn')
    
    @ui.refreshable
    def citations_display():
        """Display source citations"""
        result = app.storage.user.get('citation_result')
        
        if not result or not result.get('sources'):
            with ui.column().classes('w-full items-center justify-center p-8'):
                ui.icon('library_books', size='lg').classes('text-gray-300 mb-2')
                ui.label('No sources yet').classes('text-sm text-gray-500')
            return
        
        sources = result['sources']
        
        ui.label(f'📚 {len(sources)} Source Document{"s" if len(sources) != 1 else ""}').classes('text-lg font-bold mb-3')
        
        for idx, source in enumerate(sources, 1):
            with ui.card().classes('sf-card bg-gray-50 dark:bg-gray-800 p-3 mb-3'):
                # Source header
                with ui.row().classes('w-full items-start justify-between mb-2'):
                    ui.label(f'Source {idx}').classes('text-xs font-bold text-teal-600')
                    if source.get('score'):
                        score = source['score']
                        ui.label(f'{score:.0%} match').classes('text-xs text-gray-500')
                
                # Document info
                if source.get('metadata'):
                    metadata = source['metadata']
                    doc_name = metadata.get('source', metadata.get('filename', 'Unknown Document'))
                    ui.label(doc_name).classes('text-sm font-bold mb-2')
                    
                    # Page info if available
                    if metadata.get('page'):
                        ui.label(f"Page {metadata['page']}").classes('text-xs text-gray-500 mb-2')
                
                # Content preview
                content = source.get('content', source.get('text', ''))
                if content:
                    preview = content[:300] + '...' if len(content) > 300 else content
                    with ui.card().classes('bg-white dark:bg-gray-900 p-2'):
                        ui.label(preview).classes('text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap')
                
                # Open document button (if available)
                if source.get('metadata', {}).get('source'):
                    ui.button(
                        'View Document',
                        icon='open_in_new',
                        on_click=lambda s=source: ui.notify(f"Opening: {s.get('metadata', {}).get('source')}", type='info')
                    ).classes('text-xs mt-2')
    
    # Main layout
    with ui.column().classes('w-full gap-4'):
        # Question Input Card
        with ui.card().classes('sf-card'):
            ui.label('🤖 Ask a Question').classes('text-lg font-bold mb-3')
            
            with ui.row().classes('w-full gap-2'):
                ui.select(
                    {
                        'shopfloor_docs': 'Shopfloor Documents',
                        'technical_docs': 'Technical Documents',
                        'procedures': 'Procedures',
                        'safety': 'Safety Manuals',
                        'maintenance': 'Maintenance Guides'
                    },
                    value=app.storage.user.get('citation_collection', 'shopfloor_docs'),
                    label='Collection',
                    on_change=lambda e: app.storage.user.update({'citation_collection': e.value})
                ).classes('w-48')
            
            ui.textarea(
                label='Your Question',
                placeholder='e.g., How do I perform a changeover on Line M10? What are the startup procedures?',
                value=app.storage.user.get('citation_question', ''),
                on_change=update_question
            ).classes('w-full').style('min-height: 80px')
            
            ui.button(
                'Get Answer',
                icon='search',
                on_click=submit_question
            ).classes('sf-btn')
        
        # Results Layout
        with ui.row().classes('w-full gap-4'):
            # Left - Answer
            with ui.column().classes('flex-[3] gap-4'):
                with ui.card().classes('sf-card'):
                    answer_display()
            
            # Right - Citations
            with ui.column().classes('flex-[2] gap-4'):
                with ui.card().classes('sf-card'):
                    citations_display()
