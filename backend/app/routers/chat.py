from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from google import genai

from app.config import get_settings
from app.services.run_service import RunService, get_run_service
from app.services.chat_service import ChatAgent

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    ui_snapshot: dict = {}

async def generate_chat_stream(request: ChatRequest, svc: RunService):
    settings = get_settings()
    
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        yield "data: " + json.dumps({"type": "error", "content": "GEMINI_API_KEY not configured"}) + "\n\n"
        yield "data: " + json.dumps({"type": "done"}) + "\n\n"
        return
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    agent = ChatAgent(svc, client)
    
    async for chunk in agent.stream_chat(request.message, request.history, request.ui_snapshot):
        yield chunk

@router.post("")
async def chat_endpoint(req: ChatRequest, svc: RunService = Depends(get_run_service)):
    return StreamingResponse(generate_chat_stream(req, svc), media_type="text/event-stream")
