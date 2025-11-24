from fastapi import APIRouter, UploadFile, File, Form
from packages.core_ingest.pipeline import ingest_file

router = APIRouter(tags=["ingest"])

@router.post("/ingest")
async def ingest(app: str = Form(...), doctype: str = Form(...), file: UploadFile = File(...)):
    content = await file.read()
    stats = ingest_file(app=app, doctype=doctype, filename=file.filename, content=content)
    return {"ok": True, "stats": stats}
