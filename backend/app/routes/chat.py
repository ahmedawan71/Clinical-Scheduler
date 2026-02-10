from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.agents.orchestrator import route_request, update_context_after_execution, clear_context
from app.agents.dispatcher import execute
from app.agents.streaming_agent import stream_response
from app.schemas.chat import ChatRequest
import uuid
 
router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest, req: Request):
    
    session_id = req.headers.get("X-Session-ID") or str(uuid.uuid4())
    
    intent_data = route_request(request.message, session_id)
    
    if intent_data.get("needs_clarification"):
        return {
            "response": intent_data.get("clarification_question"),
            "needs_input": True,
            "session_id": session_id
        }

    intent = intent_data.get("intent")
    parameters = intent_data.get("parameters", {})

    result = execute(intent, parameters)

    return {
        "intent": intent,
        "parameters": parameters,
        "response": result,
        "session_id": session_id
    }

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    session_id = req.headers.get("X-Session-ID", str(uuid.uuid4()))
    intent_data = route_request(request.message, session_id)
    
    return StreamingResponse(
        stream_response(request.message, intent_data, session_id),
        media_type="text/event-stream",
        headers={"X-Session-ID": session_id}
    )
    
@router.post("/chat/clear")
async def clear_chat(req: Request):
    """Clear conversation context"""
    session_id = req.headers.get("X-Session-ID")
    if session_id:
        clear_context(session_id)
    return {"status": "Context cleared"}