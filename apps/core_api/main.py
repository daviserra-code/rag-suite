import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from nicegui import ui
from apps.core_api.routers import ask, ingest, export

app = FastAPI(title="RAG Core", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

app.include_router(ask.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(export.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}

# Initialize NiceGUI with FastAPI
ui.run_with(app, storage_secret="dev-secret")

# Build UI after initialization
from ui.app import build_ui
build_ui()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.core_api.main:app",
                host=os.getenv("APP_HOST", "0.0.0.0"),
                port=int(os.getenv("APP_PORT", "8000")),
                reload=True)
