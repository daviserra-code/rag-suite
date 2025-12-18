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

# Build UI with page decorator
from apps.shopfloor_copilot.ui import build_ui

@ui.page('/')
def index_page():
    build_ui()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.shopfloor_copilot.main:app",
                host=os.getenv("APP_HOST", "0.0.0.0"),
                port=int(os.getenv("APP_PORT", "8010")),
                reload=True)
