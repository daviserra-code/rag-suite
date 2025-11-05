from fastapi import APIRouter
from pydantic import BaseModel
from packages.core_rag.retriever import retrieve_and_answer

router = APIRouter(tags=["ask"])

class AskReq(BaseModel):
    app: str
    query: str
    filters: dict | None = None

@router.post("/ask")
def ask(req: AskReq):
    return retrieve_and_answer(req.app, req.query, req.filters or {})
