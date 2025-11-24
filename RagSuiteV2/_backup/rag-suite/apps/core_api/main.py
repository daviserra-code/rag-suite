import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from nicegui import app as ng_app
from apps.core_api.routers import ask, ingest, export
from ui.app import build_ui

app = FastAPI(title="RAG Core", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

app.include_router(ask.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(export.router, prefix="/api")

@ng_app.get("/health")
def health():
    return {"status": "ok"}

build_ui()
from nicegui import ui
ui.run_with(app, mount_path='/', storage_secret='dev-secret')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.core_api.main:app",
                host=os.getenv("APP_HOST", "0.0.0.0"),
                port=int(os.getenv("APP_PORT", "8000")),
                reload=True)
