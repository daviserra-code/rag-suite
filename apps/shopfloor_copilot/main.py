import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from nicegui import ui
from apps.shopfloor_copilot.routers import ask, ingest, export, kpi, oee_analytics, realtime, diagnostics

app = FastAPI(title="Shopfloor Copilot", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

app.include_router(ask.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(kpi.router, prefix="/api")
app.include_router(oee_analytics.router, prefix="/api")
app.include_router(realtime.router, prefix="/api")
app.include_router(diagnostics.router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "shopfloor_copilot"}

# Initialize NiceGUI with FastAPI
app.mount("/static", StaticFiles(directory="apps/shopfloor_copilot/static"), name="static")
ui.run_with(app, storage_secret="shopfloor-secret")

# Apply global dark theme CSS immediately - before any pages load
# This prevents FOUC (Flash of Unstyled Content) during navigation
ui.add_head_html('''
<style>
    /* Global dark theme loaded at app initialization to prevent FOUC */
    body {
        background: #0f172a !important;
        color: #e2e8f0 !important;
        transition: none !important;
    }
    
    /* Dark theme for all cards */
    .nicegui-card, .q-card {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #e2e8f0 !important;
    }
    
    /* Dark theme for inputs and selects */
    .q-field__control {
        background: #1e293b !important;
        color: #e2e8f0 !important;
    }
    
    .q-field__label, .q-field__native {
        color: #94a3b8 !important;
    }
    
    .q-field__input {
        color: #e2e8f0 !important;
    }
    
    /* Dark theme for tables */
    .q-table, .q-table__card {
        background: #1e293b !important;
        color: #e2e8f0 !important;
    }
    
    .q-table thead th {
        color: #f1f5f9 !important;
        background: #0f172a !important;
    }
    
    .q-table tbody td {
        color: #e2e8f0 !important;
        border-color: #334155 !important;
    }
    
    .q-table tbody tr:hover {
        background: #334155 !important;
    }
    
    /* Dark theme for buttons (non-colored) */
    .q-btn:not(.bg-primary):not(.bg-secondary):not(.bg-positive):not(.bg-negative):not(.bg-warning):not(.bg-blue):not(.bg-green):not(.bg-teal):not(.bg-purple):not(.bg-orange) {
        background: #334155 !important;
        color: #e2e8f0 !important;
    }
    
    /* Dark theme for dialogs and menus */
    .q-menu {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    
    .q-menu .q-item {
        color: #e2e8f0 !important;
    }
    
    .q-menu .q-item:hover {
        background: #334155 !important;
    }
    
    .q-dialog__backdrop {
        background: rgba(15, 23, 42, 0.75) !important;
    }
    
    /* Dark theme for expansion panels */
    .q-expansion-item {
        background: #1e293b !important;
        color: #e2e8f0 !important;
    }
    
    /* Dark theme for drawer */
    .q-drawer {
        background: #1e293b !important;
        transition: none !important;
    }
    
    .q-drawer .q-expansion-item__container {
        background: transparent !important;
    }
    
    .q-drawer .q-item {
        color: #e2e8f0 !important;
    }
    
    .q-drawer .q-item:hover {
        background: #334155 !important;
    }
    
    /* Prevent any white flash during page transitions */
    .nicegui-content, .q-page {
        background: #0f172a !important;
        transition: none !important;
    }
</style>
''')

# Import pages to register all @ui.page routes
# This must happen before uvicorn.run()
import apps.shopfloor_copilot.pages
from apps.shopfloor_copilot.pages import legacy

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.shopfloor_copilot.main:app",
                host=os.getenv("APP_HOST", "0.0.0.0"),
                port=int(os.getenv("APP_PORT", "8010")),
                reload=True)
