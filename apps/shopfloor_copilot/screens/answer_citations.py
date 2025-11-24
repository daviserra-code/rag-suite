import os
import httpx
from nicegui import ui, app
from typing import List, Dict
import re

async def ask_with_citations(question: str, collection: str = "technical_docs") -> Dict:
    """Ask a question and get answer with citations from RAG"""
    try:
        api_base = os.getenv("API_BASE", "http://core-api:8000")
        
        print(f"Asking RAG API: {question}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_base}/ask",
                json={
                    "question": question,
                    "collection": collection,
                    "include_sources": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'No answer provided')
                sources = result.get('sources', [])
                
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
    
    async def submit_question():
        """Submit question to RAG and get answer with citations"""
        question = app.storage.user.get('citation_question', '').strip()
        
        if not question:
            ui.notify('Please enter a question', type='warning')
            return
        
        ui.notify('Searching knowledge base...', type='info')
        
        collection = app.storage.user.get('citation_collection', 'technical_docs')
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
                ui.button('Export PDF', icon='picture_as_pdf', on_click=lambda: ui.notify('PDF export coming soon', type='info')).classes('sf-btn')
    
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
                        'technical_docs': 'Technical Documents',
                        'procedures': 'Procedures',
                        'safety': 'Safety Manuals',
                        'maintenance': 'Maintenance Guides'
                    },
                    value=app.storage.user.get('citation_collection', 'technical_docs'),
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
