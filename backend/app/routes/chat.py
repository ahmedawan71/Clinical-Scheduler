from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.agents.orchestrator import route_request
from app.agents.dispatcher import execute
from app.agents.streaming_agent import stream_response
from app.schemas.chat import ChatRequest
 
router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
def chat(request: ChatRequest):
    orchestration = route_request(request.message)

    intent = orchestration["intent"]
    parameters = orchestration["parameters"]

    result = execute(intent, parameters)

    return {
        "intent": intent,
        "parameters": parameters,
        "result": result
    }

@router.post("/stream")
def chat_stream(request: ChatRequest):
    orchestration = route_request(request.message)
    intent = orchestration["intent"]
    parameters = orchestration["parameters"]

    result = execute(intent, parameters)

    system_prompt = "You are a clinical assistant summarizing system actions."
    user_prompt = f"""
User request: {request.message}

System intent: {intent}
System parameters: {parameters}
System result: {result}

Explain this politely to the user.
"""

    return StreamingResponse(
        stream_response(system_prompt, user_prompt),
        media_type="text/plain"
    )