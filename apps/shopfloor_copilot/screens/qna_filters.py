import os
import httpx
from nicegui import ui, app
from sqlalchemy import create_engine, text
from typing import List, Dict
from datetime import datetime

# Database connection
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "ragdb")

engine = create_engine(f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def get_checklists_for_line(line_id: str, checklist_type: str = None) -> List[Dict]:
    """Get all checklists for a specific line"""
    try:
        with engine.connect() as conn:
            query = """
                SELECT id, title, description, checklist_type, created_at
                FROM checklists
                WHERE line_id = :line_id AND is_active = TRUE
            """
            params = {"line_id": line_id}
            
            if checklist_type and checklist_type != 'All':
                query += " AND checklist_type = :checklist_type"
                params["checklist_type"] = checklist_type
            
            query += " ORDER BY checklist_type, title"
            
            result = conn.execute(text(query), params)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error fetching checklists: {e}")
        return []

def get_checklist_items(checklist_id: int) -> List[Dict]:
    """Get all items for a checklist"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, sequence_number, item_text, is_critical, reference_document
                FROM checklist_items
                WHERE checklist_id = :checklist_id
                ORDER BY sequence_number
            """), {"checklist_id": checklist_id})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error fetching checklist items: {e}")
        return []

async def generate_ai_checklist(line_id: str, context: str) -> List[str]:
    """Generate checklist using RAG/AI"""
    try:
        # Try RAG API first
        api_base = os.getenv("API_BASE", "http://core-api:8000")
        
        prompt = f"""Generate a detailed operational checklist for production line {line_id}.

Context/Task: {context}

Create a numbered checklist with 8-12 specific, actionable items covering:
- Safety verification steps
- Equipment checks and preparations
- Quality control points
- Operational procedures

Format: Return only the checklist items as a numbered list."""
        
        print(f"Calling RAG API at {api_base}/ask with prompt...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_base}/ask",
                json={
                    "app": "shopfloor_docs",
                    "query": prompt,
                    "filters": {}
                }
            )
            
            print(f"RAG API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                print(f"RAG API answer length: {len(answer)}")
                
                # Parse answer into checklist items
                items = []
                for line in answer.split('\n'):
                    line = line.strip()
                    # Remove numbering and bullets
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•') or line.startswith('*')):
                        cleaned = line.lstrip('0123456789.-•*) ').strip()
                        if cleaned and len(cleaned) > 10:  # Filter out too short items
                            items.append(cleaned)
                
                if items:
                    print(f"Parsed {len(items)} items from RAG response")
                    return items[:12]
                else:
                    print("No valid items parsed, using fallback")
            else:
                print(f"RAG API error: {response.text}")
                
    except Exception as e:
        print(f"Error calling RAG API: {e}")
    
    # Fallback: context-aware default checklist
    print(f"Using fallback checklist for line {line_id}")
    
    context_lower = context.lower()
    
    if 'changeover' in context_lower or 'setup' in context_lower:
        return [
            "Complete current production run and clear all product from line",
            "Shut down equipment following standard procedure",
            "Remove all tooling and fixtures from current product",
            "Clean all contact surfaces and product zones thoroughly",
            "Install tooling and fixtures for new product",
            "Verify tooling dimensions and alignment",
            "Load new product specifications into control system",
            "Perform trial run and adjust settings as needed",
            "Inspect first pieces for quality compliance",
            "Obtain quality approval before full production"
        ]
    elif 'maintenance' in context_lower or 'repair' in context_lower:
        return [
            "Lock out / tag out all energy sources",
            "Verify zero energy state on all circuits",
            "Obtain maintenance work order and safety permit",
            "Review equipment history and known issues",
            "Prepare tools and replacement parts",
            "Perform visual inspection before disassembly",
            "Follow manufacturer maintenance procedures",
            "Replace worn or damaged components",
            "Test all safety systems after reassembly",
            "Document work performed and update maintenance log"
        ]
    elif 'startup' in context_lower or 'start' in context_lower:
        return [
            "Verify emergency stop is released and functional",
            "Check all safety guards are properly installed",
            "Activate main disconnect switch",
            "Verify compressed air supply pressure (6-8 bar)",
            "Check hydraulic and lubrication fluid levels",
            "Test all sensors and limit switches",
            "Clear production area of tools and materials",
            "Press green start button and monitor startup",
            "Listen for abnormal sounds or vibrations",
            "Verify product quality on first piece"
        ]
    else:
        # Generic operational checklist
        return [
            f"Verify all safety systems on line {line_id} are operational",
            "Check emergency stop button functionality",
            "Inspect equipment for visible damage or wear",
            "Verify material supply is adequate for production",
            "Test all sensors and indicators",
            "Review quality specifications for current product",
            "Check maintenance schedule compliance",
            "Verify operator training and certification",
            "Confirm production schedule and targets",
            "Document any anomalies or concerns"
        ]

def save_ai_checklist(line_id: str, section: str, title: str, items: List[str]) -> int:
    """Save AI-generated checklist to database"""
    try:
        with engine.connect() as conn:
            # Insert checklist
            result = conn.execute(text("""
                INSERT INTO checklists (line_id, section, checklist_type, title, description, created_by)
                VALUES (:line_id, :section, 'AI Generated', :title, 'AI-generated checklist', 'AI Assistant')
                RETURNING id
            """), {"line_id": line_id, "section": section, "title": title})
            
            checklist_id = result.fetchone()[0]
            
            # Insert items
            for idx, item_text in enumerate(items, 1):
                conn.execute(text("""
                    INSERT INTO checklist_items (checklist_id, sequence_number, item_text, is_critical)
                    VALUES (:checklist_id, :seq, :text, FALSE)
                """), {"checklist_id": checklist_id, "seq": idx, "text": item_text})
            
            conn.commit()
            return checklist_id
    except Exception as e:
        print(f"Error saving AI checklist: {e}")
        return None

def build_qna_filters():
    """Q&A with Filters screen - AI-powered checklist generation"""
    
    # State
    if 'checklist_line' not in app.storage.user:
        app.storage.user['checklist_line'] = 'M10'
    if 'checklist_type' not in app.storage.user:
        app.storage.user['checklist_type'] = 'All'
    if 'selected_checklist' not in app.storage.user:
        app.storage.user['selected_checklist'] = None
    if 'ai_context' not in app.storage.user:
        app.storage.user['ai_context'] = ''
    if 'checklist_items_state' not in app.storage.user:
        app.storage.user['checklist_items_state'] = {}
    
    @ui.refreshable
    def type_selector():
        """Checklist type filter dropdown"""
        ui.select(
            ['All', 'Startup', 'Shutdown', 'Maintenance', 'Safety', 'AI Generated'],
            value=app.storage.user['checklist_type'],
            label='Checklist Type',
            on_change=lambda e: update_type(e.value)
        ).classes('w-full')
    
    @ui.refreshable
    def checklist_selector():
        """Dropdown to select existing checklists"""
        line = app.storage.user['checklist_line']
        type_filter = app.storage.user['checklist_type']
        
        checklists = get_checklists_for_line(line, type_filter)
        
        if checklists:
            options = {str(c['id']): f"{c['checklist_type']} - {c['title']}" for c in checklists}
            
            # Get current value and ensure it's in options
            current_value = str(app.storage.user.get('selected_checklist', ''))
            if current_value and current_value not in options:
                # If current value not in filtered options, clear it
                app.storage.user['selected_checklist'] = None
                current_value = None
            
            ui.select(
                options,
                value=current_value,
                label='Select Checklist',
                on_change=lambda e: load_selected_checklist(int(e.value) if e.value else None)
            ).classes('w-full')
        else:
            ui.label('No checklists found for this line').classes('text-sm text-gray-500')
    
    @ui.refreshable
    def checklist_display():
        """Display checklist items with checkboxes"""
        checklist_id = app.storage.user.get('selected_checklist')
        
        if not checklist_id:
            ui.label('Select a checklist or generate a new one').classes('text-sm text-gray-500 italic')
            return
        
        items = get_checklist_items(checklist_id)
        
        if not items:
            ui.label('No items in this checklist').classes('text-sm text-gray-500')
            return
        
        for item in items:
            item_id = item['id']
            is_checked = app.storage.user['checklist_items_state'].get(item_id, False)
            
            with ui.row().classes('items-start gap-3 mb-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800'):
                checkbox = ui.checkbox(
                    value=is_checked,
                    on_change=lambda e, iid=item_id: toggle_item(iid, e.value)
                ).classes('mt-1')
                
                with ui.column().classes('flex-grow gap-1'):
                    label_classes = 'text-sm font-medium' if item['is_critical'] else 'text-sm'
                    if item['is_critical']:
                        label_classes += ' text-red-600 dark:text-red-400'
                    
                    with ui.row().classes('items-center gap-2'):
                        ui.label(f"{item['sequence_number']}.").classes('text-xs w-6 text-center bg-blue-100 dark:bg-blue-900 rounded font-bold')
                        ui.label(item['item_text']).classes(label_classes)
                        if item['is_critical']:
                            ui.icon('warning', size='sm').classes('text-red-500').tooltip('Critical item')
                    
                    if item['reference_document']:
                        ui.label(f"Ref: {item['reference_document']}").classes('text-xs text-gray-500')
        
        # Summary
        total = len(items)
        completed = sum(1 for item in items if app.storage.user['checklist_items_state'].get(item['id'], False))
        progress = (completed / total * 100) if total > 0 else 0
        
        with ui.row().classes('w-full items-center gap-4 mt-4 p-3 bg-blue-50 dark:bg-blue-900 rounded'):
            ui.label(f'Progress: {completed}/{total} items ({progress:.0f}%)').classes('font-bold')
            ui.linear_progress(progress / 100).classes('flex-grow')
    
    def toggle_item(item_id: int, checked: bool):
        """Toggle checklist item completion"""
        app.storage.user['checklist_items_state'][item_id] = checked
        checklist_display.refresh()
    
    def load_selected_checklist(checklist_id: int):
        """Load a selected checklist"""
        app.storage.user['selected_checklist'] = checklist_id
        app.storage.user['checklist_items_state'] = {}
        checklist_display.refresh()
    
    async def generate_new_checklist():
        """Generate new checklist using AI"""
        line = app.storage.user['checklist_line']
        context = app.storage.user.get('ai_context', '')
        
        if not context:
            ui.notify('Please provide context for AI generation', type='warning')
            return
        
        ui.notify('Generating checklist with AI...', type='info')
        
        # Generate items
        items = await generate_ai_checklist(line, context)
        
        # Save to database
        title = f"{line} - AI Generated - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        checklist_id = save_ai_checklist(line, line, title, items)
        
        if checklist_id:
            ui.notify(f'Checklist generated with {len(items)} items!', type='positive')
            # Switch filter to show AI generated checklists
            app.storage.user['checklist_type'] = 'AI Generated'
            app.storage.user['selected_checklist'] = checklist_id
            app.storage.user['checklist_items_state'] = {}
            # Refresh all components
            type_selector.refresh()
            checklist_selector.refresh()
            checklist_display.refresh()
        else:
            ui.notify('Failed to save checklist', type='negative')
    
    def update_line(new_line: str):
        """Update selected line"""
        app.storage.user['checklist_line'] = new_line
        app.storage.user['selected_checklist'] = None
        app.storage.user['checklist_items_state'] = {}
        checklist_selector.refresh()
        checklist_display.refresh()
    
    def update_type(new_type: str):
        """Update checklist type filter"""
        app.storage.user['checklist_type'] = new_type
        app.storage.user['selected_checklist'] = None
        app.storage.user['checklist_items_state'] = {}
        checklist_selector.refresh()
        checklist_display.refresh()
    
    def reset_checklist():
        """Reset all checkboxes"""
        app.storage.user['checklist_items_state'] = {}
        checklist_display.refresh()
    
    def export_pdf():
        """Export checklist to PDF"""
        checklist_id = app.storage.user.get('selected_checklist_id')
        
        if not checklist_id:
            ui.notify('Please select a checklist first', type='warning')
            return
        
        # Get checklist details
        try:
            with engine.connect() as conn:
                # Get checklist info
                checklist_result = conn.execute(text("""
                    SELECT id, line_id, name, checklist_type, description, created_at
                    FROM checklists
                    WHERE id = :checklist_id
                """), {"checklist_id": checklist_id})
                
                checklist = checklist_result.fetchone()
                if not checklist:
                    ui.notify('Checklist not found', type='negative')
                    return
                
                # Get checklist items
                items_result = conn.execute(text("""
                    SELECT sequence, item_text, is_critical
                    FROM checklist_items
                    WHERE checklist_id = :checklist_id
                    ORDER BY sequence
                """), {"checklist_id": checklist_id})
                
                items = [dict(row._mapping) for row in items_result]
        except Exception as e:
            ui.notify(f'Error loading checklist: {str(e)}', type='negative')
            return
        
        # Build PDF content
        content_html = f'''
        <h2>Checklist Information</h2>
        <table style="margin-bottom: 20px;">
            <tr><th>Line ID</th><td>{checklist[1]}</td></tr>
            <tr><th>Checklist Name</th><td>{checklist[2]}</td></tr>
            <tr><th>Type</th><td>{checklist[3]}</td></tr>
            <tr><th>Description</th><td>{checklist[4] or 'N/A'}</td></tr>
            <tr><th>Created</th><td>{checklist[5]}</td></tr>
        </table>
        
        <h2>Checklist Items</h2>
        <div style="margin-top: 15px;">
        '''
        
        for item in items:
            critical_class = ' checklist-critical' if item['is_critical'] else ''
            critical_badge = ' <span style="color: #dc2626; font-weight: bold;">[CRITICAL]</span>' if item['is_critical'] else ''
            
            content_html += f'''
            <div class="checklist-item{critical_class}">
                <div class="checklist-checkbox"></div>
                <div style="flex-grow: 1;">
                    <strong>{item['sequence']}.</strong> {item['item_text']}{critical_badge}
                </div>
            </div>
            '''
        
        content_html += '</div>'
        
        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checklist_{checklist[1]}_{checklist[3]}_{timestamp}.pdf"
        
        pdf_bytes = export_to_pdf(
            title=f'{checklist[2]} Checklist',
            subtitle=f'Line {checklist[1]} - {checklist[3]}',
            content_html=content_html,
            filename=filename
        )
        
        ui.download(pdf_bytes, filename)
        ui.notify('Checklist exported to PDF successfully', type='positive')
    
    # Main layout
    with ui.row().classes('w-full gap-4'):
        # Left - Filters & Controls
        with ui.column().classes('w-80 gap-4'):
            # Filters Card
            with ui.card().classes('sf-card'):
                ui.label('🔍 Filters').classes('text-lg font-bold mb-3')
                
                ui.select(
                    ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01'],
                    value=app.storage.user['checklist_line'],
                    label='Production Line',
                    on_change=lambda e: update_line(e.value)
                ).classes('w-full')
                
                type_selector()
                
                checklist_selector()
            
            # AI Generation Card
            with ui.card().classes('sf-card'):
                ui.label('🤖 AI Generation').classes('text-lg font-bold mb-3')
                
                ui.textarea(
                    label='Context / Instructions',
                    placeholder='e.g., "Changeover from Product A to Product B" or "Morning shift startup procedure"',
                    on_change=lambda e: app.storage.user.update({'ai_context': e.value})
                ).classes('w-full').style('min-height: 100px')
                
                ui.button(
                    'Generate with AI',
                    icon='auto_awesome',
                    on_click=generate_new_checklist
                ).classes('sf-btn w-full')
            
            # Actions Card
            with ui.card().classes('sf-card'):
                ui.label('⚙️ Actions').classes('text-lg font-bold mb-3')
                
                ui.button(
                    'Reset All',
                    icon='refresh',
                    on_click=reset_checklist
                ).classes('sf-btn secondary w-full')
                
                ui.button(
                    'Export PDF',
                    icon='picture_as_pdf',
                    on_click=export_pdf
                ).classes('sf-btn w-full')
        
        # Right - Checklist Display
        with ui.column().classes('flex-grow gap-4'):
            with ui.card().classes('sf-card'):
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    ui.label('✓ Checklist Items').classes('text-lg font-bold')
                    
                    if app.storage.user.get('selected_checklist'):
                        checklists = get_checklists_for_line(app.storage.user['checklist_line'])
                        selected = next((c for c in checklists if c['id'] == app.storage.user['selected_checklist']), None)
                        if selected:
                            ui.label(f"{selected['checklist_type']}").classes('text-sm px-3 py-1 bg-blue-100 dark:bg-blue-900 rounded-full')
                
                checklist_display()
