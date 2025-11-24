from nicegui import ui
import httpx, os

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api")

def build_ui():

    with ui.header().classes('items-center justify-between'):
        ui.label('RAG Suite').classes('text-xl')
        ui.link('API Docs', f'{API_BASE.replace("/api","")}/docs')

    with ui.row().classes('w-full p-4 gap-6'):
        with ui.card().classes('w-full'):
            ui.label('Chiedi').classes('text-lg')
            app_select = ui.select(['shopfloor','museo','cittadino'], value='shopfloor', label='App')
            query = ui.textarea(label='Domanda', placeholder='Es. Qual è la procedura per...')
            linea = ui.input(label='Filtro linea (opzionale)')
            turno = ui.input(label='Turno (opzionale)')

            table = ui.table(columns=[
                {'name':'doc_id','label':'Doc','field':'doc_id'},
                {'name':'pages','label':'Pagine','field':'pages'},
                {'name':'score','label':'Score','field':'score'},
            ], rows=[], row_key='doc_id').classes('w-full')

            async def do_ask():
                payload = {"app": app_select.value, "query": query.value, "filters": {"linea": linea.value, "turno": turno.value} }
                async with httpx.AsyncClient(timeout=120.0) as client:
                    r = await client.post(f'{API_BASE}/ask', json=payload)
                data = r.json()
                ans.value = data.get("answer","(nessuna risposta)")
                rows = []
                for c in data.get("citations",[]):
                    rows.append({"doc_id": c.get("doc_id"), "pages": c.get("pages"), "score": c.get("score")})
                table.rows = rows

            ui.button('Cerca', on_click=do_ask)
            ans = ui.markdown('')       # risposta

        with ui.card().classes('w-full'):
            ui.label('Ingest').classes('text-lg')
            app_ing = ui.select(['shopfloor','museo','cittadino'], value='shopfloor', label='App')
            doctype = ui.input(label='Doctype', value='WI')
            upload = ui.upload(label='Carica PDF', auto_upload=True)

            async def handle_upload(e):
                f = e.content
                files = {'file': (e.name, f, 'application/pdf')}
                data = {'app': app_ing.value, 'doctype': doctype.value}
                async with httpx.AsyncClient(timeout=600.0) as client:
                    r = await client.post(f'{API_BASE}/ingest', data=data, files=files)
                ui.notify(r.json())
            upload.on('upload', handle_upload)


