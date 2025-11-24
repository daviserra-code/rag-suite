from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["chat"])

class ChatReq(BaseModel):
    message: str

@router.post("/chat")
def chat_endpoint(req: ChatReq):
    return {"response": f"Echo from Cittadino: {req.message}"}
