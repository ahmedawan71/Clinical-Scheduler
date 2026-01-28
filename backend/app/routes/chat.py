from fastapi import APIRouter
from app.agents.orchestrator import route_request
from app.agents.dispatcher import execute
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
