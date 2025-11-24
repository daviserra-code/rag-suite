from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from packages.core_ingest.pipeline import ingest_file

router = APIRouter(tags=["ingest"])

@router.post("/ingest")
async def ingest(
    app: str = Form(...), 
    doctype: str = Form(...), 
    file: UploadFile = File(...),
    # Optional MES context metadata
    plant: Optional[str] = Form(None),
    line: Optional[str] = Form(None),
    station: Optional[str] = Form(None),
    turno: Optional[str] = Form(None),
    rev: Optional[str] = Form(None),
    valid_from: Optional[str] = Form(None),
    valid_to: Optional[str] = Form(None),
    safety_tag: Optional[str] = Form(None),
    lang: Optional[str] = Form("en")
):
    """
    Ingest a document with MES context metadata.
    
    MES Context Fields:
    - plant: Plant identifier (e.g., "P01")
    - line: Production line (e.g., "A01")
    - station: Work station (e.g., "S110")
    - turno: Shift identifier (e.g., "T1", "T2", "T3")
    - rev: Document revision (e.g., "v1.2")
    - valid_from: Start date (ISO format)
    - valid_to: End date (ISO format)
    - safety_tag: Safety level (e.g., "critical")
    - lang: Language code (e.g., "en", "it")
    """
    content = await file.read()
    stats = ingest_file(
        app=app, 
        doctype=doctype, 
        filename=file.filename, 
        content=content,
        plant=plant,
        line=line,
        station=station,
        turno=turno,
        rev=rev,
        valid_from=valid_from,
        valid_to=valid_to,
        safety_tag=safety_tag,
        lang=lang
    )
    return {"ok": True, "stats": stats}
