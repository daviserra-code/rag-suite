import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from nicegui import ui
from apps.musea.routers import chat

app = FastAPI(title="Musea", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

app.include_router(chat.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "app": "musea"}

# Initialize NiceGUI with FastAPI
ui.run_with(app, storage_secret="musea-secret")

@ui.page('/')
def main_page():
    ui.label('Musea').classes('text-2xl')
    ui.label('AI Museum Guide').classes('text-lg text-gray-500')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.musea.main:app",
                host=os.getenv("APP_HOST", "0.0.0.0"),
                port=int(os.getenv("APP_PORT", "8030")),
                reload=True)
